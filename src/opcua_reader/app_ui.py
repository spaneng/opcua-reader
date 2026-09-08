import logging

from pydoover import ui

from .injector import build_injector_ui
from .overview import build_overview_ui

log = logging.getLogger(__name__)


class OpcuaReaderUI(ui.UI, display_name="Fuel Additive"):
    """UI built at runtime from the configured injectors.

    Each injector gets a submodule with its HMI widget and batches table, and
    the overview contributes the analog variables plus the Reconciliation
    widget. The remote-component children carry literal values that the
    application patches into ui_state each loop; the plain analog variables
    are tag-bound.
    """

    async def setup(self):
        injector_specs = [
            (int(inj.injector_index.value), inj.injector_name.value)
            for inj in self.config.injectors.elements
        ]

        for index, display_name in injector_specs:
            self.add_element(build_injector_ui(index, display_name))

        for elem in build_overview_ui(
            injector_specs,
            self.config.timezone.value,
            self.config.skid_name.value,
            tank_count=int(self.config.tank_count.value),
        ):
            self.add_element(elem)
