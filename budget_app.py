import os
import logging
import datetime
from flask import Flask

ROOT = os.getcwd()

# Create Flask Object
APP = Flask(__name__,
            template_folder=os.path.join(ROOT, "templates"),
            static_folder=os.path.join(ROOT, "static"))

log_dir = os.path.join(ROOT, 'logs')
def init_logger(log_directory=log_dir):
    log_path = os.path.abspath(log_directory)
    if not os.path.exists(log_path):
        os.mkdir(log_path)

    logging.basicConfig(level=logging.DEBUG,
                        filename=os.path.join(
                            log_path,
                            'budget_{}.log'.format(datetime.datetime.now().strftime('%Y_%m_%d-%H_%M_%S'))))
    logger = logging.getLogger()  # Creates root logger
    return logger


# Start Logger
LOGGER = init_logger() if not logging.getLogger().hasHandlers() else logging.getLogger()


# Attach modules
import budget_home
import budget_transactions
import modify_transactions
import update
