from pathlib import Path

from pydoover import config
from pydoover.processor import (
    ExtendedPermissionsConfig,
    ScheduleConfig,
    TimezoneConfig,
)


class FuelAdditiveReportConfig(config.Schema):
    dv_proc_extended_permissions = ExtendedPermissionsConfig()
    # The PLC clears the daily data at midnight; run shortly after 1am Saudi
    # time so the report captures the last injection of the day.
    dv_proc_schedules = ScheduleConfig(
        allowed_modes=["cron"],
        default="cron(0 1 * * ?)",
    )
    dv_proc_timezone = TimezoneConfig(default="Asia/Riyadh")
    # The data plane emails a finished report to `config.dv_emails` verbatim
    # (doover-data reports hook), so the key has to be exactly that - the
    # display name would otherwise sanitise to `email_destinations` and no
    # email would ever be sent. Defaulted to empty rather than required so the
    # existing install keeps generating until someone fills the addresses in.
    dv_emails = config.Array(
        "Email Destinations",
        name="dv_emails",
        element=config.String("Email Address", name="dv_email"),
        default=[],
        description="Email addresses to send this report to once it is generated.",
    )


def export() -> None:
    FuelAdditiveReportConfig.export(
        Path(__file__).parents[2] / "doover_config.json",
        "fuel_additive_report_generator",
    )
