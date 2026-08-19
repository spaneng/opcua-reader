import logging

from pydoover import ui

log = logging.getLogger(__name__)


def element_name(nsidx: str, var_name: str) -> str:
    """Element/tag name for a configured OPC UA variable."""
    return f"{nsidx}_{var_name}"


def slider_name(nsidx: str, var_name: str, alarm_name: str) -> str:
    """Element name for a variable's alarm-point slider."""
    return f"{nsidx}_{var_name}_{alarm_name}_slider"


class OpcuaReaderUI(ui.UI):
    """UI built at runtime from the configured OPC UA variables.

    Each variable gets a display element whose value is bound to the tag the
    application sets for it, plus a slider per configured alarm to set the
    alarm point.
    """

    async def setup(self):
        alarm_elems = []
        for var in self.config.opcua_values.elements:
            nsidx = var.name_space_index.value
            var_name = var.variable_name.value
            data_type = var.data_type.value
            units = var.units.value

            display_name = var_name
            if units:
                display_name = f"{var_name} ({units})"

            name = element_name(nsidx, var_name)
            match data_type:
                case "Int":
                    elem = ui.NumericVariable(
                        display_name,
                        value=ui.tag_ref(name, "number"),
                        precision=0,
                        name=name,
                    )
                case "Float":
                    elem = ui.NumericVariable(
                        display_name,
                        value=ui.tag_ref(name, "number"),
                        precision=2,
                        name=name,
                    )
                case "String":
                    elem = ui.TextVariable(
                        display_name, value=ui.tag_ref(name, "string"), name=name
                    )
                case "Boolean":
                    elem = ui.BooleanVariable(
                        display_name, value=ui.tag_ref(name, "boolean"), name=name
                    )
                case _:
                    raise ValueError(f"Unsupported data type: {data_type}")
            self.add_element(elem)

            sliders = []
            for alm in var.alarms.elements:
                if not alm.name.value:
                    log.warning(
                        f"Alarm name is empty for variable {var_name}. Skipping alarm slider."
                    )
                    continue
                sliders.append(self._make_alarm_slider(nsidx, var_name, alm))

            if len(sliders) == 1:
                alarm_elems.append(sliders[0])
            elif sliders:
                alarm_elems.append(
                    ui.Submodule(
                        display_name, children=sliders, name=f"{name}_alm_settings"
                    )
                )

        if alarm_elems:
            self.add_element(
                ui.Submodule(
                    "Alarms Settings",
                    children=alarm_elems,
                    name="opcua_reader_alarms",
                )
            )

    @staticmethod
    def _make_alarm_slider(nsidx, var_name, alm):
        min_val = alm.min_alarm.value
        max_val = alm.max_alarm.value
        return ui.Slider(
            alm.name.value,
            min_val=min_val,
            max_val=max_val,
            step_size=0.1,
            dual_slider=False,
            # An inverted slider shades [value, max]; for a High alarm this makes
            # the shaded band the range that alarms, matching the old behaviour.
            inverted=alm.high_low.value != "Low",
            default=min_val + (max_val - min_val) / 2,
            name=slider_name(nsidx, var_name, alm.name.value),
        )
