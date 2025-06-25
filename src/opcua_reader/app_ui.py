from pydoover import ui


class OpcuaReaderUI:
    def __init__(self, config):
        self._config = config

        self.get_ui_from_config()




        self.is_working = ui.BooleanVariable("is_working", "We Working?")
        self.uptime = ui.DateTimeVariable("uptime", "Started")

        self.send_alert = ui.Action("send_alert", "Send message as alert", position=1)
        self.text_parameter = ui.TextParameter("test_message", "Put in a message")

        self.test_output = ui.TextVariable("test_output", "This is message we got")

        self.battery = ui.Submodule("battery", "Battery Module")
        self.battery_voltage = ui.NumericVariable(
            "voltage", "Battery Voltage", precision=2, ranges=[
                ui.Range("Low", 0, 10, ui.Colour.red),
                ui.Range("Normal", 10, 20, ui.Colour.green),
                ui.Range("High", 20, 30, ui.Colour.blue),
            ])

        self.battery_low_voltage_alert = ui.NumericParameter("low_voltage_alert", "Low Voltage Alert")
        self.battery_charge_mode = ui.StateCommand("charge_mode", "Charge Mode", user_options=[
            ui.Option("charge", "Charge"),
            ui.Option("discharge", "Discharge"),
            ui.Option("idle", "Idle")
        ])
        self.battery.add_children(self.battery_voltage, self.battery_low_voltage_alert, self.battery_charge_mode)

    def get_ui_from_config(self):
        for var in self._config.read_values.elements:
            nsidx = var.name_space_index.value
            var_name = var.variable_name.value
            data_type = var.data_type.value
            units = var.units.value
            if units:
                var_name = f"{var_name} ({units})"


            match data_type:
                case "Int":
                    ui_var = ui.NumericVariable(f"{nsidx}_{var_name}", var_name, precision=0)
                case "Float":
                    ui_var = ui.NumericVariable(f"{nsidx}_{var_name}", var_name, precision=2)
                case "String":
                    ui_var = ui.TextVariable(f"{nsidx}_{var_name}", var_name)
                case "Boolean":
                    ui_var = ui.BooleanVariable(f"{nsidx}_{var_name}", var_name)
                case _:
                    raise ValueError(f"Unsupported data type: {data_type}")
            setattr(self, f"{nsidx}_{var_name}", ui_var)

    def fetch(self):
        ui_elements = []
        for attr in dir(self):
            if not attr.startswith("_") and not callable(getattr(self, attr)):
                ui_elements.append(getattr(self, attr))
        return ui_elements
    
    def update(self, is_working, voltage, uptime):
        self.is_working.update(is_working)
        self.uptime.update(uptime)
        self.battery_voltage.update(voltage)
