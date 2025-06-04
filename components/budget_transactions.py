from components import page
from budget_app import APP, LOGGER
from budget_data import DATA, fetch_filtered_transactions
from flask import request, render_template, redirect, url_for, jsonify
import pandas as pd


class TransactionsPage(page.Page):
    def __init__(self):
        """
        /transact/<arguments>
        """

        super().__init__()
        self.template = 'transactions_table.html'
        self.name = 'transact'

        self.filters = dict(self.config['ui_settings.default_filters'])
        self.date_filters = [i.title() for i in list(DATA.date_filters.keys())]

    def current_filter_url(self):
        url = url_for('data_transactions') + \
              "?income_expense={}&date={}&account={}&category={}&date_start=&date_end=".format(
                  self.filters['income_expense'],
                  self.filters['date'],
                  self.filters['account'],
                  self.filters['category'],
                  # self.filters['date_start'],  # not implemented
                  # self.filters['date_end'],  # not implemented
              )
        return url

    def fetch_transactions(self):
        # Get transaction data from database table with current filters
        result = fetch_filtered_transactions(self.filters)
        result.fillna(value='')
        return result

    def get(self):
        # Get Date Filter
        if request.args.get('date') is not None:
            self.filters['date'] = request.args.get('date')

        # Get Account Filter
        if request.args.get('account') is not None:
            self.filters['account'] = request.args.get('account')

        # Get Category Filter
        if request.args.get('category') is not None:
            self.filters['category'] = request.args.get('category')

        # Get & Reformat expense_income_filter
        if request.args.get('income_expense') is not None:
            self.filters['income_expense'] = request.args.get('income_expense').lower()

        print('Fetching /transact with filters: {}'.format(dict(self.filters)))
        LOGGER.debug('Fetching /transact with filters: {}'.format(dict(self.filters)))

        # Calculate today's account values from database
        todays_accounts = DATA.calculate_todays_account_values()
        for t in todays_accounts:
            todays_accounts[t] = '$ {:.2f}'.format(todays_accounts[t])

        # Fetch latest categories
        categories = DATA.categories['category_name'].to_list()
        categories.sort()

        active_year = DATA.year
        if DATA.year is None:
            active_year = 0

        return render_template(
            self.template,
            date_filter=self.date_filters[:-2],
            active_year=active_year,
            accounts=['All'] + DATA.accounts['account_name'].to_list(),
            account_values_today=todays_accounts,  # Account value dictionary for just today
            categories=['All'] + categories,
            date_filter_default=self.filters['date'],
            account_filter_default=self.filters['account'],
            category_filter_default=self.filters['category'],
            income_expense_filter_default=self.filters['income_expense'],
        )

    def update(self):
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

        return redirect(self.current_filter_url())

    def submit(self):
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

        credit_account = int(DATA.accounts[DATA.accounts['account_name'] == credit_account]['account_id'])

        if debit_account == '':
            debit_account = None
        else:
            debit_account = int(DATA.accounts[DATA.accounts['account_name'] == debit_account]['account_id'])

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

    def delete(self):
        print('Deleting transaction(s)')
        transaction_id = request.args.get('transaction_id')
        transaction_list = transaction_id.split(',')

        for i in transaction_list:
            DATA.delete_transaction(i)
            print('Transaction {id} deleted'.format(id=i))

    def duplicate(self):
        print('duplicating transaction(s)')
        transaction_id = request.args.get('transaction_id')
        transaction_list = transaction_id.split(',')

        for i in transaction_list:
            DATA.duplicate_transaction(i)
            print('Transaction {id} duplicated'.format(id=i))

    def mark_posted(self):
        print('Flipping transaction(s) posted flag')
        transaction_id = request.args.get('transaction_id')
        transaction_list = transaction_id.split(',')

        for i in transaction_list:
            if DATA.get_transaction(DATA.dbConnection, i)['is_posted']:
                DATA.update_transaction(i, is_posted=False)
                print('Transaction {id} unmarked as posted'.format(id=i))
            else:
                DATA.update_transaction(i, is_posted=True)
                print('Transaction {id} marked as posted'.format(id=i))


TRANSACTION_PAGE = TransactionsPage()


@APP.route("/transact/", methods=['GET'])
def data_transactions():
    """
    /transact/<arguments>

    :return: render_template
    """

    if DATA.year == 0:
        DATA.year = None

    elif DATA.year is None:
        print('loading /transact with default year filter')
        DATA.set_year()

    return TRANSACTION_PAGE.get()


@APP.route("/transact/_posted_table_data/", methods=['GET'])
def _posted_table_data():
    print('fetching posted table data')

    result = TRANSACTION_PAGE.fetch_transactions()

    # Split Transactions by posted status
    grouped_result = result.groupby('is_posted')

    try:
        posted_transactions = grouped_result.get_group('checked')
    except KeyError as e:
        posted_transactions = pd.DataFrame(columns=result.columns)
        LOGGER.exception(e)

    return jsonify({'data': posted_transactions.to_dict('records')})


@APP.route("/transact/_upcoming_table_data/", methods=['GET'])
def _upcoming_table_data():
    print('fetching upcoming table data')

    result = TRANSACTION_PAGE.fetch_transactions()

    # Split Transactions by posted status
    grouped_result = result.groupby('is_posted')

    try:
        upcoming_transactions = grouped_result.get_group('')
    except KeyError as e:
        upcoming_transactions = pd.DataFrame(columns=result.columns)
        LOGGER.exception(e)

    return jsonify({'data': upcoming_transactions.to_dict('records')})


@APP.route("/transact/submit_transaction", methods=['POST'])
def submit_transaction():
    """
    /transact/submit_transaction
       Accessed by form

    :return: redirect
    """
    TRANSACTION_PAGE.submit()
    return redirect(TRANSACTION_PAGE.current_filter_url())


@APP.route("/transact/update_transaction", methods=['POST'])
def update_transaction():
    TRANSACTION_PAGE.update()
    return redirect(TRANSACTION_PAGE.current_filter_url())


@APP.route("/transact/delete_transaction", methods=['GET'])
def delete_transaction():
    TRANSACTION_PAGE.delete()
    return redirect(TRANSACTION_PAGE.current_filter_url())


@APP.route("/transact/duplicate_transaction", methods=['GET'])
def duplicate_transaction():
    TRANSACTION_PAGE.duplicate()
    return redirect(TRANSACTION_PAGE.current_filter_url())


@APP.route("/transact/post_transaction", methods=['GET'])
def post_transaction():
    TRANSACTION_PAGE.mark_posted()
    return redirect(TRANSACTION_PAGE.current_filter_url())
