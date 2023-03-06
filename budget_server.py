# budget_server.py
__version__ = '0.1.1'

from budget_data import BudgetData
# from budget_data import init_logger

import os
import logging
import datetime
import argparse
import warnings
import config
from flask import Flask, redirect, render_template, url_for, request, jsonify
# from collections import namedtuple


def init_logger(log_directory='./logs'):
    # Start Logger
    log_path = os.path.abspath(log_directory)
    if not os.path.exists(log_path):
        os.mkdir(log_path)

    logging.basicConfig(level=logging.DEBUG,
                        filename=os.path.join(
                            log_path,
                            'budget_{}.log'.format(datetime.datetime.now().strftime('%Y_%m_%d-%H_%M_%S'))))
    logger = logging.getLogger() # Creates root logger
    return logger


def init_data(database_file):
    # Create new data object and connect to database. Previous object gets collected as garbage, running the __del__
    #   function, closing the former db connection
    data = BudgetData()
    data.connect(database_file)

    if data.dbConnected:
        LOGGER.debug('Connected to DATA')

        # Get Accounts from Data
        accounts = data.get_accounts()

    else:
        # LOGGER.debug('database connection failed -- cancelling startup')
        print('database connection failed')
        warnings.warn('database connection failed')
        LOGGER.warning('database connection failed. Attempted connection to: {}'.format(database_file))

    return data


# Create Flask Object
APP = Flask(__name__,
            template_folder="./templates",
            static_folder="./static", )

# Start Logger
LOGGER = init_logger() if not logging.getLogger().hasHandlers() else logging.getLogger()

# Load Config File
CONFIG = config.CONFIG

# Fetch database file location from the config. Defaults to live version
ENVIRON = CONFIG['env']['environ']
DB_FILE = CONFIG['database.{}'.format(ENVIRON)]['file']

DATA = init_data(DB_FILE)

CATEGORIES = CONFIG['ui_settings']['categories'].replace('\n', '')
CATEGORIES = CATEGORIES.split(',')

FILTERS = dict(CONFIG['ui_settings.default_filters'])


@APP.route("/", methods=['GET'])
def get_home():
    """
    Home page

    :return:
    """
    print('Fetching HOME')
    global DATA
    DATA = init_data(DB_FILE)

    result = DATA.calculate_account_values()

    accounts = DATA.get_accounts().set_index('account_id', drop=False)
    accounts.index = accounts.index.astype(str)
    asset_accounts = accounts.loc[accounts['account_type'] == 'asset']

    # Loop through the account values dataframe to calculate and construct CanvasJS dictionaries
    prev_date = 19700101
    asset_account_values = {}
    for a in list(asset_accounts.index):
        asset_account_values[str(a)] = []
    burn_time = []
    for i in result.index:
        date = int(result.iloc[i]['transaction_date'].strftime('%Y%m%d'))

        if date == prev_date:
            pass
        else:
            account_sum = 0
            for acc in list(asset_accounts.index):
                asset_account_values[str(acc)].append(
                    {"y": result.at[i, str(acc)],
                     "label": result.at[i, 'transaction_date'].strftime('%Y-%m-%d')}
                )
                account_sum += float(result.at[i, str(acc)])

            # Calculate Burn Time for CanvasJS Line chart
            y = result.at[i, 'transaction_date'].year
            m = result.at[i, 'transaction_date'].month
            d = result.at[i, 'transaction_date'].day

            investment_est = 7500

            burn = round((account_sum + investment_est) / 3800, 2)
            burn_time.append({"year": y, "month": m, "day": d, "burn": burn})

            prev_date = date

    # Translate Account Names for Datatables Columns
    new_cols = []
    for c in result.columns:
        try:
            c = accounts.at[int(c), 'name']
        except:
            pass
        new_cols.append(c)
    result.columns = new_cols
    result.fillna(value='')

    # Fetch today's account values from data object
    todays_accounts = DATA.calculate_todays_account_values()
    for t in todays_accounts:
        todays_accounts[t] = '$ {:.2f}'.format(todays_accounts[t])

    # Sort accounts for stacked chart
    account_order = [(i, sum(result[i])) for i in list(asset_account_values.keys())]
    account_sums = sorted([i[1] for i in account_order], reverse=True)
    account_view_reorder = []
    for x in range(len(account_sums)):
        for y in account_order:
            if y[1] == account_sums[x]:
                account_view_reorder.append(y[0])

    return render_template(
        'index.html',
        data=result.to_dict('records'),         # Used in table for account value per transaction
        accounts=accounts.to_dict('index'),     # Used to translate account_id to name
        account_values=asset_account_values,    # Account value dictionary by day for CanvasJS stacked bar chart
        account_view_order=account_view_reorder,  # List of account ids, ordered by average value largest to smallest
        account_values_today=todays_accounts,   # Account value dictionary for just today
        burn_time=burn_time,                    # List of dictionaries describing burn time
    )


