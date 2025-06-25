import logging
import time
import asyncio

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
        self.ui = OpcuaReaderUI()
        # self.state = OpcuaReaderState()

        self.server_uri = self.config.opcua_uri.value
        self.vars = self.config.opcua_values.elements

        self.client = Client(self.server_uri)
        
    async def setup(self):
        self.ui_manager.add_children(*self.ui.fetch())

    async def main_loop(self):
        # log.info(f"State is: {self.state.state}")
        server_vals = await self.get_server_values()
        if server_vals:
            log.info("Server values fetched successfully.")
            await self.update_ui(server_vals)
        else:
            log.error("Failed to fetch server values.")
        asyncio.sleep(5)

    async def get_server_values(self):
        res = []
        if self.ua_uri is None:
            log.error("No OPC UA URI provided in the configuration.")
            return
        
        async with Client(url=self.ua_uri) as client:
            log.info("Connected to OPC UA Server at %s", self.ua_uri)

            objects = client.nodes.objects
            log.info("Objects node is: %r", objects)

            for var in self.config.read_values.elements:
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
    
    async def update_ui(self, values):
        for value in values:
            nsidx = value["nsidx"]
            var_name = value["var_name"]
            ui_var = getattr(self.ui, f"{nsidx}_{var_name}", None)
            if ui_var:
                log.info(f"Updating UI variable {ui_var.name} with value {value['value']}")
                ui_var.update(value["value"])
            else:
                log.warning(f"UI variable {nsidx}_{var_name} not found")
