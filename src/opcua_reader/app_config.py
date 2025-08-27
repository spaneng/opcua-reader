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

class OpcuaReaderConfig(config.Schema):
    def __init__(self):

        self.opcua_uri = config.String(
            "OPCUA Address",
            description="OPC UA server URI, e.g. opc.tcp://localhost:4840/freeopcua/server/",
        )
        
        injector = config.Object(
            "Injector",
            description="Injector configuration",
        )
        
        injector.add_elements(
            config.String(
                "Injector Name",
                description="Name of the injector",
            ),
            config.Integer(
                "Injector Index",
                description="Index of the injector, used for the OPC UA node names",
            )
        )
        
        self.injectors = config.Array(
            "Injectors",
            description="List of injectors, names MUST be unique",
            element=injector
        )
        
        self.timezone = config.String(
            "Timezone",
            description="Timezone of the report, e.g. America/New_York",
            default=Timezone.RIYADH.value
        )
        
        self.report_restart_time = config.Integer(
            "Report Restart Time",
            description="Time in Hrs to restart the report, 6=6am, 12=noon, 17=5pm etc.",
            default=10
        )

def export():
    OpcuaReaderConfig().export(Path(__file__).parent.parent.parent / "doover_config.json", "fuel_additive_opcua_reader")
