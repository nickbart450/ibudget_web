# budget_server.py
__version__ = '0.0.1'

from budget_data import BudgetData

from flask import Flask, redirect, render_template, url_for, request, jsonify
import os
import logging
import datetime
import argparse

START_FLAG = True
# PORT = 9000

APP = Flask(__name__,
            template_folder="./templates",
            static_folder="./static",)

categories = [
    'All',
    'Credit Card Payment',
    'Job Pay',
    'Transfer',
    'Alcohol',
    'Automotive',
    'Dining',
    'Entertainment',
    'Gas',
    'Gifts',
    'Grocery',
    'Health Care',
    'Home',
    'Insurance',
    'Investment',
    'Merchandise',
    'Mortgage',
    'Other',
    'Other Services',
    'Tax Refund-Payment',
    'Utilities',
]


@APP.route("/", methods=['GET'])
def get_home():
    """
    Home page

    :return:
    """
    print('Fetching HOME')
    accounts = DATA.get_accounts()

    # STARTING_VALUES_2022 = {'transaction_id': 'start',
    #                    'transaction_date': 'start',
    #                    'posted_date': 'start',
    #                    '0': 0.00,  # External Accounts
    #                    '100': 2152.98,  # Main Skyla Checking
    #                    '101': 1005.00,  # Main Skyla Savings
    #                    '102': 14000.00,  # House/Emergency Skyla Savings
    #                    '103': 1480.00,  # TD Bank Checking
    #                    '104': 500.00,  # TD Savings
    #                    '201': 130.00,
    #                    '202': 2700.00,
    #                    '300': 0.00,
    #                    '4895': 0.00,
    #                    '5737': 0.00,
    #                    '9721': 0.00,
    #                    # 'Retirement'     : 0.00,
    #                    # 'Fidelity'       : 15000.00,
    #                    # 'TD Ameritrade'  : 0.00,
    #                    # 'Electrum Wallet': 0.135,
    #                    # 'Binance'        : 0.00,
    #                    # 'FTX'            : 0.00,
    #                    }
    # result = DATA.calculate_account_values(STARTING_VALUES_2022)

    STARTING_VALUES_2023 = {'transaction_id': 'start',
                            'transaction_date': 'start',
                            'posted_date': 'start',
                            '0': 0.00,  # External Accounts
                            '100': 2237.19,  # Main Skyla Checking
                            '101': 505.13,  # Main Skyla Savings
                            '102': 12002.95,  # House/Emergency Skyla Savings
                            '103': 1300.06,  # TD Bank Checking
                            '104': 500.00,  # TD Savings
                            '201': 520.00,
                            '202': 1890.00,
                            '300': 0.00,
                            '4895': -689.77,
                            '5737': 101.18,
                            '9721': 0.00}
    result = DATA.calculate_account_values(STARTING_VALUES_2023)

    # Reformat account values for CanvasJS stacked chart
    prev_date = 20211230
    account_values = {'100': [],
                      '101': [],
                      '102': [],
                      'TD': [],
                      'Cash': [],
                      }
    for i in result.index:
        date = int(result.iloc[i]['transaction_date'].strftime('%Y%m%d'))

        if prev_date == date:
            pass
        else:
            account_values['100'].append({"y": result.iloc[i-1]['100'], "label": result.iloc[i-1]['transaction_date'].strftime('%Y-%m-%d')})
            account_values['101'].append({"y": result.iloc[i-1]['101'], "label": result.iloc[i-1]['transaction_date'].strftime('%Y-%m-%d')})
            account_values['102'].append({"y": result.iloc[i-1]['102'], "label": result.iloc[i-1]['transaction_date'].strftime('%Y-%m-%d')})
            account_values['TD'].append({"y": result.iloc[i-1]['103']+result.iloc[i-1]['104'], "label": result.iloc[i-1]['transaction_date'].strftime('%Y-%m-%d')})
            account_values['Cash'].append({"y": result.iloc[i-1]['201']+result.iloc[i-1]['202'], "label": result.iloc[i-1]['transaction_date'].strftime('%Y-%m-%d')})
            prev_date = date

    # Calculate Burn Time for CanvasJS Line chart
    prev_date = 20211230
    burn_time = []
    for i in result.index:
        date = int(result.iloc[i]['transaction_date'].strftime('%Y%m%d'))

        if prev_date == date:
            pass
        else:
            y = result.iloc[i]['transaction_date'].year
            m = result.iloc[i]['transaction_date'].month
            d = result.iloc[i]['transaction_date'].day
            account_sum = sum([result.iloc[i-1]['100'], result.iloc[i-1]['101'], result.iloc[i-1]['102'],
                               result.iloc[i-1]['103'], result.iloc[i-1]['104'], result.iloc[i-1]['201'],
                               result.iloc[i-1]['202']])
            investment_est = 6000

            b = round((account_sum+investment_est)/3600, 2)

            burn_time.append({"year":y, "month": m, "day": d, "burn": b})
            prev_date = date


    # Translate Account Names for Datatables Columns
    translate = accounts[['account_id', 'name']]
    translate.set_index('account_id', inplace=True)
    translate = translate.to_dict(orient='dict')

    new_cols = []
    for c in result.columns:
        try:
            c = int(c)
            c = translate['name'][c]
        except:
            pass
        new_cols.append(c)

    result.columns = new_cols
    # result.to_csv('./test.csv')

    return render_template(
        'index.html',
        data=result.to_dict('records'),
        account_values=account_values,
        burn_time=burn_time,
    )


