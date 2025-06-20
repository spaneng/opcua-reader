"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""

def test_import_app():
    from opcua_reader.application import OpcuaReaderApplication
    assert OpcuaReaderApplication

def test_config():
    from opcua_reader.app_config import OpcuaReaderConfig

    config = OpcuaReaderConfig()
    assert isinstance(config.to_dict(), dict)

def test_ui():
    from opcua_reader.app_ui import OpcuaReaderUI
    assert OpcuaReaderUI

def test_state():
    from opcua_reader.app_state import OpcuaReaderState
    assert OpcuaReaderState