import os
from pathlib import Path
import sys

import yaml

import logging

logger = logging.getLogger(__name__)

SETTINGS_PATH = os.environ.get("SETTINGS", None)

class Settings:
    _ERROR_ON_STARTUP = """Please configure settings by running
    export SETTINGS=/path/to/conf.yaml"""

    def __init__(self, settings_path=SETTINGS_PATH):
        """Read the user settings"""

        if not settings_path:
            logger.critical(self._ERROR_ON_STARTUP)
            sys.exit()

        self.__get_settings(settings_path)

    @property
    def settings(self):

        return self._settings

    
    def __get_settings(self, settings_path):
        """Get variables from settings file."""

        try:
            with Path(settings_path).open("r", encoding="utf-8") as settings_file:
                self._settings = yaml.safe_load(settings_file)

        except OSError as ose:
            logger.critical("Failed to read settings file, please check your SETTINGS env variable: %s", ose)
            sys.exit(1)