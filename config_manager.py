import configparser
import os
from logger import logger  # Import the logger

class ConfigManager:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        logger.info(f"Loaded configuration from {config_file}")

    def get(self, section, key, fallback=None):
        value = self.config.get(section, key, fallback=fallback)
        return os.path.expanduser(value) if '~' in value else value

    def getfloat(self, section, key, fallback=None):
        return self.config.getfloat(section, key, fallback=fallback)

    def getboolean(self, section, key, fallback=None):
        return self.config.getboolean(section, key, fallback=fallback)

config = ConfigManager()