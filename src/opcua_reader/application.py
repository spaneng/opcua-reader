import logging
import time
import asyncio

from typing import Any
from asyncua import Client
from pydoover.docker import Application
from pydoover import ui

from .app_config import OpcuaReaderConfig
from .app_ui import OpcuaReaderUI
from .app_state import OpcuaReaderState

log = logging.getLogger()

class OpcuaReaderApplication(Application):
    config: OpcuaReaderConfig  # not necessary, but helps your IDE provide autocomplete!

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.started = time.time()
        
        
    async def setup(self):
        self.ui = OpcuaReaderUI(self.config)
        self.loop_pause_period = 5

        self.server_uri = self.config.opcua_uri.value
        self.vars = self.config.opcua_values.elements

        self.ui_manager.add_children(*self.ui.fetch())
        self.ui_manager.set_display_name("OPC UA Reader")
        

    async def main_loop(self):
        # log.info(f"State is: {self.state.state}")
        server_vals = await self.get_server_values()
        if server_vals:
            log.info("Server values fetched successfully.")
            values = await self.get_server_values()
            self.ui.update(values)
            log.info("UI updated with new values.")
        else:
            log.error("Failed to fetch server values.")
        

    async def get_server_values(self):
        res = []
        if self.server_uri is None:
            log.error("No OPC UA URI provided in the configuration.")
            return
        
        async with Client(url=self.server_uri) as client:
            log.info("Connected to OPC UA Server at %s", self.server_uri)

            objects = client.nodes.objects
            log.info("Objects node is: %r", objects)

            for var in self.config.opcua_values.elements:
    
                nsidx = var.name_space_index.value
                var_name = var.variable_name.value
                snsr_name = var.sensor_object_name.value

                sensor_obj = await objects.get_child([f"{nsidx}:{snsr_name}"])
                try:
                    _variable = await sensor_obj.get_child([f"{nsidx}:{var_name}"])  
                    value = await _variable.read_value()
                    log.info("Value of MyVariable: %s", value)
                except Exception as e:
                    log.error("Error reading variable: %s", e)
                    value = None
                res.append({
                    "nsidx": nsidx,
                    "var_name": var_name,
                    "value": value
                })
                
        return res
    
    async def _on_deployment_config_update(self, channel_name, config: dict[str, Any]):
        # this uses an internal method because we don't have a good way of "application discovery" at the moment.
        # however, we want to set the UI variant based on the number of vega nodes. Usually this will be 1.
        await super()._on_deployment_config_update(channel_name, config)
        num_vegas = len([n for n in config["applications"] if "opcua_reader" in n])
        if num_vegas > 1 or len(config["applications"]) > 5:
            log.info("Multiple sensors/apps detected. Setting UI variant to `submodule`.")
            self.ui_manager.set_variant("submodule")
        else:
            log.info("Single sensor detected. Setting UI variant to `stacked`.")
            self.ui_manager.set_variant("stacked")