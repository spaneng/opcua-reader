from pathlib import Path

from pydoover import config


class AlarmConfig(config.Object):
    name = config.String(
        "Alarm Name",
        description="Name of the alarm",
    )
    high_low = config.Enum(
        "Alarm Condition",
        description="High: value greater than limit, Low: value less than limit",
        choices=["High", "Low"],
        default=config.NotSet,
    )
    min_alarm = config.Number(
        "Minimum Alarm Value",
        description="Minimum value for the alarm to trigger",
        default=0.0,
    )
    max_alarm = config.Number(
        "Maximum Alarm Value",
        description="Maximum value for the alarm to trigger",
        default=100.0,
    )
    grace_period = config.Number(
        "Grace Period (s)",
        description="Duration threshold has to be met before calling alarm",
        default=60 * 10.0,  # 10 minutes
    )


class OpcuaVariableConfig(config.Object):
    name_space_index = config.String(
        "Name Space Index",
        description="Name Space Index of the OPC UA variable",
    )
    variable_name = config.String(
        "Variable Name",
        description="Name of the OPC UA variable to read",
    )
    sensor_object_name = config.String(
        "Sensor Object Name",
        description="Name of the sensor object in the OPC UA server",
    )
    data_type = config.Enum(
        "Data Type",
        description="Data type of the OPC UA variable",
        choices=["Int", "Float", "String", "Boolean"],
        default=config.NotSet,
    )
    units = config.String(
        "Units",
        description="Unit of the OPC UA variable, e.g. '°C', 'V', 'm/s', etc",
        default="",
    )
    alarms = config.Array(
        "Variable Alarms",
        description="Alarms associated with this OPC UA variable",
        element=AlarmConfig("Alarm"),
    )


class OpcuaReaderConfig(config.Schema):
    opcua_uri = config.String(
        "OPCUA Address",
        description="OPC UA server URI, e.g. opc.tcp://localhost:4840/freeopcua/server/",
    )
    opcua_values = config.Array(
        "OPCUA Server Values", element=OpcuaVariableConfig("OPCUA Variable")
    )


def export():
    OpcuaReaderConfig.export(
        Path(__file__).parents[2] / "doover_config.json", "opcua_reader"
    )


if __name__ == "__main__":
    export()
