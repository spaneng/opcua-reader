"""Fuel Additive Reconciliation Report entry point."""

from typing import Any

from pydoover.processor import run_app

from .app_config import FuelAdditiveReportConfig
from .application import FuelAdditiveReportGenerator


def handler(event: dict[str, Any], context: Any) -> None:
    """Run the report generator."""
    FuelAdditiveReportConfig.clear_elements()
    run_app(FuelAdditiveReportGenerator(), event, context)
