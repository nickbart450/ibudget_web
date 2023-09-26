import pandas as pd

from components import page
from budget_app import APP, LOGGER
from budget_data import DATA, fetch_filtered_transactions
from flask import request, render_template, redirect, url_for


class TransactionsPage(page.Page):
    def __init__(self):
        """
        /transact/<arguments>
        """

        super().__init__()
        self.template = 'transactions_table.html'
        self.name = 'transact'

        self.categories = self.config['ui_settings']['categories'].replace('\n', '').split(',')
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
        self.todays_accounts = DATA.calculate_todays_account_values()
        for t in self.todays_accounts:
            self.todays_accounts[t] = '$ {:.2f}'.format(self.todays_accounts[t])

        # Get transaction data from database table with current filters
        result = fetch_filtered_transactions(self.filters)
        result.fillna(value='')

        # Split Transactions by posted status
        self.transactions = result.groupby('is_posted')
        try:
            self.posted_transactions = self.transactions.get_group('checked')
        except KeyError as e:
            self.posted_transactions = pd.DataFrame(columns=result.columns)
            LOGGER.exception(e)

        try:
            self.upcoming_transactions = self.transactions.get_group('')
        except KeyError as e:
            self.upcoming_transactions = pd.DataFrame(columns=result.columns)
            LOGGER.exception(e)

        if self.transactions is None or len(self.transactions) == 0:
            print('WARNING! No transactions meet current filters. Redirecting back to /transact')
            LOGGER.warning('No transactions meet current filters. Redirecting back to /transact')
            LOGGER.warning('Current Filters: {}'.format(dict(self.filters)))
            self.filters = dict(self.config['ui_settings.default_filters'])  # reset filters to default and reset page
            return redirect(url_for('data_transactions'))
        elif len(self.posted_transactions) > 0 or len(self.upcoming_transactions) > 0:
            return render_template(
                self.template,
                posted_data=self.posted_transactions.to_dict('records'),
                upcoming_data=self.upcoming_transactions.to_dict('records'),
                date_filter=self.date_filters,
                accounts=['All'] + list(DATA.accounts['name']),
                account_values_today=self.todays_accounts,  # Account value dictionary for just today
                categories=self.categories,
                date_filter_default=self.filters['date'],
                account_filter_default=self.filters['account'],
                category_filter_default=self.filters['category'],
                income_expense_filter_default=self.filters['income_expense'],
            )

        else:
            # Really unlikely to wind up here, but want to recover safely nonetheless
            LOGGER.error('No transactions meet current filters. Redirecting back to /transact')
            self.filters = dict(self.config['ui_settings.default_filters'])  # reset filters to default and reset page
            return redirect(url_for('data_transactions'))

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

        credit_account = int(DATA.accounts[DATA.accounts['name'] == credit_account]['account_id'])

        if debit_account == '':
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

    def delete(self):
        print('Deleting transaction')
        transaction_id = request.args.get('transaction_id')
        DATA.delete_transaction(transaction_id)


TRANSACTION_PAGE = TransactionsPage()


@APP.route("/transact/", methods=['GET'])
def data_transactions():
    """
    /transact/<arguments>

    :return: render_template
    """

    return TRANSACTION_PAGE.get()


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
