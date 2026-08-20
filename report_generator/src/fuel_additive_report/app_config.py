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


def export() -> None:
    FuelAdditiveReportConfig.export(
        Path(__file__).parents[2] / "doover_config.json",
        "fuel_additive_report_generator",
    )
