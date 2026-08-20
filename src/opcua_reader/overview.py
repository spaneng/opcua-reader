import logging

from pydoover import ui

from .opcua_client import AsyncUAClient
from .utils import to_camel_case

log = logging.getLogger()

# Path (below the app node) to the Reconciliation remote component.
RECONCILIATION_PATH = ["Reconciliation"]

NOTIFICATION_SEVERITY_WARN = "Warn"


def build_overview_ui(
    injector_specs: list[tuple[int, str]], timezone: str
) -> list[ui.Element]:
    """Build the overview UI elements.

    ``injector_specs`` is a list of (index, display_name) tuples from config.

    The plain analog variables are tag-bound (the application sets a tag per
    value). The Reconciliation widget reads literal ``currentValue``s from its
    children, so those are NOT tag-bound — the application patches their
    values into the ``ui_state`` aggregate each loop.
    """
    elements = [
        ui.NumericVariable(
            "Level Tank 1 (%)",
            value=ui.tag_ref("LevelTank1", "number"),
            precision=1,
            position=1,
            name="LevelTank1",
        ),
        ui.NumericVariable(
            "Level Tank 2 (%)",
            value=ui.tag_ref("LevelTank2", "number"),
            precision=1,
            position=2,
            name="LevelTank2",
        ),
        ui.NumericVariable(
            "Pressure (bar)",
            value=ui.tag_ref("Pressure", "number"),
            precision=2,
            position=3,
            name="Pressure",
        ),
        ui.NumericVariable(
            "Shelter Temperature (°C)",
            value=ui.tag_ref("ShelterTemperature", "number"),
            precision=1,
            position=4,
            name="ShelterTemperature",
        ),
        ui.NumericVariable(
            "Temperature Pump 1 (°C)",
            value=ui.tag_ref("TemperaturePump1", "number"),
            precision=1,
            position=5,
            name="TemperaturePump1",
        ),
        ui.NumericVariable(
            "Temperature Pump 2 (°C)",
            value=ui.tag_ref("TemperaturePump2", "number"),
            precision=1,
            position=6,
            name="TemperaturePump2",
        ),
    ]

    children = _build_reconciliation_children(injector_specs)
    children.extend(
        [
            ui.NumericVariable("Gas Total (L)", name="GasTotal"),
            ui.NumericVariable("Gas Total (L)", name="CalcedInjectedTotal"),
            ui.NumericVariable("Injected Total (L)", name="ActualInjectedTotal"),
            ui.NumericVariable("Difference (%)", name="Difference"),
        ]
    )

    reconciliation = ui.RemoteComponent(
        "Reconciliation",
        # Hosted as a file attachment on the agent channel of this name
        # (publish with `doover channel publish-file`). scope/module must be
        # pinned because the channel name does not match the widget's Module
        # Federation container name.
        component_url="fuel_additive_reconciliation",
        scope="ReconciliationComponent",
        module="./ReconciliationComponent",
        children=children,
        timezone=timezone,
        # Resolved from the deployment config when the runtime schema is
        # published, so the widget shows the install's display name.
        skid_name="$config.app().APP_DISPLAY_NAME",
        position=7,
        injectors=reconciliation_injectors_meta(injector_specs),
        name="Reconciliation",
    )
    elements.append(reconciliation)
    return elements


def reconciliation_injectors_meta(
    injector_specs: list[tuple[int, str]],
) -> list[dict]:
    """The `injectors` prop the Reconciliation widget (and report) expects."""
    return [
        {
            "name": to_camel_case(display_name),
            "displayName": display_name,
            "index": index,
        }
        for index, display_name in injector_specs
    ]


def _build_reconciliation_children(
    injector_specs: list[tuple[int, str]],
) -> list[ui.Element]:
    children = []
    for index, display_name in injector_specs:
        name = to_camel_case(display_name)
        children.extend(
            [
                ui.NumericVariable(
                    f"Injector {index} Total Injected Today (L)",
                    name=f"{name}_LDayTotal",
                ),
                ui.NumericVariable(
                    f"Header {index} Total Flow Today (L)",
                    name=f"{name}_header_LDayTotal",
                ),
                ui.NumericVariable(
                    f"Injector {index} Calced Total (L)",
                    name=f"{name}CalcedLTotal",
                ),
                ui.NumericVariable(
                    f"Injector {index} Difference (%)",
                    name=f"{name}Difference",
                ),
            ]
        )
    return children


class AlarmObj:  # can be either a warning or an alarm
    def __init__(self, name_base: str, obj_name: str = "Warnings"):
        self.name_base = name_base

        self.obj_name = obj_name
        self.heading = obj_name[:-1] if obj_name.endswith(("s", "S")) else obj_name
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
            self.code_id,
        ]


class PollingNode:
    def __init__(self, name_base: str):
        self.name_base = name_base
        self.name = f"{name_base}"
        self.node_id = f'ns=3;s="DB_OPCUA_AnalogValues"."{self.name_base}"'


