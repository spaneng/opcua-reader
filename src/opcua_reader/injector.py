import logging

import asyncio

from .utils import to_camel_case
from pydoover.docker import DeviceAgentInterface
from pydoover import ui

from datetime import datetime
from zoneinfo import ZoneInfo

from .opcua_client import AsyncUAClient
from .doover_table import DooverTableManager

log = logging.getLogger()

class Node:
    def __init__(self, name_base: str, idx: int):
        self.name_base = name_base
        self.idx = idx
        self.name = f"{name_base}{idx}"
        self.node_id = f'ns=3;s="DB_OPCUA_Report"."{self.name}"'

class Injector:
    REPORT_SUB_NODE = "BatchStartTime"
    REPORT_NODE_NAME_BASES =[
        "BatchEndTime",
        "BatchStartTime",
        "CurrentIntervalFlowHeader",
        "InjectionType",
        "InjectionVolumeInjector",
        "NameInjector",
        "SPT_BatchPresetInject",
        "SPT_RateIntervalInject",
        "SPT_VolumePerInject",
        "TotalInjectedVolumeBatchInject",
        "TotalInjectedVolumeBatchTodayInject",
        "TotalInjectedVolumeInject",
        "TotalInjectedVolumeRatioInject",
        "TotalInjectedVolumeRatioTodayInject",
        "TotalMainFlowHeader",
        "TotalMainFlowTodayHeader",
        "TotalRuntime"
    ]
    
    POLLING_NODE_NAME_BASES = [
        "InjectionType",
        "NameInjector",
        "TotalInjectedVolumeInject",
        
        "SPT_BatchPresetInject",
        "TotalInjectedVolumeBatchInject",
        "TotalInjectedVolumeBatchTodayInject",
        
        "SPT_RateIntervalInject",
        "SPT_VolumePerInject",
        "InjectionVolumeInjector",
        "TotalInjectedVolumeRatioInject",
        "TotalInjectedVolumeRatioTodayInject",
        
        "CurrentIntervalFlowHeader",
        "TotalMainFlowHeader",
        "TotalMainFlowTodayHeader",
    ]

    # _polling_node_ui = [
    #     {"InjectionType":{"name": "Injection Type"}},
    #     {"NameInjector":{"name": "Injector Name"}},
    #     {"TotalInjectedVolumeInject":{"name": "Total Injected Volume"}},
    #     {"SPT_BatchPresetInject":{"name": "Batch Preset"}},
    #     {"TotalInjectedVolumeBatchInject":{"name": "Total Injected Volume Batch"}},
    #     {"TotalInjectedVolumeBatchTodayInject":{"name": "Total Injected Volume Batch Today"}},

    #     {"SPT_RateIntervalInject":{"name": "Rate Interval"}},
    #     {"SPT_VolumePerInject":{"name": "Volume Per Inject"}},
    #     {"InjectionVolumeInjector":{"name": "Injection Volume Injector"}},
    #     {"TotalInjectedVolumeRatioInject":{"name": "Total Injected Volume Ratio"}},
    #     {"TotalInjectedVolumeRatioTodayInject":{"name": "Total Injected Volume Ratio Today"}},
    #     {"CurrentIntervalFlowHeader":{"name": "Current Interval Flow"}},
    #     {"TotalMainFlowHeader":{"name": "Total Main Flow"}},
    #     {"TotalMainFlowTodayHeader":{"name": "Total Main Flow Today"}},
    # ]
    
        # "Batch_Start_Time": "Start Time",
        # "Duration": "Duration",
        # "Actual_Injected": "Actual Inject Amount",
        # "Theoretical_Injected": "Imputed Value",
        # "Actual_Theoretical_Ratio": "Actual vs Theoretical Ratio",
        # "Header_Volume": "Header Volume"
    
    TABLE_HEADER_DISPLAY_NAMES = {
        "a": "Start Time", # 
        "b": "Duration", # 
        "c": "Actual Inject (L)", #
        "d": "Calc'd Inject (L)", #
        "e": "Difference (%)", #
        "f": "Header Volume (L)" #
    }
    
    TABLE_HEADER_ORDER = [
        "a",
        "b",
        "c",
        "d",
        "e",
        "f"
    ]
    
    def __init__(
        self, 
        index: int,
        display_name: str,
        opcua_client: AsyncUAClient,
        dda: DeviceAgentInterface,
        ui_manager: ui.UIManager,
        timezone: str = "Asia/Riyadh",
    ):
        self.index = index
        self.client = opcua_client
        self.dda = dda
        self.ui_manager = ui_manager
        self.timezone = timezone
        self.polling_nodes = []
        self.report_nodes = []
        self.display_name = display_name
        self.name = to_camel_case(display_name)
        
        self.table_manager = DooverTableManager(
            dda=self.dda, 
            channel_name=f"injector-{self.index}-table"
        )
        
        self._hmi_ui_val_map = {            
            f"InjectionVolumeInjector{self.index}": f"injector{self.index}LInject",
            f"TotalInjectedVolumeRatioInject{self.index}": f"injector{self.index}LTotal",
            f"TotalInjectedVolumeRatioTodayInject{self.index}": f"injector{self.index}LDayTotal",
            
            f"CurrentIntervalFlowHeader{self.index}": f"header{self.index}LInterval",
            f"TotalMainFlowHeader{self.index}": f"header{self.index}LTotal",
            f"TotalMainFlowTodayHeader{self.index}": f"header{self.index}LDayTotal",
            
            f"SPT_RateIntervalInject{self.index}": f"injector{self.index}InjectRateInterval",
            f"SPT_VolumePerInject{self.index}": f"injector{self.index}VolPerInject",
        }
    
    def set_polling_nodes(self):
        nodes = []
        for node_base in self.POLLING_NODE_NAME_BASES:
            node = Node(node_base,self.index)
            nodes.append(node)
        self.polling_nodes = nodes
    
    def set_report_nodes(self):
        nodes = []
        for node_base in self.REPORT_NODE_NAME_BASES:
            node = Node(node_base,self.index)
            nodes.append(node)
        self.report_nodes = nodes
        
    async def setup(self):
        logging.info(f"Setting up injector {self.index}")
        
        # Setup Doover Table Manager
        await self.table_manager.setup()
        self.table_manager.add_table(
            name=self.name,
            display_name=self.display_name,
            header_display_names=self.TABLE_HEADER_DISPLAY_NAMES,
            header_order=self.TABLE_HEADER_ORDER
        )
        
        # Setup OPC UA Nodes
        self.set_polling_nodes()
        self.set_report_nodes()
        node_ids = [node.node_id for node in self.polling_nodes + self.report_nodes]
        await self.client.register_nodes(node_ids)
        await self.create_report_sub()
        
    async def add_data_entry(self, data: dict):
        await self.table_manager.add_data_entry(self.name, data)
        
    async def get_table_entry_data(self):
        report_data = {}
        for node in self.report_nodes:
            value = await self.client.get_node_id_val(node.node_id)
            report_data[node.name] = value
        return report_data
    
    async def make_table_entry(self):
        data = await self.get_table_entry_data()
        try:
            start_string = data.get(f"BatchStartTime{self.index}", None)
            logging.info(f"******* Start string: {start_string}")
            dt_utc = datetime.fromisoformat(start_string.replace("Z", "+00:00"))
            dt_local = dt_utc.astimezone(ZoneInfo(self.timezone))
            dt_local_str = dt_local.strftime("%I:%M:%S %p")
        except Exception as e:
            log.error(f"Error making table entry: {e}")
            return None
        
        gasoline_vol = data.get(f"CurrentIntervalFlowHeader{self.index}", None)
        vol_per_inject = data.get(f"SPT_RateIntervalInject{self.index}", None)
        inject_interval = data.get(f"SPT_VolumePerInject{self.index}", None)
        actual_injected = data.get(f"InjectionVolumeInjector{self.index}", None)
        if gasoline_vol is None or vol_per_inject is None or inject_interval is None or actual_injected is None:
            theoretical_injected = None
            actual_theoretical_ratio = None
        else:
            if vol_per_inject != 0:
                theoretical_injected = round(gasoline_vol * inject_interval / vol_per_inject, 2)
            else:
                theoretical_injected = 0
            if theoretical_injected != 0:
                actual_theoretical_ratio = round((actual_injected / theoretical_injected)*100, 1)
            else:
                actual_theoretical_ratio = 0
            gasoline_vol = round(gasoline_vol, 2)
            actual_injected = round(actual_injected, 2)
        
        runtime = data.get(f"TotalRuntime{self.index}", None)
        if runtime is not None:
            runtime = self.format_seconds_to_hms(runtime)
        return {
            "a": dt_local_str,
            "b": runtime,
            "c": actual_injected,
            "d": theoretical_injected,
            "f": actual_theoretical_ratio,
            "e": gasoline_vol
        }
        
    def format_seconds_to_hms(self, seconds: float) -> str:
        """Convert seconds (float) into 'Hr:Min:Sec' string."""
        total_seconds = int(seconds)  # drop fractional part
        hrs = total_seconds // 3600
        mins = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    
    async def report_sub_cb(self, node, val):
        """
        Callback for the report subscription.
        This will be called after each batch from either batch mode
        or ratio mode is complete.
        """
        new_data = await self.make_table_entry()
        await self.add_data_entry(new_data)
        
    async def create_report_sub(self):
        """
        Create a subscription for the nodes.
        """
        sub_node_id = f'ns=3;s="DB_OPCUA_Report"."{self.REPORT_SUB_NODE}{self.index}"'
        await self.client.add_subscription(sub_node_id, self.report_sub_cb)
    
    async def get_polling_data(self):
        """
        Get the polling data for this injector.
        """
        polling_data = {}
        for node in self.polling_nodes:
            value = await self.client.get_node_id_val(node.node_id)
            polling_data[node.name] = value
        return polling_data
    
    async def main_loop(self):
        await self.update_ui()
        
    async def create_ui(self):
        """
        Get the UI for this injector.
        """
        polling_data = await self.get_polling_data()
        for node_name,val in polling_data.items():
            match val:
                case bool():
                    ui_var = ui.BooleanVariable(f"{self.index}_{node_name}", node_name)
                case int() | float():
                    ui_var = ui.NumericVariable(
                        f"{self.index}_{node_name}",
                        node_name,
                        precision=2 if isinstance(val, float) else 0
                    )
                case str():
                    ui_var = ui.TextVariable(f"{self.index}_{node_name}", node_name)
                case _:
                    log.warning(f"Unsupported data type for node_name {node_name}: {type(val)}")
                    continue
            logging.debug(f"Creating UI variable for {node_name}: {type(ui_var)}")
            setattr(self, f"{node_name}", ui_var)
            
    async def fetch_ui(self):
        await self.create_ui()
        """
        Fetch the ui for this injector.
        This is a placeholder for any additional fetching logic.
        """
        ui_vars = []
        # for node in self.polling_nodes:
        #     elem = getattr(self, f"{node.name}", None)
        #     if elem is not None:
        #         ui_vars.append(elem)
                
        hmi_remote = ui.RemoteComponent(
        # hmi_remote = ui.Submodule(
            f"injector_{self.index}_hmi",
            f"Injector {self.index} HMI",
            component_url="https://spaneng.github.io/fuel-additive-hmi/HMIComponent.js",
            injector_index=self.index,
            children=[
                ui.NumericVariable(f"injector{self.index}LInject", f"Injector {self.index} L Inject"),
                ui.NumericVariable(f"injector{self.index}LTotal", f"Injector {self.index} Total Injected (L)"),
                ui.NumericVariable(f"injector{self.index}LDayTotal", f"Injector {self.index} Total Injected Today (L)"),
                
                ui.NumericVariable(f"header{self.index}LInterval", f"Header {self.index} L Inject"),
                ui.NumericVariable(f"header{self.index}LTotal", f"Header {self.index} Total Injected (L)"),
                ui.NumericVariable(f"header{self.index}LDayTotal", f"Header {self.index} Total Today (L)"),
                
                ui.NumericVariable(f"injector{self.index}VolPerInject", f"Injector {self.index} Vol Per Injection"),
                ui.NumericVariable(f"injector{self.index}InjectRateInterval", f"Injector {self.index} Injection Rate Interval"),
            ]
        )
        
        table_remote = ui.RemoteComponent(
            f"injector_{self.index}_table",
            f"Injector {self.index} Table",
            component_url="https://spaneng.github.io/doover_tables/DooverTables.js",
            channel_name=self.table_manager.channel_name,
            table_name=self.name
        )
        
        table_submodule = ui.Submodule(
            f"injector_{self.index}_table",
            f"Injector {self.index} Batches",
            [table_remote],
            is_collapsed=False,
            position=100+self.index
        )
        
        ui_vars.append(hmi_remote)
        ui_vars.append(table_submodule)
        
        self.ui_submodule = ui.Submodule(
            f"injector_{self.index}",
            f"Injector {self.index}",
            ui_vars,
            is_collapsed=True
        )
        return self.ui_submodule
            
    async def update_ui(self):
        """
        Update the UI with the latest data.
        """
        polling_data = await self.get_polling_data()
        for node_name,val in polling_data.items():
            # ui_var = getattr(self, f"{node_name}", None)
            hmi_var_name = self._hmi_ui_val_map.get(node_name, None)
            if hmi_var_name is not None:
                hmi_var = self.ui_manager.get_element(hmi_var_name)
                if hmi_var is not None:
                    hmi_var.update(val)
                else:
                    log.warning(f"HMI variable {hmi_var_name} not found for injector {self.index}.")
            
            # if ui_var is not None:
            #     ui_var.update(val)
            # else:
            #     log.warning(f"UI variable {node_name} not found for injector {self.index}.")
        # if hasattr(self, 'ui'):
        #     self.ui.update(polling_data)
        # else:
        #     log.warning("UI not set up yet, cannot update.")