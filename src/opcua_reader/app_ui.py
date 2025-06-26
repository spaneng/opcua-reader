from pydoover import ui
import logging

log = logging.getLogger()
class OpcuaReaderUI:
    def __init__(self, config):
        self._config = config

        self.get_ui_from_config()

        self.alert_stream = ui.AlertStream("opcua_reader_alerts", "OPC UA Reader Alerts")

    def get_ui_from_config(self):
        alarm_elems = []
        for var in self._config.opcua_values.elements:

            nsidx = var.name_space_index.value
            var_name = var.variable_name.value
            data_type = var.data_type.value
            units = var.units.value
            
            display_name = var_name
            if units:
                display_name = f"{var_name} ({units})"

            match data_type:
                case "Int":
                    ui_var = ui.NumericVariable(f"{nsidx}_{var_name}", display_name, precision=0)
                case "Float":
                    ui_var = ui.NumericVariable(f"{nsidx}_{var_name}", display_name, precision=2)
                case "String":
                    ui_var = ui.TextVariable(f"{nsidx}_{var_name}", display_name)
                case "Boolean":
                    ui_var = ui.BooleanVariable(f"{nsidx}_{var_name}", display_name)
                case _:
                    raise ValueError(f"Unsupported data type: {data_type}")
            setattr(self, f"{nsidx}_{var_name}", ui_var)

            # create alarm UI
            lalm = len(var.alarms.elements)
            print(f"Number of alarms for {var_name}: {lalm}")
            alm_elem = None
            if lalm == 1:
                alm = var.alarms.elements[0]
                alm_name = alm.name.value
                alm_elem = ui.Slider(
                    f"{nsidx}_{var_name}_{alm_name}_slider",
                    f"{alm_name}",
                    min_val=alm.min_alarm.value,
                    max_val=alm.max_alarm.value,
                    step=0.1,
                    value=alm.min_alarm.value +((alm.max_alarm.value-alm.min_alarm.value) / 2),
                    inverted=False if alm.high_low.value == "Low" else True,
                )
            elif lalm > 1:
                sliders = []
                for alm in var.alarms.elements:
                    alm_name = alm.name.value
                    if alm_name:
                        alm_elem = ui.Slider(
                            f"_{nsidx}_{var_name}_{alm_name}_slider",
                            f"{alm_name} Alarms",
                            min_val=alm.min_alarm.value,
                            max_val=alm.max_alarm.value,
                            step=0.1,
                            value=alm.min_alarm.value +((alm.max_alarm.value-alm.min_alarm.value) / 2),
                            inverted=False if alm.high_low.value == "Low" else True,
                        )
                        setattr(self, f"_{nsidx}_{var_name}_{alm_name}_slider", alm_elem)
                        sliders.append(alm_elem)
                    else:
                        raise ValueError("Alarm name cannot be empty")

                alm_elem = ui.Submodule(
                    f"_{nsidx}_{var_name}_alm_settings",
                    f"{display_name}",
                    children=sliders
                )
            if alm_elem is not None:
                setattr(self, f"_{nsidx}_{var_name}_alm", alm_elem)
                alarm_elems.append(getattr(self, f"_{nsidx}_{var_name}_alm"))

        if len(alarm_elems) > 0:
            print("adding alarms to UI")
            self.alarms = ui.Submodule(
                "opcua_reader_alarms",
                "Alarms Settings",
                children=alarm_elems
            )

    def fetch(self):
        ui_elements = [self.alert_stream]
        for attr in dir(self):
            if not attr.startswith("_") and not callable(getattr(self, attr)):
                ui_elements.append(getattr(self, attr))
        return ui_elements

    def update(self, values):
        for value in values:
            nsidx = value["nsidx"]
            var_name = value["var_name"]
            ui_var = getattr(self, f"{nsidx}_{var_name}", None)
            if ui_var:
                log.info(f"Updating UI variable {ui_var.name} with value {value['value']}")
                ui_var.update(value["value"])
            else:
                log.warning(f"UI variable {nsidx}_{var_name} not found")

    # def update(self, is_working, voltage, uptime):
    #     self.is_working.update(is_working)
    #     self.uptime.update(uptime)
    #     self.battery_voltage.update(voltage)