@APP.route("/transact/", methods=['GET'])
def data_transactions():
    """
    /transact/<arguments>

    :return:
    """
    global FILTERS
    global DATA
    DATA = init_data(DB_FILE)

    # Get Date Filter
    if request.args.get('date') is not None:
        FILTERS['date'] = request.args.get('date')
    date_filters = [i.title() for i in list(DATA.date_filters.keys())]

    # Get Account Filter
    if request.args.get('account') is not None:
        FILTERS['account'] = request.args.get('account')

    # Get Category Filter
    if request.args.get('category') is not None:
        FILTERS['category'] = request.args.get('category')

    # Get & Reformat expense_income_filter
    if request.args.get('income_expense') is not None:
        FILTERS['income_expense'] = request.args.get('income_expense').lower()

    print('Fetching /transact with filters: {}'.format(dict(FILTERS)))

    result = fetch_filtered_transactions()

    if len(result) > 0:
        result.fillna(value='')
        return render_template(
            'transactions_table.html',
            data=result.to_dict('records'),
            date_filter=date_filters,
            accounts=['All'] + list(DATA.accounts['name']),
            categories=CATEGORIES,
            date_filter_default=FILTERS['date'],
            account_filter_default=FILTERS['account'],
            category_filter_default=FILTERS['category'],
            income_expense_filter_default=FILTERS['income_expense'],
        )
    else:
        print('WARNING! No transactions meet current filters. Redirecting back to /transact')
        LOGGER.debug('No transactions meet current filters. Redirecting back to /transact')
        LOGGER.debug('Current Filters: {}'.format(dict(FILTERS)))
        FILTERS = dict(CONFIG['ui_settings.default_filters'])  # reset filters to default and reset page
        return redirect(url_for('data_transactions'))


@APP.route("/transact/submit_transaction", methods=['POST'])
def submit_transaction():
    """
    /transact/submit_transaction

    Accessed by form

    :return: redirect
    """
    print('POSTing transaction')
    transaction_date = request.form['date']
    posted_date = request.form['post_date']
    credit_account = request.form['account-credit']
    debit_account = request.form['account-debit']
    amount = request.form['amount']
    category = request.form['category']
    description = request.form['description']
    vendor = request.form['vendor']
    posted_flag = request.form.get('is_posted_selector')

    if posted_flag == 'on':
        posted_flag = True
    else:
        posted_flag = False

    # accounts = DATA.get_accounts()
    credit_account = int(DATA.accounts[DATA.accounts['name'] == credit_account]['account_id'])

    if debit_account == '':
        # print('debit account is None: {}'.format(debit_account))
        debit_account = None
    else:
        debit_account = int(DATA.accounts[DATA.accounts['name'] == debit_account]['account_id'])

    DATA.add_transaction(
        transaction_date=transaction_date,
        category=category,
        amount=amount,
        posted_date=posted_date,
        credit_account=credit_account,
        debit_account=debit_account,
        description=description,
        vendor=vendor,
        is_posted=posted_flag)
    return redirect(url_for('data_transactions'))


@APP.route("/transact/update_transaction", methods=['POST'])
def update_transaction():
    print('POSTing transaction update')
    transaction_id = request.args.get('transaction_id')

    transaction_date = request.form['date']
    posted_date = request.form['post_date']
    credit_account = request.form['account-credit']
    debit_account = request.form['account-debit']
    amount = request.form['amount']
    category = request.form['category']
    description = request.form['description']
    vendor = request.form['vendor']
    posted_flag = request.form.get('is_posted_selector')
    if posted_flag == 'on':
        posted_flag = True
    else:
        posted_flag = False

    DATA.update_transaction(transaction_id,
                            transaction_date=transaction_date,
                            posted_date=posted_date,
                            category=category,
                            amount=amount,
                            credit_account=credit_account,
                            debit_account=debit_account,
                            description=description,
                            vendor=vendor,
                            is_posted=posted_flag)

    return redirect(url_for('data_transactions'))


@APP.route("/transact/delete_transaction", methods=['GET'])
def delete_transaction():
    print('Deleting transaction')
    transaction_id = request.args.get('transaction_id')
    DATA.delete_transaction(transaction_id)
    return redirect(url_for('data_transactions'))


def fetch_filtered_transactions():
    # Fetch filtered results
    result = DATA.get_transactions(
        date_filter=FILTERS['date'],
        start_date=None,
        end_date=None,
        date_type='transaction_date',
        account_filter=FILTERS['account'],
        expense_income_filter=FILTERS['income_expense'],
        append_total=False,
    )

    if FILTERS['category'] == 'All':
        pass
    else:
        result = result[result['category'] == str(FILTERS['category'])]

    # Reformat amount column
    result['amount_string'] = result['amount'].map('$ {:,.2f}'.format)

    # Reformat date columns
    result['transaction_date'] = result['transaction_date'].dt.strftime('%Y-%m-%d')
    result['posted_date'] = result['posted_date'].dt.strftime('%Y-%m-%d')

    # Reformat is_posted column
    result['is_posted'] = result['is_posted'].replace([0, 1], ['', 'checked'])

    # Append account names
    account_id_list = [0] + list(DATA.accounts['account_id'])
    account_translate_dict = {}
    for i in list(range(len(account_id_list))):
        account_translate_dict[account_id_list[i]] = (['All'] + list(DATA.accounts['name']))[i]
    result['credit_account_name'] = result['credit_account_id'].replace(account_translate_dict)
    result['debit_account_name'] = result['debit_account_id'].replace(account_translate_dict)

    return result


if __name__ == '__main__':
    ENVIRON = CONFIG['env']['environ']
    print('Config environment: {}'.format(ENVIRON))
    LOGGER.debug('Config environment: {}'.format(ENVIRON))

    # argparse setup -- Available Arguments:
    #   --db_file   specify new .db file to open
    #   --port      specify alternative port number to launch development server on (Default: 9000)
    parser = argparse.ArgumentParser(
        prog='budget_web',
        description='Individual Financial Tracking and Analysis Web Application',
        # epilog='Text at the bottom of help'
    )
    parser.add_argument('--db_file')
    parser.add_argument('--port', nargs='?', const=9000, type=int)
    args = parser.parse_args()

    # Rebuild data object with our args/options and reconnect to database
    # Allows us to specify custom or alternative database file at testing startup
    if args.db_file is not None:
        db_file = os.path.abspath(args.db_file)
        DATA = init_data(db_file)

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
