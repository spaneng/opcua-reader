from pathlib import Path

from pydoover import config

class opcua_variable(config.Object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name_space_index = config.String(
            "Name Space Index", 
            description="Name Space Index of the OPC UA variable"
        )
        self.variable_name = config.String(
            "Variable Name",
            description="Name of the OPC UA variable to read"
        )
        self.sensor_object_name = config.String(
            "Sensor Object Name",
            description="Name of the sensor object in the OPC UA server"
        )
        self.data_type = config.Enum(
            "Data Type",
            description="Data type of the OPC UA variable",
            choices=["Int", "Float", "String", "Boolean"]
        )
        self.units = config.String(
            "Units",
            description="Unit of the OPC UA variable, e.g. '°C', 'V', 'm/s', etc",
            default=""
        )
        
class OpcuaReaderConfig(config.Schema):
    def __init__(self):

        self.opcua_uri = config.String(
            "OPCUA Address",
            description="OPC UA server URI, e.g. opc.tcp://localhost:4840/freeopcua/server/",
        )

        opcua_node_elems = opcua_variable("OPCUA Variable")

        self.opcua_values = config.Array("OPCUA Server Values", element=opcua_node_elems)

        # self.sim_app_key = config.Application("Simulator App Key", description="The app key for the simulator")


if __name__ == "__main__":
    OpcuaReaderConfig().export(Path(__file__).parent.parent.parent / "doover_config.json", "opcua_reader")
