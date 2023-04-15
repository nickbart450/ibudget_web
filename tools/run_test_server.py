# run_test_server.py
__version__ = '0.2.0'

import os
import argparse

from budget_app import APP, LOGGER
from budget_data import BudgetData, DATA
from components import config


if __name__ == '__main__':
    # Load Config File
    CONFIG = config.CONFIG

    # Fetch database file location from the config. Defaults to live version
    ENVIRON = CONFIG['env']['environ']
    LOGGER.debug('Config environment: {}'.format(ENVIRON))
    DB_FILE = CONFIG['database.{}'.format(ENVIRON)]['file']

    CATEGORIES = CONFIG['ui_settings']['categories'].replace('\n', '')
    CATEGORIES = CATEGORIES.split(',')

    FILTERS = dict(CONFIG['ui_settings.default_filters'])

    # argparse setup -- Available Arguments:
    #   --db_file   specify new .db file to open
    #   --port      specify alternative port number to launch development server on (Default: 9000)
    parser = argparse.ArgumentParser(
        prog='budget_web',
        description='Individual Financial Tracking and Analysis Web Application',
    )
    parser.add_argument('--db_file')
    parser.add_argument('--port', nargs='?', const=9000, type=int)
    args = parser.parse_args()

    # Rebuild data object with our args/options and reconnect to database
    # Allows us to specify custom or alternative database file at testing startup
    if args.db_file is not None:
        db_file = os.path.abspath(args.db_file)
        DATA = BudgetData()
        DATA.connect(db_file)

    if args.port is None:
        port = 9000
    else:
        port = args.port

    print('Budget Starting at: http://127.0.0.1:{}'.format(port))
    LOGGER.info('Starting Budget at: http://127.0.0.1:{}'.format(port))
    try:
        APP.run(debug=True, port=port)  # use_reloader=False
    finally:
        DATA.close()
