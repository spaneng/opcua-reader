import logging
import time
import asyncio
import types

from typing import Any
from asyncua import Client
from pydoover.docker import Application, DeviceAgentInterface
from pydoover import ui

from .app_config import OpcuaReaderConfig
from .opcua_client import AsyncUAClient
from .overview import Overview
from .injector import Injector

log = logging.getLogger()

class OpcuaReaderApplication(Application):
    config: OpcuaReaderConfig  # not necessary, but helps your IDE provide autocomplete!

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.started = time.time()
        self.injectors = []
        
    async def setup(self):
        self.loop_pause_period = 5
        self.ui_elems = [ui.AlertStream("opcua_reader_alerts", "OPC UA Reader Alerts")]
        print(dir(self.config.opcua_uri))

        print(self.config.opcua_uri.__dict__)

        # Initializa OPCUA Client
        self.server_uri = self.config.opcua_uri.value
        self.opcua_client = AsyncUAClient(self.server_uri)
        await self.opcua_client.setup()
        log.info("OPC UA Client setup complete.")
        
        # Initialize Overview
        self.overview = Overview(self.opcua_client, self.device_agent)
        await self.overview.setup()
        self.ui_elems.extend(self.overview.fetch_ui())
        print("ui_elems after overview is included", self.ui_elems)
        
        # Initialize Injectors
        self.no_injectors = self.config.no_of_injectors.value
        print(f"Number of injectors: {self.no_injectors}")
        for inj in range(self.no_injectors):
            idx = inj + 1
            injector = Injector(
                idx,
                self.opcua_client, 
                self.device_agent,
            )
            await injector.setup()
            self.injectors.append(injector)
            self.ui_elems.append(await injector.fetch_ui())
            
            log.info(f"Injector {idx} initialized.")

        self.ui_manager.add_children(*self.ui_elems)
        self.ui_manager.set_display_name("OPC UA Reader")

    async def main_loop(self):
        print("running main loop")
        await self.overview.main_loop()
        for injector in self.injectors:
            await injector.main_loop()
    

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