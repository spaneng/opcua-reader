import logging

import asyncio

from pydoover.docker import DeviceAgentInterface
from pydoover import ui

from .opcua_client import AsyncUAClient

log = logging.getLogger()

class AlarmObj: #can be either a warning or an alarm
    def __init__(self, name_base: str, obj_name: str = "Warnings"):
        self.name_base = name_base
        
        self.obj_name = obj_name
        self.heading = obj_name[:-1] if obj_name.endswith(('s', 'S')) else obj_name
        server_obj_name = obj_name
        if obj_name == "Alarms":
            server_obj_name = "Alams"
        self.active_id = f'ns=3;s="DB_OPCUA_{server_obj_name}"."{self.obj_name}"[{self.name_base}]."Active"'
        self.timestamp_id = f'ns=3;s="DB_OPCUA_{server_obj_name}"."{self.obj_name}"[{self.name_base}]."Timestamp"'
        self.alarm_text_id = f'ns=3;s="DB_OPCUA_{server_obj_name}"."{self.obj_name}"[{self.name_base}]."AlarmText"'
        self.code_id = f'ns=3;s="DB_OPCUA_{server_obj_name}"."{self.obj_name}"[{self.name_base}]."Code"'
        
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
    
    # Alarms list found at: 
    # - opcua-reader/src/opcua_reader/Alarms Configuration PLC(DiscreteAlarms).csv
    
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
        52,
        53,
        54,
        55,
        56,
        57,
        60,
        61,
        65,
        66,
        67,
        68,
        69,
        70,
        71,
        72,
        73,
        74,
        75,
        76,
        77,
        78
    ]
    _warning_node_name_bases = [
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
        23,
        24,
        29,
        30,
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
        ui_manager: ui.UIManager,
        injectors: list,
        timezone: str = "Asia/Riyadh",
        skid_name: str = "Skid 1"
    ):
        self.client = opcua_client
        self.dda = dda
        self.ui_manager = ui_manager
        self.injectors = injectors
        self.polling_nodes = []
        self.alarm_objs = []
        self.timezone = timezone
        self.skid_name = skid_name
        
        self.polling_node_values = {}
        
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
            node = AlarmObj(node_base,  obj_name="Alarms")
            nodes.append(node)
        for node_base in self._warning_node_name_bases:
            node = AlarmObj(node_base,  obj_name="Warnings")
            nodes.append(node)
        
        for node in nodes:
            print(f"node.name_base: {node.name_base}")
            print(f"node.active_id: {node.active_id}")
            print(f"node.timestamp_id: {node.timestamp_id}")
            print(f"node.alarm_text_id: {node.alarm_text_id}")
            print(f"node.code_id: {node.code_id}")
        # print("-------- Alarm Objs --------")
        # print(f"{nodes}")
        
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
            if val in ["True", True, 1]:
                alarm_type = node_obj.heading
                log.warning(f"Received {alarm_type} for node {node_obj.name_base}.")
                
                alarm_text = await self.client.get_node_id_val(node_obj.alarm_text_id)
                timestamp = await self.client.get_node_id_val(node_obj.timestamp_id)
                code = await self.client.get_node_id_val(node_obj.code_id)
                
                log.info(f"{alarm_type} triggered: {alarm_text} at {timestamp} with code {code}.")
                print(f"{alarm_type} triggered: {alarm_text} at {timestamp} with code {code}.")
                
                await self.dda.publish_to_channel(
                    "significantEvent",
                    f"{alarm_type}: {alarm_text} at {timestamp} with code {code}",
                )

        return alarm_sub_cb

    async def create_alarm_subs(self):
        """
        Create a shared subscription for all alarm nodes.
        Using a single subscription with optimized parameters helps prevent
        "Subscription state changed (Late)" errors on the PLC.
        """
        print("Creating shared alarm subscription for nodes...")
        print(f"Alarm nodes: {self.alarm_objs}")
        
        # Build dictionary of node_id -> callback for shared subscription
        node_callbacks = {}
        for node_obj in self.alarm_objs:
            sub_node_id = node_obj.active_id
            print(f"Preparing subscription for {node_obj.name_base}...")
            print(f"Subscription node ID: {sub_node_id}")
            alarm_sub_cb = await self.get_alarm_sub_cb(node_obj)
            node_callbacks[sub_node_id] = alarm_sub_cb
            print(f"Alarm subscription callback prepared for {sub_node_id}")
        
        # Create a single shared subscription with optimized parameters
        # Publishing interval: 1000ms (1 second) - gives server time to process
        # Lifetime count: 20000 - allows subscription to survive longer periods
        # Max keep-alive: 10000 - ensures connection stays alive
        try:
            await self.client.create_shared_subscription(
                node_callbacks,
                publishing_interval=1000,  # 1 second publishing interval
                lifetime_count=20000,     # Higher lifetime count
                max_keep_alive_count=10000  # Higher keep-alive count
            )
            print(f"Shared alarm subscription created for {len(node_callbacks)} nodes")
            logging.info(f"Shared alarm subscription created for {len(self.alarm_objs)} alarm nodes.")
        except Exception as e:
            log.error(f"Error creating shared alarm subscription: {e}")
            raise
    
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
            position=1
        )
        
        self.levelTank2 = ui.NumericVariable(
            name="LevelTank2",
            display_name="Level Tank 2 (%)",
            precision=1,
            position=2
        )
        
        self.pressure = ui.NumericVariable(
            name="Pressure",
            display_name="Pressure (bar)",
            precision=2,
            position=3
        )
        
        self.shelterTemperature = ui.NumericVariable(
            name="ShelterTemperature",
            display_name="Shelter Temperature (°C)",
            precision=1,
            position=4
        )
        
        self.temperaturePump1 = ui.NumericVariable(
            name="TemperaturePump1",
            display_name="Temperature Pump 1 (°C)",
            precision=1,
            position=5
        )
        
        self.temperaturePump2 = ui.NumericVariable(
            name="TemperaturePump2",
            display_name="Temperature Pump 2 (°C)",
            precision=1,
            position=6
        )
        
        children = self.get_reconciliation_ui()
        children.extend([
            ui.NumericVariable(
                name="GasTotal",
                display_name="Gas Total (L)",
            ),
            ui.NumericVariable(
                name="CalcedInjectedTotal",
                display_name="Gas Total (L)",
            ),
            ui.NumericVariable(
                name="ActualInjectedTotal",
                display_name="Injected Total (L)",
            ),
            ui.NumericVariable(
                name="Difference",
                display_name="Difference (%)",
            ),
        ])
        
        self.reconciliation = ui.RemoteComponent(
            name="Reconciliation",
            display_name="Reconciliation",
            component_url="https://spaneng.github.io/fuel-additive-reconciliation/ReconciliationComponent.js",
            children=children,
            timezone=self.timezone,
            skid_name=self.skid_name,
            position=7,
            injectors=[
                {
                    "name": injector.name,
                    "displayName": injector.display_name,
                    "index": injector.index
                }
                for injector in self.injectors
            ]
        )
        
        return [
            self.levelTank1,
            self.levelTank2,
            self.pressure,
            self.shelterTemperature,
            self.temperaturePump1,
            self.temperaturePump2,
            self.reconciliation,
        ]

    def get_reconciliation_ui(self):
        children = []
        for injector in self.injectors:
            _children = [
                ui.NumericVariable(
                    f"{injector.name}_LDayTotal", 
                    f"Injector {injector.index} Total Injected Today (L)"
                ),
                ui.NumericVariable(
                    f"{injector.name}_header_LDayTotal", 
                    f"Header {injector.index} Total Flow Today (L)"
                ),
                ui.NumericVariable(
                    f"{injector.name}CalcedLTotal", 
                    f"Injector {injector.index} Calced Total (L)"
                ),
                ui.NumericVariable(
                    f"{injector.name}Difference",
                    f"Injector {injector.index} Difference (%)"
                )
            ]
            children.extend(_children)
        return children
    
    async def update_reconciliation_ui(self):
        gas_total = 0
        calced_injected_total = 0
        actual_injected_total = 0
        
        
        for injector in self.injectors:
            polling_data = await injector.get_polling_data()
            LInjectedDayTotal = polling_data[f"TotalInjectedVolumeRatioTodayInject{injector.index}"]
            LFlowDayTotal = polling_data[f"TotalMainFlowTodayHeader{injector.index}"]
            VolPerInject = polling_data[f"SPT_VolumePerInject{injector.index}"] #
            InjectRateInterval = polling_data[f"SPT_RateIntervalInject{injector.index}"] #
            
            if InjectRateInterval != 0:
                CalcedLTotal = (LFlowDayTotal /InjectRateInterval)* VolPerInject
            else:
                CalcedLTotal = 0
            
            if LInjectedDayTotal != 0:
                Difference = (1-(CalcedLTotal / LInjectedDayTotal))*100
            else:
                Difference = 0
            
            gas_total += LFlowDayTotal
            calced_injected_total += CalcedLTotal
            actual_injected_total += LInjectedDayTotal
            
            injector_day_total = f"{injector.name}_LDayTotal"
            header_day_total = f"{injector.name}_header_LDayTotal"
            inj_calced_total = f"{injector.name}CalcedLTotal"
            inj_difference = f"{injector.name}Difference"
            
            linjected_day_total = round(LInjectedDayTotal, 2)
            lflow_day_total = round(LFlowDayTotal, 2)
            # print(f"updating injector {injector.index}")
            # print(f"linjected_day_total: {linjected_day_total}")
            # print(f"lflow_day_total: {lflow_day_total}")
            # print(f"calced_l_total: {CalcedLTotal}")
            # print(f"difference: {Difference}")
            # print("--------------------------------")
            
            self.ui_manager.get_element(injector_day_total).update(linjected_day_total)
            self.ui_manager.get_element(header_day_total).update(lflow_day_total)
            self.ui_manager.get_element(inj_calced_total).update(round(CalcedLTotal, 2))
            self.ui_manager.get_element(inj_difference).update(round(Difference, 2))
            
        if actual_injected_total != 0:
            difference = round((1-(calced_injected_total / actual_injected_total))*100, 2)
        else:
            difference = 0
            
        self.ui_manager.get_element("GasTotal").update(round(gas_total, 2))
        self.ui_manager.get_element("CalcedInjectedTotal").update(round(calced_injected_total, 2))
        self.ui_manager.get_element("ActualInjectedTotal").update(round(actual_injected_total, 2))
        self.ui_manager.get_element("Difference").update(difference)
            
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
        
        await self.update_reconciliation_ui()
        