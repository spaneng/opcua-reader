from pydoover import ui
import logging

log = logging.getLogger()
class OpcuaReaderUI:
    def __init__(self, config):
        self._config = config

        self.get_ui_from_config()

    def get_ui_from_config(self):
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

    def fetch(self):
        ui_elements = []
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
