import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pydoover.models import File
from pydoover.models.data.exceptions import DooverAPIError
from pydoover.reports import Application

from .app_config import FuelAdditiveReportConfig
from .build_pdf import build_pdf

log = logging.getLogger(__name__)

REPORT_TIMEZONE = "Asia/Riyadh"


def report_filename(skid_name: str, day: datetime) -> str:
    """The report's file name, e.g. ``SJBP_09-09-26.pdf``.

    ``day`` is the day being reported on, not the day the report ran - these
    run after midnight, so the two differ. The heading inside the PDF does not
    repeat it; the report already has a Date field.

    Built from the parts because neither separator survives the trip:

    - "/" is a path separator, so it can be neither a file name nor an S3
      attachment key.
    - Spaces are percent-encoded by ``aiohttp.FormData``, which defaults to
      ``quote_fields=True`` and so writes ``filename="a%20b.pdf"`` into the
      multipart header. doover-data stores ``field.file_name()`` verbatim, so
      the "%20" reaches the recipient in the name of the emailed attachment.
      Skid names have spaces of their own ("Saad BP"), so this is not just
      about the separator.
    """
    return f"{skid_name.replace(' ', '_')}_{day:%d-%m-%y}.pdf"


def find_reconciliation(obj, target_key="Reconciliation"):
    """
    Recursively search for the sub-object with the given key
    inside a nested dictionary structure.
    """
    if not isinstance(obj, dict):
        return None

    for key, value in obj.items():
        if key == target_key:
            return value  # found it!
        if isinstance(value, dict):
            result = find_reconciliation(value, target_key)
            if result is not None:
                return result
    return None


