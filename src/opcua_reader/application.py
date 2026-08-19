import logging
import time

from asyncua import Client
from pydoover.docker import Application
from pydoover.utils.alarm import create_alarm

from .app_config import OpcuaReaderConfig
from .app_ui import OpcuaReaderUI, element_name, slider_name

log = logging.getLogger()

# The data plane deserialises severity as the serde variant name, not the int
# value that pydoover.models.NotificationSeverity carries.
NOTIFICATION_SEVERITY_WARN = "Warn"


class OpcuaReaderApplication(Application):
    config_cls = OpcuaReaderConfig
    ui_cls = OpcuaReaderUI

    async def setup(self):
        self.started = time.time()
        self.loop_target_period = 5

        self.server_uri = self.config.opcua_uri.value
        self.vars = self.config.opcua_values.elements

        self.alarms = {}
        self.init_alarms()

    async def main_loop(self):
        values = await self.get_server_values()
        if not values:
            log.error("Failed to fetch server values.")
            return

        for value in values:
            await self.set_tag(
                element_name(value["nsidx"], value["var_name"]), value["value"]
            )

    def init_alarms(self):
        # Alarm sliders live inside submodules, so look them up through the
        # UI's recursive interaction registry rather than as attributes.
        interactions = self.ui.get_interactions()

        for var in self.vars:
            nsidx = var.name_space_index.value
            var_name = var.variable_name.value

            for alm in var.alarms.elements:
                alm_name = alm.name.value
                if not alm_name:
                    log.warning(
                        f"Alarm name is empty for variable {var_name}. Skipping alarm creation."
                    )
                    continue

                slider = interactions[slider_name(nsidx, var_name, alm_name)]
                high = alm.high_low.value == "High"

                self.alarms[(nsidx, var_name, alm_name)] = create_alarm(
                    self._passthrough,
                    self._make_threshold(slider, high),
                    self._make_alarm_callback(
                        alm_name, "above" if high else "below", slider
                    ),
                    grace_period=alm.grace_period.value,
                )

    @staticmethod
    async def _passthrough(value):
        return value

    @staticmethod
    def _slider_level(slider):
        # A slider the operator has never moved has no stored value, so reading
        # it raises (AttributeError when no manager is attached, e.g. in tests).
        # Fall back to its default (the midpoint of its range).
        try:
            return slider.value
        except (KeyError, AttributeError):
            return slider.default

    def _make_threshold(self, slider, high: bool):
        def threshold_met(value):
            level = self._slider_level(slider)
            if value is None or level is None or not isinstance(value, (int, float)):
                return False
            return value > level if high else value < level

        return threshold_met

    def _make_alarm_callback(self, alm_name: str, alert_txt: str, slider):
        async def callback():
            level = self._slider_level(slider)
            message = f"Alert: {alm_name} is {alert_txt} {level}"
            await self.create_message(
                "notifications",
                {"message": message, "severity": NOTIFICATION_SEVERITY_WARN},
            )
            log.info(f"ALARM: {message}")

        return callback

    async def get_server_values(self):
        if self.server_uri is None:
            log.error("No OPC UA URI provided in the configuration.")
            return None

        res = []
        async with Client(url=self.server_uri) as client:
            log.info("Connected to OPC UA Server at %s", self.server_uri)

            objects = client.nodes.objects

            for var in self.vars:
                nsidx = var.name_space_index.value
                var_name = var.variable_name.value
                snsr_name = var.sensor_object_name.value

                try:
                    sensor_node = await objects.get_child([f"{nsidx}:{snsr_name}"])
                    var_node = await sensor_node.get_child([f"{nsidx}:{var_name}"])
                    value = await var_node.read_value()
                    log.info("Value of %s: %s", var_name, value)
                except Exception as e:
                    log.error("Error reading variable %s: %s", var_name, e)
                    value = None

                res.append({"nsidx": nsidx, "var_name": var_name, "value": value})

                for alm in var.alarms.elements:
                    check_alarm = self.alarms.get((nsidx, var_name, alm.name.value))
                    if check_alarm is not None:
                        await check_alarm(value)

        return res
