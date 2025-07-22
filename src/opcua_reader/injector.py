import logging

import asyncio

from pydoover.docker import DeviceAgentInterface
from pydoover import ui

from .opcua_client import AsyncUAClient

log = logging.getLogger()

class Node:
    def __init__(self, name_base: str, idx: int):
        self.name_base = name_base
        self.idx = idx
        self.name = f"{name_base}{idx}"
        self.node_id = f'ns=3;s="DB_OPCUA_Report"."{self.name}"'

class Injector:
    _report_sub_node = "BatchStartTime"
    _reports_node_name_bases =[
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
    
    _polling_node_name_bases = [
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

    _polling_node_ui = [
        {"InjectionType":{"name": "Injection Type"}},
        {"NameInjector":{"name": "Injector Name"}},
        {"TotalInjectedVolumeInject":{"name": "Total Injected Volume"}},
        {"SPT_BatchPresetInject":{"name": "Batch Preset"}},
        {"TotalInjectedVolumeBatchInject":{"name": "Total Injected Volume Batch"}},
        {"TotalInjectedVolumeBatchTodayInject":{"name": "Total Injected Volume Batch Today"}},

        {"SPT_RateIntervalInject":{"name": "Rate Interval"}},
        {"SPT_VolumePerInject":{"name": "Volume Per Inject"}},
        {"InjectionVolumeInjector":{"name": "Injection Volume Injector"}},
        {"TotalInjectedVolumeRatioInject":{"name": "Total Injected Volume Ratio"}},
        {"TotalInjectedVolumeRatioTodayInject":{"name": "Total Injected Volume Ratio Today"}},
        {"CurrentIntervalFlowHeader":{"name": "Current Interval Flow"}},
        {"TotalMainFlowHeader":{"name": "Total Main Flow"}},
        {"TotalMainFlowTodayHeader":{"name": "Total Main Flow Today"}},
    ]
    
    def __init__(
        self, 
        index: int,
        opcua_client: AsyncUAClient,
        dda: DeviceAgentInterface,
    ):
        self.index = index
        self.client = opcua_client
        self.dda = dda
        self.polling_nodes = []
        self.report_nodes = []
    
    def set_polling_nodes(self):
        nodes = []
        for node_base in self._polling_node_name_bases:
            node = Node(node_base,self.index)
            nodes.append(node)
        self.polling_nodes = nodes
    
    def set_report_nodes(self):
        nodes = []
        for node_base in self._reports_node_name_bases:
            node = Node(node_base,self.index)
            nodes.append(node)
        self.report_nodes = nodes
        
    async def setup(self):
        self.set_polling_nodes()
        self.set_report_nodes()
        node_ids = [node.node_id for node in self.polling_nodes + self.report_nodes]
        await self.client.register_nodes(node_ids)
        await self.create_report_sub()
        
    async def get_report_data_entry(self):
        """
        Get the report data for this injector.
        """
        report_data = {}
        for node in self.report_nodes:
            value = await self.client.get_node_id_val(node.node_id)
            report_data[node.name] = value
        return report_data
    
    async def report_sub_cb(self, node, val):
        """
        Callback for the report subscription.
        This will be called after each batch from either batch mode
        or ratio mode is complete.
        """
        log.info(f"Report data changed for node {node}: {val}")
        print("getting new data for report")
        new_data = await self.get_report_data_entry()
        print("got new data, getting old report data")
        report_data = await self.dda.get_channel_aggregate(f"Injector{self.index}_reportData")
        print("report data:", report_data)

        current_report=report_data.get('0', {})
        print("current report:", current_report)
        no_entries = len(current_report.keys())
        print(f"Number of entries in current report: {no_entries}")
        
        current_report[no_entries] = new_data
        print("Updated current report with new data.")
        report_data[0] = current_report
        print("Publishing updated report data to channel.")

        print("Updated report data:", report_data)
        
        await self.dda.publish_to_channel(f"Injector{self.index}_reportData", report_data, record_log=True)
        log.info(f"Report data for injector {self.index} updated: {new_data}")
        
    async def create_report_sub(self):
        """
        Create a subscription for the nodes.
        """
        sub_node_id = f'ns=3;s="DB_OPCUA_Report"."{self._report_sub_node}{self.index}"'
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
            print(f"Creating UI variable for {node_name}: {type(ui_var)}")
            setattr(self, f"{node_name}", ui_var)
            
    async def fetch_ui(self):
        await self.create_ui()
        """
        Fetch the ui for this injector.
        This is a placeholder for any additional fetching logic.
        """
        ui_vars = []
        for node in self.polling_nodes:
            elem = getattr(self, f"{node.name}", None)
            if elem is not None:
                ui_vars.append(elem)
        
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
            ui_var = getattr(self, f"{node_name}", None)
            if ui_var is not None:
                ui_var.update(val)
            else:
                log.warning(f"UI variable {node_name} not found for injector {self.index}.")
        # if hasattr(self, 'ui'):
        #     self.ui.update(polling_data)
        # else:
        #     log.warning("UI not set up yet, cannot update.")