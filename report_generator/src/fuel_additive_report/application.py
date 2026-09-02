import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pydoover.models import File
from pydoover.reports import Application

from .app_config import FuelAdditiveReportConfig
from .build_pdf import build_pdf

log = logging.getLogger(__name__)

REPORT_TIMEZONE = "Asia/Riyadh"


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
            filename = f"{context['skid_name']}.pdf"
            files.append(File(filename, "application/pdf", len(pdf_bytes), pdf_bytes))

        if not files:
            raise RuntimeError("No reconciliation data found for any device.")
        return files

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
            injector_meta = reconciliation_state.get("injectors") or []
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
            context["skid_name"] = (
                reconciliation_state.get("skid_name") or f"skid-{agent_id}"
            )
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