class FuelAdditiveReportGenerator(Application):
    config: FuelAdditiveReportConfig
    config_cls = FuelAdditiveReportConfig

    async def generate(
        self,
        agent_ids: list[int],
        period_start: datetime,
        period_end: datetime,
    ) -> list[File]:
        files = []
        for agent_id in agent_ids:
            log.info(f"Generating report for agent {agent_id}...")
            context = await self.get_context(int(agent_id), period_end)
            if context is None:
                log.error(f"No reconciliation data found for agent {agent_id}.")
                continue

            pdf_bytes = build_pdf(context)
            filename = report_filename(context["skid_name"], context["report_day"])
            files.append(File(filename, "application/pdf", len(pdf_bytes), pdf_bytes))

        if not files:
            raise RuntimeError("No reconciliation data found for any device.")
        return files

    def device_display_name(self, agent_id: int) -> str | None:
        """The device's own name, e.g. "SJBP", for skids with no skid_name set.

        DEVICE_MAP comes from the report's deployment config rather than the
        snapshot, so it is current rather than whatever the device was called
        on the day being reported.
        """
        device = (self.received_deployment_config.get("DEVICE_MAP") or {}).get(
            str(agent_id)
        ) or {}
        return device.get("display_name") or device.get("name")

    async def get_context(self, agent_id: int, period_end: datetime):
        """
        This function gets context for the report.

        For context (lol):
            The PLC clears the daily data at midnight local time, so the day's
            final totals live in the last snapshot before that reset. We take
            the whole local day as the window and walk back from its end --
            anchoring on the reset rather than on the run time, because these
            skids resume injecting within minutes of midnight and a lookback
            measured from the run would land on the *new* day's data.
        """
        day_end = period_end.astimezone(ZoneInfo(REPORT_TIMEZONE)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        day_start = day_end - timedelta(days=1)

        # The injector roster lives on the channel aggregate, not reliably in
        # each message. ui_state messages are partial - most carry the
        # Reconciliation block with an empty `injectors` list, because the
        # roster only changes when the app restarts. Requiring it per message
        # is why NRBP, QSBP and SRBP produced no report on 09/09 despite
        # publishing 144, 134 and 128 messages that day.
        fallback_injectors = []
        try:
            aggregate = await self.api.fetch_channel_aggregate(
                "ui_state", agent_id=agent_id
            )
        except DooverAPIError as e:
            # Non-fatal: a message that carries its own roster still reports.
            log.warning(f"Could not fetch ui_state aggregate for {agent_id}: {e}")
        else:
            agg_state = (aggregate.data or {}).get("state")
            agg_recon = find_reconciliation(agg_state) or {}
            fallback_injectors = agg_recon.get("injectors") or []
            log.info(
                f"Aggregate for agent {agent_id} lists "
                f"{len(fallback_injectors)} injector(s)."
            )

        messages = await self.api.iter_messages(
            "ui_state",
            before=day_end,
            after=day_start,
            agent_id=agent_id,
        ).collect()
        messages.sort(key=lambda m: m.id)
        log.info(
            f"Retrieved {len(messages)} ui_state messages for agent {agent_id} "
            f"between {day_start} and {day_end}."
        )

        context = {
            "injectors": [],
            "report_date": day_start.strftime("%d-%m-%Y"),
            # Overwritten below with the timestamp of the snapshot actually
            # used -- the report is "as at" the day's final reading.
            "report_time": day_end.strftime("%I:%M%p").lower(),
        }

        # Rebuild the day's final state by merging the messages in order
        # rather than reading one of them. A ui_state message carries only
        # what changed in that update, so any single snapshot has holes: the
        # first cut of this reported NRBP with a populated Inj 2 and an
        # all-zero Inj 1, because the message it landed on simply had not
        # touched Inj 1's keys. Merging chronologically leaves each key at its
        # last value of the day, which is what a day total is. For a device
        # that does publish full snapshots this is a no-op - the last message
        # overwrites every key anyway.
        merged: dict = {}
        injector_meta = []
        snapshot_skid_name = None
        last_update = None
        for message in messages:
            state = message.data.get("state") if isinstance(message.data, dict) else None
            reconciliation_state = find_reconciliation(state)
            if reconciliation_state is None:
                continue

            if reconciliation_state.get("injectors"):
                injector_meta = reconciliation_state["injectors"]
            if reconciliation_state.get("skid_name"):
                snapshot_skid_name = reconciliation_state["skid_name"]

            children = reconciliation_state.get("children") or {}
            for key, value in children.items():
                if isinstance(value, dict) and value.get("currentValue") is not None:
                    merged[key] = value
                    last_update = message.timestamp

        injector_meta = injector_meta or fallback_injectors
        if not injector_meta or not merged:
            log.error(
                f"No reconciliation data found for agent {agent_id} "
                f"({len(injector_meta)} injector(s), {len(merged)} value(s) merged)."
            )
            return None

        def value_of(key):
            return (merged.get(key) or {}).get("currentValue", 0)

        injectors = []
        zero_flow_injectors = 0
        for injector in injector_meta:
            injector_name = injector["name"]

            flowmeter_total = value_of(f"{injector_name}_header_LDayTotal")
            if flowmeter_total is None or flowmeter_total < 100:
                zero_flow_injectors += 1

            injectors.append(
                {
                    "index": injector["index"],
                    "injector_name": injector["displayName"],
                    "flowmeter_total": flowmeter_total,
                    "actual_injection_detergent": value_of(f"{injector_name}_LDayTotal"),
                    "calculated_detergent": value_of(f"{injector_name}CalcedLTotal"),
                    "difference": value_of(f"{injector_name}Difference"),
                }
            )

        if zero_flow_injectors == len(injector_meta):
            log.error(f"Every injector read zero flow for agent {agent_id}.")
            return None

        context["injectors"] = injectors
        # DEVICE_MAP wins over the snapshot's own skid_name. Four of the five
        # CRDD skids publish skid_name as the *application's* display name, so
        # trusting the snapshot both mislabels them and gives four skids one
        # identical file name - and attachment keys are (channel, message,
        # filename), so same-named files overwrite each other.
        context["skid_name"] = (
            self.device_display_name(agent_id)
            or snapshot_skid_name
            or f"skid-{agent_id}"
        )
        # The file name carries the day, so a report that has been emailed on
        # says which skid and which day without being opened.
        context["report_day"] = day_start
        # "as at" the last reading that fed the report, not the run time.
        if last_update is not None:
            context["report_time"] = (
                last_update.astimezone(ZoneInfo(REPORT_TIMEZONE))
                .strftime("%I:%M%p")
                .lower()
            )

        context["total_gasoline"] = value_of("GasTotal")
        context["total_calculated_detergent"] = value_of("CalcedInjectedTotal")
        context["total_actual_detergent_injected"] = value_of("ActualInjectedTotal")
        context["difference"] = value_of("Difference")
        return context
