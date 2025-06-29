from pathlib import Path

from pydoover import config


class Alarm(config.Object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = config.String(
            "Alarm Name", 
            description="Name of the alarm"
        )

        self.high_low = config.Enum(
            "Alarm Condition",
            description="High: value greater than limit, Low: value less than limit",
            choices=["High", "Low"]
        )

        self.min_alarm = config.Number(
            "Minimum Alarm Value",
            description="Minimum value for the alarm to trigger",
            default=0.0,
        )
        
        self.max_alarm = config.Number(
            "Maximum Alarm Value",
            description="Maximum value for the alarm to trigger",
            default=100.0
        )
        
        self.grace_period = config.Number(
            "Grace Period (s)",
            description="Duration threshold has to be met before calling alarm",
            default = 60*10.0 # 10 minutes
        )

class OPCUAVariable(config.Object):
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

        alarmObjs = Alarm("Alarm")
        
        self.alarms = config.Array(
            "Variable Alarms",
            description="Alarms associated with this OPC UA variable",
            element=alarmObjs,
        )
class OpcuaReaderConfig(config.Schema):
    def __init__(self):

        self.opcua_uri = config.String(
            "OPCUA Address",
            description="OPC UA server URI, e.g. opc.tcp://localhost:4840/freeopcua/server/",
        )

        opcua_node_elems = OPCUAVariable("OPCUA Variable")

        self.opcua_values = config.Array("OPCUA Server Values", element=opcua_node_elems)

        # self.sim_app_key = config.Application("Simulator App Key", description="The app key for the simulator")


if __name__ == "__main__":
    OpcuaReaderConfig().export(Path(__file__).parent.parent.parent / "doover_config.json", "opcua_reader")
