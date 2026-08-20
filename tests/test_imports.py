"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""


def test_import_app():
    from opcua_reader.application import OpcuaReaderApplication

    assert OpcuaReaderApplication
    assert OpcuaReaderApplication.config_cls is not None
    assert OpcuaReaderApplication.ui_cls is not None


def test_config():
    from opcua_reader.app_config import OpcuaReaderConfig

    schema = OpcuaReaderConfig.to_schema()
    assert isinstance(schema, dict)
    assert len(schema["properties"]) > 0


def test_ui():
    from pydoover.ui import UI

    from opcua_reader.app_ui import OpcuaReaderUI

    assert issubclass(OpcuaReaderUI, UI)


def test_state():
    from opcua_reader.app_state import OpcuaReaderState

    assert OpcuaReaderState
