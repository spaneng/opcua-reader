import logging
import time
from typing import Any

from pydoover.docker import Application

from .app_config import OpcuaReaderConfig
from .app_ui import OpcuaReaderUI
from .injector import Injector
from .opcua_client import AsyncUAClient
from .overview import Overview

log = logging.getLogger()

# How long a pending ui_state aggregate patch may coalesce before the DDA
# pushes it to the cloud.
UI_STATE_MAX_AGE_SECS = 5
# The reconciliation report reads ui_state *message history*, so periodically
# log a snapshot of the patched values as a channel message.
UI_STATE_LOG_PERIOD_SECS = 300


class OpcuaReaderApplication(Application):
    config_cls = OpcuaReaderConfig
    ui_cls = OpcuaReaderUI

    async def setup(self):
        self.started = time.time()
        self.loop_target_period = 5

        # name -> (path below app node, values) queued for the next ui_state patch
        self._pending_ui_values: dict[tuple[str, ...], dict[str, Any]] = {}
        self._pending_ui_props: dict[tuple[str, ...], dict[str, Any]] = {}
        self._last_ui_state_log = 0.0

        # Initialise OPCUA Client
        self.server_uri = self.config.opcua_uri.value
        self.opcua_client = AsyncUAClient(self.server_uri)
        await self.opcua_client.setup()
        log.info("OPC UA Client setup complete.")

        # Initialise Injectors
        self.injectors = []
        for inj_conf in self.config.injectors.elements:
            injector = Injector(
                int(inj_conf.injector_index.value),
                inj_conf.injector_name.value,
                self.opcua_client,
                self,
                self.config.timezone.value,
            )
            await injector.setup()
            self.injectors.append(injector)

            log.info(
                f"Injector {inj_conf.injector_name.value}; "
                f"{inj_conf.injector_index.value} initialized."
            )

        # Initialise Overview
        self.overview = Overview(
            self.opcua_client,
            self,
            injectors=self.injectors,
            timezone=self.config.timezone.value,
        )
        await self.overview.setup()

    async def main_loop(self):
        await self.overview.main_loop()
        for injector in self.injectors:
            await injector.main_loop()

        await self.flush_ui_values()

    # --- legacy remote-component value plumbing -----------------------------
    #
    # The HMI and Reconciliation widgets read literal `currentValue`s from
    # their children in ui_state (v1 behaviour), so those values cannot be
    # tag-bound. Instead, injectors and the overview queue values here and the
    # main loop flushes them as one deep-merge patch on the ui_state channel.

    def queue_ui_values(
        self,
        path: list[str],
        values: dict[str, Any],
        node_props: dict[str, Any] | None = None,
    ):
        """Queue literal currentValue updates for elements below the app node.

        ``path`` is the chain of element names below this app's node in
        ui_state, ``values`` maps child element name -> value, and
        ``node_props`` are extra properties merged onto the element at
        ``path`` itself.
        """
        key = tuple(path)
        self._pending_ui_values.setdefault(key, {}).update(values)
        if node_props:
            self._pending_ui_props.setdefault(key, {}).update(node_props)

    def _build_ui_state_patch(self) -> dict[str, Any]:
        app_children: dict[str, Any] = {}
        for key in set(self._pending_ui_values) | set(self._pending_ui_props):
            children = app_children
            node: dict[str, Any] = {}
            for name in key:
                node = children.setdefault(name, {})
                children = node.setdefault("children", {})
            node.update(self._pending_ui_props.get(key, {}))
            for name, value in self._pending_ui_values.get(key, {}).items():
                children.setdefault(name, {})["currentValue"] = value

        return {"state": {"children": {self.app_key: {"children": app_children}}}}

    async def flush_ui_values(self):
        if not (self._pending_ui_values or self._pending_ui_props):
            return

        patch = self._build_ui_state_patch()
        self._pending_ui_values = {}
        self._pending_ui_props = {}

        await self.update_channel_aggregate(
            "ui_state", patch, max_age_secs=UI_STATE_MAX_AGE_SECS
        )

        now = time.time()
        if now - self._last_ui_state_log >= UI_STATE_LOG_PERIOD_SECS:
            self._last_ui_state_log = now
            await self.create_message("ui_state", patch)
