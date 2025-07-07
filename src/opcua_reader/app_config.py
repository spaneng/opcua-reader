from pathlib import Path

from pydoover import config


class OpcuaReaderConfig(config.Schema):
    def __init__(self):

        self.opcua_uri = config.String(
            "OPCUA Address",
            description="OPC UA server URI, e.g. opc.tcp://localhost:4840/freeopcua/server/",
        )
        
        self.no_of_injectors = config.Enum(
            "Number of Injectors",
            description="Number of injectors to monitor",
            choices=[2, 3, 6]
        )

if __name__ == "__main__":
    OpcuaReaderConfig().export(Path(__file__).parent.parent.parent / "doover_config.json", "fuel_additive_opcua_reader")
