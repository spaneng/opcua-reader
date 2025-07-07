import logging

import asyncio

from pydoover.docker import DeviceAgentInterface
from pydoover import ui

from .opcua_client import AsyncUAClient

log = logging.getLogger()

class AlarmObj:
    def __init__(self, name_base: str, obj_name: str = "Warnings"):
        self.name_base = name_base
        
        self.obj_name = obj_name
        self.active_id = f'ns=3;s="DB_OPCUA_{obj_name}"."{self.obj_name}"[{self.name_base}]."Active"'
        self.timestamp_id = f'ns=3;s="DB_OPCUA_{obj_name}"."{self.obj_name}"[{self.name_base}]."Timestamp"'
        self.alarm_text_id = f'ns=3;s="DB_OPCUA_{obj_name}"."{self.obj_name}"[{self.name_base}]."AlarmText"'
        self.code_id = f'ns=3;s="DB_OPCUA_{obj_name}"."{self.obj_name}"[{self.name_base}]."Code"'
        
    def get_node_ids(self):
        return [
            self.active_id,
            self.timestamp_id,
            self.alarm_text_id,
            self.code_id
        ]
        
class PollingNode:
    def __init__(self, name_base: str, ):
        self.name_base = name_base
        self.name = f"{name_base}"
        self.node_id = f'ns=3;s="DB_OPCUA_AnalogValues"."{self.name_base}"'
        

class Overview:
    _alarm_sub_node_name_bases = [
        1,
        3,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        31,
        32,
        33,
        34,
        35,
        37,
        38,
        45,
        50,
        51,
        56,
        60,
        61,
        65,
        66,
        111,
        112,
        113,
        114,
        115,
        116,
        117,
        118,
        119,
        120,
        121,
        122,
        123,
        124,
        129,
        130,
    ]

    _polling_node_name_bases = [
        "LevelTank1",
        "LevelTank2",
        "Pressure",
        "ShelterTemperature",
        "TemperaturePump1",
        "TemperaturePump2"
    ]
    
    def __init__(
        self, 
        opcua_client: AsyncUAClient,
        dda: DeviceAgentInterface,
    ):
        self.client = opcua_client
        self.dda = dda
        self.polling_nodes = []
        self.alarm_objs = []
        
    
    def set_polling_nodes(self):
        nodes = []
        for node_base in self._polling_node_name_bases:
            node = PollingNode(node_base)
            nodes.append(node)
        self.polling_nodes = nodes
        
    def get_alarm_node_ids(self):
        node_ids = []
        for obj in self.alarm_objs:
            node_ids.extend(obj.get_node_ids())
        return node_ids
    
    def get_polling_node_ids(self):
        return [node.node_id for node in self.polling_nodes]
    
    def set_alarm_objs(self):
        nodes = []
        for node_base in self._alarm_sub_node_name_bases:
            node = AlarmObj(node_base,  obj_name="Warnings")
            nodes.append(node)
        self.alarm_objs = nodes
        
    async def setup(self):
        self.set_polling_nodes()
        self.set_alarm_objs()
        node_ids = [node_id for node_id in self.get_polling_node_ids() + self.get_alarm_node_ids()]
        
        await self.client.register_nodes(node_ids)
        await self.create_alarm_subs()
        
        # main loop -> get polling data and push to ui
        
    async def get_alarm_sub_cb(self, node_obj):
        async def alarm_sub_cb(node, val):
            """
            Callback for the alarm subscription.
            """
            print(f"Alarm callback for node {node_obj.name_base}: {val}")
            if val in ["True", True, 1]:
                log.warning(f"Received Alarm for node {node_obj.name_base}.")
                
                alarm_text = await self.client.get_node_id_val(node_obj.alarm_text_id)
                timestamp = await self.client.get_node_id_val(node_obj.timestamp_id)
                code = await self.client.get_node_id_val(node_obj.code_id)
                
                log.info(f"Alarm triggered: {alarm_text} at {timestamp} with code {code}.")
                
                await self.dda.publish_to_channel(
                    "significantEvent",
                    f"Alarm: {alarm_text} at {timestamp} with code {code}",
                )

        return alarm_sub_cb

    async def create_alarm_subs(self):
        """
        Create a subscription for the nodes.
        """
        print("Creating alarm subscriptions for nodes...")
        print(f"Alarm nodes: {self.alarm_objs}")
        for node_obj in self.alarm_objs:
            print(f"Creating subscription for {node_obj.name_base}...")
            sub_node_id = node_obj.active_id
            print(f"Subscription node ID: {sub_node_id}")
            alarm_sub_cb = await self.get_alarm_sub_cb(node_obj)
            print(f"Alarm subscription callback: {alarm_sub_cb}")
            await self.client.add_subscription(sub_node_id, alarm_sub_cb)
            print(f"Alarm subscriptions create for {sub_node_id}")
            logging.info(f"Alarm subscription created for {node_obj.name_base}.")
    
    async def get_polling_value(self, name: str):
        """
        Get the polling data for this injector.
        """
        node_id = f'ns=3;s="DB_OPCUA_AnalogValues"."{name}"'
        value = await self.client.get_node_id_val(node_id)
        return value
    
    
    async def main_loop(self):
        await self.update_ui()
        
            
    def fetch_ui(self):
        """
        Fetch the ui for this injector.
        This is a placeholder for any additional fetching logic.
        """
        
        self.levelTank1 = ui.NumericVariable(
            name="LevelTank1",
            display_name="Level Tank 1 (%)",
            precision=1,
        )
        
        self.levelTank2 = ui.NumericVariable(
            name="LevelTank2",
            display_name="Level Tank 2 (%)",
            precision=1,
        )
        
        self.pressure = ui.NumericVariable(
            name="Pressure",
            display_name="Pressure (bar)",
            precision=2,
        )
        
        self.shelterTemperature = ui.NumericVariable(
            name="ShelterTemperature",
            display_name="Shelter Temperature (°C)",
            precision=1,
        )
        
        self.temperaturePump1 = ui.NumericVariable(
            name="TemperaturePump1",
            display_name="Temperature Pump 1 (°C)",
            precision=1,
        )
        
        self.temperaturePump2 = ui.NumericVariable(
            name="TemperaturePump2",
            display_name="Temperature Pump 2 (°C)",
            precision=1,
        )
        
        return [
            self.levelTank1,
            self.levelTank2,
            self.pressure,
            self.shelterTemperature,
            self.temperaturePump1,
            self.temperaturePump2,
        ]
            
    async def update_ui(self):
        """
        Update the UI with the latest data.
        """
        self.levelTank1.update(
            await self.get_polling_value("LevelTank1")
        )
        self.levelTank2.update(
            await self.get_polling_value("LevelTank2")
        )
        self.pressure.update(
            await self.get_polling_value("Pressure")
        )
        self.shelterTemperature.update(
            await self.get_polling_value("ShelterTemperature")
        )
        self.temperaturePump1.update(
            await self.get_polling_value("TemperaturePump1")
        )
        self.temperaturePump2.update(
            await self.get_polling_value("TemperaturePump2")
        )
        