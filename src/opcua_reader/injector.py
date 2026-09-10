import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from pydoover import ui

from .doover_table import DooverTableManager
from .opcua_client import AsyncUAClient
from .utils import to_camel_case

log = logging.getLogger()


def table_channel_name(index: int) -> str:
    """Channel that holds the injector's batch table aggregate."""
    return f"injector-{index}-table"


def hmi_children_path(index: int) -> list[str]:
    """Path (below the app node) to the HMI remote component's children."""
    return [f"injector_{index}", f"injector_{index}_hmi"]


def build_injector_ui(index: int, display_name: str) -> ui.Submodule:
    """Build the UI submodule for one injector.

    The HMI and table widgets read literal ``currentValue``s from their
    children, so these variables are NOT tag-bound — the application patches
    their values straight into the ``ui_state`` aggregate each loop.
    """
    hmi_remote = ui.RemoteComponent(
        f"Injector {index} HMI",
        # Hosted as a file attachment on the agent channel of this name
        # (publish with `doover channel publish-file`). scope/module must be
        # pinned because the channel name does not match the widget's Module
        # Federation container name.
        component_url="fuel_additive_hmi",
        scope="HMIComponent",
        module="./HMIComponent",
        injector_index=index,
        name=f"injector_{index}_hmi",
        children=[
            ui.NumericVariable(
                f"Injector {index} L Inject", name=f"injector{index}LInject"
            ),
            ui.NumericVariable(
                f"Injector {index} Total Injected (L)", name=f"injector{index}LTotal"
            ),
            ui.NumericVariable(
                f"Injector {index} Total Injected Today (L)",
                name=f"injector{index}LDayTotal",
            ),
            ui.NumericVariable(
                f"Header {index} L Inject", name=f"header{index}LInterval"
            ),
            ui.NumericVariable(
                f"Header {index} Total Injected (L)", name=f"header{index}LTotal"
            ),
            ui.NumericVariable(
                f"Header {index} Total Today (L)", name=f"header{index}LDayTotal"
            ),
            ui.NumericVariable(
                f"Injector {index} Vol Per Injection",
                name=f"injector{index}VolPerInject",
            ),
            ui.NumericVariable(
                f"Injector {index} Injection Rate Interval",
                name=f"injector{index}InjectRateInterval",
            ),
        ],
    )

    table_remote = ui.RemoteComponent(
        f"Injector {index} Table",
        component_url="https://spaneng.github.io/doover_tables/DooverTables.js",
        channel_name=table_channel_name(index),
        table_name=to_camel_case(display_name),
        name=f"injector_{index}_table",
    )

    table_submodule = ui.Submodule(
        f"Injector {index} Batches",
        children=[table_remote],
        is_collapsed=False,
        position=100 + index,
        name=f"injector_{index}_table",
    )

    return ui.Submodule(
        f"Injector {index}",
        children=[hmi_remote, table_submodule],
        is_collapsed=True,
        name=f"injector_{index}",
    )


class Node:
    def __init__(self, name_base: str, idx: int):
        self.name_base = name_base
        self.idx = idx
        self.name = f"{name_base}{idx}"
        self.node_id = f'ns=3;s="DB_OPCUA_Report"."{self.name}"'


class Injector:
    REPORT_SUB_NODE = "BatchEndTime"
    REPORT_NODE_NAME_BASES = [
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
        "TotalRuntime",
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

    TABLE_HEADER_DISPLAY_NAMES = {
        "a": "Start Time",
        "b": "Dur. (H:M:S)",
        "c": "Actual Inject (L)",
        "d": "Calc'd Inject (L)",
        "e": "Diff. (%)",
        "f": "Header Volume (L)",
    }

    TABLE_HEADER_ORDER = [
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
    ]

    def __init__(
        self,
        index: int,
        display_name: str,
        opcua_client: AsyncUAClient,
        app,
        timezone: str = "Asia/Riyadh",
    ):
        self.index = index
        self.client = opcua_client
        self.app = app
        self.timezone = timezone
        self.polling_nodes = []
        self.report_nodes = []
        self.display_name = display_name
        self.name = to_camel_case(display_name)

        self.table_manager = DooverTableManager(
            dda=app.device_agent,
            channel_name=table_channel_name(self.index),
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
            node = Node(node_base, self.index)
            nodes.append(node)
        self.polling_nodes = nodes

    def set_report_nodes(self):
        nodes = []
        for node_base in self.REPORT_NODE_NAME_BASES:
            node = Node(node_base, self.index)
            nodes.append(node)
        self.report_nodes = nodes

    async def setup(self):
        log.info(f"Setting up injector {self.index}")

        # Setup Doover Table Manager
        await self.table_manager.setup()
        self.table_manager.add_table(
            name=self.name,
            display_name=self.display_name,
            header_display_names=self.TABLE_HEADER_DISPLAY_NAMES,
            header_order=self.TABLE_HEADER_ORDER,
        )

        # Setup OPC UA Nodes
        self.set_polling_nodes()
        self.set_report_nodes()
        node_ids = [node.node_id for node in self.polling_nodes + self.report_nodes]
        await self.client.register_nodes(node_ids)
        # await self.create_report_sub()

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
            log.info(f"******* Start string: {start_string}")
            try:
                dt_utc = datetime.fromisoformat(start_string.replace("Z", "+00:00"))
            except Exception as e:
                log.debug(f"Error parsing ISO format: {e}")
                # Parse format like "21-Oct-2025, 14:43:40"
                dt_naive = datetime.strptime(start_string, "%d-%b-%Y, %H:%M:%S")
                # Assume it's in UTC and convert to local timezone
                dt_utc = dt_naive.replace(tzinfo=ZoneInfo("UTC"))

            dt_local = dt_utc.astimezone(ZoneInfo(self.timezone))
            dt_local_str = dt_local.strftime("%I:%M:%S %p")
        except Exception as e:
            log.error(f"Error making table entry: {e}")
            return None

        gasoline_vol = data.get(f"CurrentIntervalFlowHeader{self.index}", None)
        vol_per_inject = data.get(f"SPT_RateIntervalInject{self.index}", None)
        inject_interval = data.get(f"SPT_VolumePerInject{self.index}", None)
        actual_injected = data.get(f"InjectionVolumeInjector{self.index}", None)
        if (
            gasoline_vol is None
            or vol_per_inject is None
            or inject_interval is None
            or actual_injected is None
        ):
            theoretical_injected = None
            actual_theoretical_ratio = None
        else:
            if vol_per_inject != 0:
                theoretical_injected = round(
                    gasoline_vol * inject_interval / vol_per_inject, 2
                )
            else:
                theoretical_injected = 0
            if theoretical_injected != 0:
                actual_theoretical_ratio = round(
                    (actual_injected / theoretical_injected) * 100, 1
                )
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
            "e": gasoline_vol,
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

    async def update_ui(self):
        """
        Queue the latest polling values for the HMI remote component.
        """
        polling_data = await self.get_polling_data()
        values = {}
        for node_name, val in polling_data.items():
            hmi_var_name = self._hmi_ui_val_map.get(node_name, None)
            if hmi_var_name is not None:
                values[hmi_var_name] = val
        self.app.queue_ui_values(hmi_children_path(self.index), values)
