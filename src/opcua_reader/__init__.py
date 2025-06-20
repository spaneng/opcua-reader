from pydoover.docker import run_app

from .application import OpcuaReaderApplication
from .app_config import OpcuaReaderConfig

def main():
    """
    Run the application.
    """
    run_app(OpcuaReaderApplication(config=OpcuaReaderConfig()))