class Overview:
    # Alarms list found at:
    # - opcua-reader/src/opcua_reader/Alarms Configuration PLC(DiscreteAlarms).csv

    _alarm_sub_node_name_bases = [
        1, 3, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
        31, 32, 33, 34, 35, 37, 38, 45, 50, 51, 52, 53, 54, 55, 56,
        57, 60, 61, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76,
        77, 78,
    ]  # fmt: skip
    _warning_node_name_bases = [
        11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 29, 30,
    ]  # fmt: skip

    _polling_node_name_bases = [
        "LevelTank1",
        "LevelTank2",
        "Pressure",
        "ShelterTemperature",
        "TemperaturePump1",
        "TemperaturePump2",
    ]

    def __init__(
        self,
        opcua_client: AsyncUAClient,
        app,
        injectors: list,
        timezone: str = "Asia/Riyadh",
    ):
        self.client = opcua_client
        self.app = app
        self.injectors = injectors
        self.polling_nodes = []
        self.alarm_objs = []
        self.timezone = timezone

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
            node = AlarmObj(node_base, obj_name="Alarms")
            nodes.append(node)
        for node_base in self._warning_node_name_bases:
            node = AlarmObj(node_base, obj_name="Warnings")
            nodes.append(node)

        for node in nodes:
            log.debug(
                f"Alarm obj {node.name_base}: active={node.active_id} "
                f"timestamp={node.timestamp_id} text={node.alarm_text_id} code={node.code_id}"
            )

        self.alarm_objs = nodes

    async def setup(self):
        self.set_polling_nodes()
        self.set_alarm_objs()
        node_ids = [
            node_id
            for node_id in self.get_polling_node_ids() + self.get_alarm_node_ids()
        ]

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

                log.info(
                    f"{alarm_type} triggered: {alarm_text} at {timestamp} with code {code}."
                )

                await self.app.create_message(
                    "notifications",
                    {
                        "message": f"{alarm_type}: {alarm_text} at {timestamp} with code {code}",
                        "severity": NOTIFICATION_SEVERITY_WARN,
                    },
                )

        return alarm_sub_cb

    async def create_alarm_subs(self):
        """
        Create a shared subscription for all alarm nodes.
        Using a single subscription with optimized parameters helps prevent
        "Subscription state changed (Late)" errors on the PLC.
        """
        log.info(
            f"Creating shared alarm subscription for {len(self.alarm_objs)} nodes..."
        )

        # Build dictionary of node_id -> callback for shared subscription
        node_callbacks = {}
        for node_obj in self.alarm_objs:
            sub_node_id = node_obj.active_id
            alarm_sub_cb = await self.get_alarm_sub_cb(node_obj)
            node_callbacks[sub_node_id] = alarm_sub_cb
            log.debug(f"Alarm subscription callback prepared for {sub_node_id}")

        # Create a single shared subscription with optimized parameters
        # Publishing interval: 1000ms (1 second) - gives server time to process
        # Lifetime count: 20000 - allows subscription to survive longer periods
        # Max keep-alive: 10000 - ensures connection stays alive
        try:
            await self.client.create_shared_subscription(
                node_callbacks,
                publishing_interval=1000,
                lifetime_count=20000,
                max_keep_alive_count=10000,
            )
            log.info(
                f"Shared alarm subscription created for {len(self.alarm_objs)} alarm nodes."
            )
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

    async def update_reconciliation_ui(self):
        gas_total = 0
        calced_injected_total = 0
        actual_injected_total = 0

        values = {}
        for injector in self.injectors:
            polling_data = await injector.get_polling_data()
            LInjectedDayTotal = polling_data[
                f"TotalInjectedVolumeRatioTodayInject{injector.index}"
            ]
            LFlowDayTotal = polling_data[f"TotalMainFlowTodayHeader{injector.index}"]
            VolPerInject = polling_data[f"SPT_VolumePerInject{injector.index}"]
            InjectRateInterval = polling_data[f"SPT_RateIntervalInject{injector.index}"]

            if None in (
                LInjectedDayTotal,
                LFlowDayTotal,
                VolPerInject,
                InjectRateInterval,
            ):
                log.warning(
                    f"Missing reconciliation data for injector {injector.index}. Skipping."
                )
                continue

            if InjectRateInterval != 0:
                CalcedLTotal = (LFlowDayTotal / InjectRateInterval) * VolPerInject
            else:
                CalcedLTotal = 0

            if LInjectedDayTotal != 0:
                Difference = (1 - (CalcedLTotal / LInjectedDayTotal)) * 100
            else:
                Difference = 0

            gas_total += LFlowDayTotal
            calced_injected_total += CalcedLTotal
            actual_injected_total += LInjectedDayTotal

            values[f"{injector.name}_LDayTotal"] = round(LInjectedDayTotal, 2)
            values[f"{injector.name}_header_LDayTotal"] = round(LFlowDayTotal, 2)
            values[f"{injector.name}CalcedLTotal"] = round(CalcedLTotal, 2)
            values[f"{injector.name}Difference"] = round(Difference, 2)

        if actual_injected_total != 0:
            difference = round(
                (1 - (calced_injected_total / actual_injected_total)) * 100, 2
            )
        else:
            difference = 0

        values["GasTotal"] = round(gas_total, 2)
        values["CalcedInjectedTotal"] = round(calced_injected_total, 2)
        values["ActualInjectedTotal"] = round(actual_injected_total, 2)
        values["Difference"] = difference

        # The report generator reads these from ui_state message history, and
        # needs the `injectors` prop on the Reconciliation node to interpret
        # the children (and `skid_name` to title/name the PDF) — include them
        # so every logged snapshot is self-contained.
        self.app.queue_ui_values(
            RECONCILIATION_PATH,
            values,
            node_props={
                "injectors": reconciliation_injectors_meta(
                    [(inj.index, inj.display_name) for inj in self.injectors]
                ),
                "skid_name": self.app.app_display_name,
            },
        )

    async def update_ui(self):
        """
        Update the UI with the latest data.
        """
        for name in self._polling_node_name_bases:
            await self.app.set_tag(name, await self.get_polling_value(name))

        await self.update_reconciliation_ui()
