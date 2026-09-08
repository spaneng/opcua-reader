from pathlib import Path

from pydoover.processor import ScheduleConfig, TimezoneConfig
from pydoover.reports import ReportConfig


class FuelAdditiveReportConfig(ReportConfig):
    """Config for the fuel additive reconciliation report.

    Device permissions and the email destinations the finished report is sent
    to come from :class:`pydoover.reports.ReportConfig`. Only the schedule and
    timezone are overridden here - a subclass declaration replaces the
    inherited element of the same name and keeps its position in the form.
    """

    # ReportConfig runs monthly at 8am. The PLC clears the daily data at
    # midnight, so run shortly after 1am Saudi time instead, to capture the
    # last injection of the day.
    dv_proc_schedules = ScheduleConfig(
        allowed_modes=["cron"],
        default="cron(0 1 * * ?)",
    )
    dv_proc_timezone = TimezoneConfig(default="Asia/Riyadh")


def export() -> None:
    FuelAdditiveReportConfig.export(
        Path(__file__).parents[2] / "doover_config.json",
        "fuel_additive_report_generator",
    )
