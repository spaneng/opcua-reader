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


def report_label(skid_name: str, day: datetime) -> str:
    """The heading a report carries, e.g. ``SJBP - 12/09/26``.

    ``day`` is the day being reported on, not the day the report ran - these
    run after midnight, so the two differ.
    """
    return f"{skid_name} - {day:%d/%m/%y}"


def report_filename(skid_name: str, day: datetime) -> str:
    """The label as a file name, e.g. ``SJBP_09-09-26.pdf``.

    Built from the parts rather than from ``report_label`` because neither
    separator in the label survives the trip:

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

        # Iterate back through the data to find the last injection of the day.
        for attempt, message in enumerate(reversed(messages), start=1):
            state = message.data.get("state") if isinstance(message.data, dict) else None
            reconciliation_state = find_reconciliation(state)
            log.debug(f"Attempt: {attempt}, Timestamp: {message.timestamp}")

            if reconciliation_state is None:
                log.debug("No reconciliation state found, trying again...")
                continue

            children = reconciliation_state.get("children", {})
            injector_meta = reconciliation_state.get("injectors") or fallback_injectors
            if not injector_meta:
                log.debug("No injector metadata found, trying again...")
                continue

            injectors = []
            zero_flow_injectors = 0
            for injector in injector_meta:
                injector_name = injector["name"]

                flowmeter_total = children.get(
                    f"{injector_name}_header_LDayTotal", {}
                ).get("currentValue", 0)
                if flowmeter_total is None or flowmeter_total < 100:
                    zero_flow_injectors += 1

                injectors.append(
                    {
                        "index": injector["index"],
                        "injector_name": injector["displayName"],
                        "flowmeter_total": flowmeter_total,
                        "actual_injection_detergent": children.get(
                            f"{injector_name}_LDayTotal", {}
                        ).get("currentValue", 0),
                        "calculated_detergent": children.get(
                            f"{injector_name}CalcedLTotal", {}
                        ).get("currentValue", 0),
                        "difference": children.get(
                            f"{injector_name}Difference", {}
                        ).get("currentValue", 0),
                    }
                )

            if zero_flow_injectors == len(injector_meta):
                log.debug("All injectors have zero flow, trying again...")
                continue

            log.debug(f"Successful attempt: {attempt}")
            context["injectors"] = injectors
            # DEVICE_MAP wins over the snapshot's own skid_name. Four of the
            # five CRDD skids publish skid_name as the *application's* display
            # name ("Fuel Additive OPCUA Reader"), so trusting the snapshot
            # both mislabels them and gives four skids one identical file name
            # - and attachment keys are (channel, message, filename), so
            # same-named files overwrite each other and only one survives.
            context["skid_name"] = (
                self.device_display_name(agent_id)
                or reconciliation_state.get("skid_name")
                or f"skid-{agent_id}"
            )
            # Carried by both the heading and the file name, so a report that
            # has been emailed on says which skid and which day without being
            # opened. Whatever the skid is called, the label follows.
            context["report_label"] = report_label(context["skid_name"], day_start)
            context["report_day"] = day_start
            # "as at" the reading this report was built from, not the run time.
            context["report_time"] = (
                message.timestamp.astimezone(ZoneInfo(REPORT_TIMEZONE))
                .strftime("%I:%M%p")
                .lower()
            )

            # totals
            context["total_gasoline"] = children.get("GasTotal", {}).get(
                "currentValue", 0
            )
            context["total_calculated_detergent"] = children.get(
                "CalcedInjectedTotal", {}
            ).get("currentValue", 0)
            context["total_actual_detergent_injected"] = children.get(
                "ActualInjectedTotal", {}
            ).get("currentValue", 0)
            context["difference"] = children.get("Difference", {}).get(
                "currentValue", 0
            )
            return context

        return None