@APP.route("/transact/", methods=['GET'])
def get_transactions():
    """
    /transact page

    :return:
    """
    print('Fetching /transact')
    accounts = DATA.get_accounts()
    result = DATA.get_transactions()

    # Reformat amount column
    result['amount_string'] = result['amount'].map('$ {:,.2f}'.format)

    # Reformat date columns
    result['transaction_date'] = result['transaction_date'].dt.strftime('%Y-%m-%d')
    result['posted_date'] = result['posted_date'].dt.strftime('%Y-%m-%d')

    # Reformat is_posted column
    result['is_posted'] = result['is_posted'].replace([0, 1], ['', 'checked'])

    # Append account names
    account_name_list = ['All'] + list(accounts['name'])
    account_id_list = [0] + list(accounts['account_id'])
    account_translate_dict = {}
    for i in list(range(len(account_id_list))):
        account_translate_dict[account_id_list[i]] = account_name_list[i]
    result['credit_account_name'] = result['credit_account_id'].replace(account_translate_dict)
    result['debit_account_name'] = result['debit_account_id'].replace(account_translate_dict)

    # print(result.head())
    return render_template(
        'transactions_table.html',
        data=result.to_dict('records'),
        date_filter=list(DATA.date_filters.keys()),
        date_filter_default='Date Filter',
        accounts=account_name_list,
        account_filter_default='Account Filter',
        categories=categories,
        category_filter_default='All',
        income_expense_filter_default='both',
    )


@APP.route("/transact/data", methods=['POST', 'GET'])
def data_transactions():
    """
    /transact/<arguments>

    :return:
    """
    print('Fetching /transact with filters')
    accounts = DATA.get_accounts()

    # Get Date Filter
    request_date_filter = request.args.get('date')

    # Get Account Filter
    selected_account_filter = request.args.get('account')

    # Get Category Filter
    selected_category_filter = request.args.get('category')

    # Get & Reformat expense_income_filter
    expense_income_filter = request.args.get('income_expense')
    # print('expense_income_filter: ', expense_income_filter)
    selected_income_expense_filter = expense_income_filter.lower()

    result = DATA.get_transactions(
        date_filter=request_date_filter,
        start_date=None,
        end_date=None,
        date_type='transaction_date',
        account_filter=selected_account_filter,
        expense_income_filter=expense_income_filter,
        append_total=False,
    )

    if len(result) > 0:
        if selected_category_filter == 'All':
            pass
        else:
            result = result[result['category'] == selected_category_filter]

        # Reformat amount column
        result['amount_string'] = result['amount'].map('$ {:,.2f}'.format)

        # Reformat date columns
        result['transaction_date'] = result['transaction_date'].dt.strftime('%Y-%m-%d')
        result['posted_date'] = result['posted_date'].dt.strftime('%Y-%m-%d')

        # Reformat is_posted column
        result['is_posted'] = result['is_posted'].replace([0, 1], ['', 'checked'])

        # Append account names
        account_name_list = ['All'] + list(accounts['name'])
        account_id_list = [0] + list(accounts['account_id'])
        account_translate_dict = {}
        for i in list(range(len(account_id_list))):
            account_translate_dict[account_id_list[i]] = account_name_list[i]
        result['credit_account_name'] = result['credit_account_id'].replace(account_translate_dict)
        result['debit_account_name'] = result['debit_account_id'].replace(account_translate_dict)

        # print(result.head())
        return render_template(
            'transactions_table.html',
            data=result.to_dict('records'),
            date_filter=list(DATA.date_filters.keys()),
            date_filter_default=request_date_filter,
            accounts=account_name_list,
            account_filter_default=selected_account_filter,
            categories=categories,
            category_filter_default=selected_category_filter,
            income_expense_filter_default=selected_income_expense_filter,
        )
    else:
        print('No transactions meet current filters. redirecting back to /transact')
        return redirect(url_for('get_transactions'))


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

    accounts = DATA.get_accounts()
    credit_account = int(accounts[accounts['name'] == credit_account]['account_id'])

    if debit_account == '':
        # print('debit account is None: {}'.format(debit_account))
        debit_account = None
    else:
        debit_account = int(accounts[accounts['name'] == debit_account]['account_id'])

    print('adding transaction:')
    print('\ttransaction_date: ', transaction_date)
    print('\tposted_date: ', posted_date)
    print('\tcredit_account: ', credit_account)
    print('\tdebit_account: ', debit_account)
    print('\tamount: ', amount)
    print('\tcategory: ', category)
    print('\tdescription: ', description)
    print('\tvendor: ', vendor)
    print('\tposted_flag: ', posted_flag)

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
    return redirect(url_for('get_transactions'))


