import enum
from pathlib import Path

from pydoover import config


class Timezone(enum.Enum):
    SYDNEY = "Australia/Sydney"
    BRISBANE = "Australia/Brisbane"
    MELBOURNE = "Australia/Melbourne"
    PERTH = "Australia/Perth"
    ADELAIDE = "Australia/Adelaide"
    DARWIN = "Australia/Darwin"
    HOBART = "Australia/Hobart"
    RIYADH = "Asia/Riyadh"
    DUBAI = "Asia/Dubai"
    KUWAIT = "Asia/Kuwait"
    BAHRAIN = "Asia/Bahrain"
    OMAN = "Asia/Muscat"
    QATAR = "Asia/Qatar"
    KSA = "Asia/Riyadh"


class InjectorConfig(config.Object):
    injector_name = config.String(
        "Injector Name",
        description="Name of the injector",
    )
    injector_index = config.Integer(
        "Injector Index",
        description="Index of the injector, used for the OPC UA node names",
    )


class OpcuaReaderConfig(config.Schema):
    opcua_uri = config.String(
        "OPCUA Address",
        description="OPC UA server URI, e.g. opc.tcp://localhost:4840/freeopcua/server/",
    )
    skid_name = config.String(
        "Skid Name",
        description=(
            "Short site/skid code used to title the reconciliation report and "
            "name its PDF, e.g. SJBP. Leave blank to use the app display name."
        ),
        default="",
    )
    injectors = config.Array(
        "Injectors",
        description="List of injectors, names MUST be unique",
        element=InjectorConfig("Injector"),
    )
    timezone = config.String(
        "Timezone",
        description="Timezone of the report, e.g. America/New_York",
        default=Timezone.RIYADH.value,
    )
    report_restart_time = config.Integer(
        "Report Restart Time",
        description="Time in Hrs to restart the report, 6=6am, 12=noon, 17=5pm etc.",
        default=10,
    )


def export():
    OpcuaReaderConfig.export(
        Path(__file__).parents[2] / "doover_config.json", "fuel_additive_opcua_reader"
    )
