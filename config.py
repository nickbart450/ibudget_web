import configparser

# Load Config File
config_files = [
    './config.ini',
    './environ.ini'
]
CONFIG = configparser.ConfigParser()
CONFIG.read(config_files)