@APP.route("/transact/update_transaction", methods=['GET', 'POST'])
def update_transaction():
    print('Update transaction')
    # result = DATA.get_transactions()
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

    print('Updating transaction:')
    print('\ttransaction_id: ', transaction_id)
    print('\ttransaction_date: ', transaction_date)
    print('\tposted_date: ', posted_date)
    print('\tcredit_account: ', credit_account)
    print('\tdebit_account: ', debit_account)
    print('\tamount: ', amount)
    print('\tcategory: ', category)
    print('\tdescription: ', description)
    print('\tvendor: ', vendor)
    print('\tposted_flag: ', posted_flag)

    DATA.update_transaction(transaction_id,
        transaction_date=transaction_date,
        category=category,
        amount=amount,
        posted_date=posted_date,
        credit_account=credit_account,
        debit_account=debit_account,
        description=description,
        vendor=vendor,
        is_posted=posted_flag)
    return redirect(url_for('get_transactions'))


@APP.route("/transact/delete_transaction", methods=['GET', 'POST'])
def delete_transaction():
    print('Deleting transaction')
    transaction_id = request.args.get('transaction_id')
    DATA.delete_transaction(transaction_id)
    return redirect(url_for('get_transactions'))


if __name__ == '__main__':
    # Start Logger
    if not os.path.exists(os.path.abspath('./logs')):
        os.mkdir(os.path.abspath('./logs'))

    log_path = os.path.abspath('./logs')
    logging.basicConfig(level=logging.DEBUG,
                        filename=os.path.join(
                            log_path,
                            'budget_{}.log'.format(datetime.datetime.now().strftime('%Y_%m_%d-%H_%M_%S'))))
    LOGGER = logging.getLogger()

    # argparse setup
    parser = argparse.ArgumentParser(
        prog='budget_web',
        description='Individual Financial Tracking and Analysis Web Application',
        # epilog='Text at the bottom of help'
    )
    parser.add_argument('db_file')
    parser.add_argument('--port', nargs='?', const=9000, type=int)
    args = parser.parse_args()

    # Create data object and connect to database
    DATA = BudgetData()
    print('connecting to {}'.format(args.db_file))
    DATA.connect(args.db_file)

    if DATA.dbConnected:
        LOGGER.debug('db File Connected')
        LOGGER.debug('db SQL version: {}'.format(DATA.db_version))
    else:
        print('Failed to Connect to Database -- shutting down')
        LOGGER.debug('database connection failed -- cancelling startup')
        START_FLAG = False

    if START_FLAG:
        # webbrowser.open('http://127.0.0.1:{}'.format(PORT), new=2)  # , autoraise=True
        if args.port is None:
            port = 9000
        else:
            port = args.port
        LOGGER.debug('Starting Budget at: http://127.0.0.1:{}'.format(port))
        print('Budget Starting at: http://127.0.0.1:{}'.format(port))
        try:
            APP.run(debug=True, port=port)  # , use_reloader=False
        finally:
            DATA.close()