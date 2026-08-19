from pydoover.docker import run_app

from .application import OpcuaReaderApplication


def main():
    """
    Run the application.
    """
    run_app(OpcuaReaderApplication())
