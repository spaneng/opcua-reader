from pydoover.docker import run_app

from .application import OpcuaReaderApplication
from .app_config import OpcuaReaderConfig

import logging
class ExcludePackageFilter(logging.Filter):
    """
    Filters out any log records whose logger name starts with one of the
    specified package prefixes (e.g., 'asyncua').
    """
    def __init__(self, *blocked_prefixes: str):
        super().__init__()
        # default to 'asyncua' if nothing passed
        self.blocked = blocked_prefixes or ("asyncua",)

    def filter(self, record: logging.LogRecord) -> bool:
        name = record.name  # e.g. "asyncua.client.client" or "myapp.module"
        return not any(name == p or name.startswith(p + ".") for p in self.blocked)

def main():
    """
    Run the application.
    """
    run_app(OpcuaReaderApplication(config=OpcuaReaderConfig()), log_filters=ExcludePackageFilter("asyncua"))
