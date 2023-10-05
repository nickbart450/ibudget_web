import pandas as pd

from components import page
from budget_app import APP, LOGGER
from budget_data import DATA, fetch_filtered_transactions
from flask import request, render_template, redirect, url_for


class AnalyzePage(page.Page):
    def __init__(self):
        """
        /analyze/<arguments>
        """

        super().__init__()
        self.template = 'analyze.html'
        self.name = 'analyze'

        self.categories = self.config['ui_settings']['categories'].replace('\n', '').split(',')
        self.filters = dict(self.config['ui_settings.default_filters'])
        self.date_filters = [i.title() for i in list(DATA.date_filters.keys())]

        self.category_summary_columns = ['Category', 'Expenses', 'Expenses %', 'Income', 'Income %']

    def current_filter_url(self):

        url = url_for('analyze') + \
              "?date={}&account={}&date_start=&date_end=".format(
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

        print('Fetching /analyze with filters: {}'.format(dict(self.filters)))
        LOGGER.debug('Fetching /analyze with filters: {}'.format(dict(self.filters)))

        # Calculate today's account values from database
        self.todays_accounts = DATA.calculate_todays_account_values()
        for t in self.todays_accounts:
            self.todays_accounts[t] = '$ {:.2f}'.format(self.todays_accounts[t])

        # Get category summary data and render page
        try:
            result = self.category_summary()
        except KeyError as e:
            result = pd.DataFrame(columns=self.category_summary_columns)
            LOGGER.exception(e)
            LOGGER.warning('No data met current filters: {}'.format(dict(self.filters)))

        return render_template(
            self.template,
            data_columns=result.columns.to_list(),
            data=result.to_dict('records'),
            date_filter=self.date_filters,
            accounts=['All'] + list(DATA.accounts['name']),
            account_values_today=self.todays_accounts,  # Account value dictionary for just today
            categories=self.categories,
            date_filter_default=self.filters['date'],
            account_filter_default=self.filters['account'],
            category_filter_default=self.filters['category'],
            income_expense_filter_default=self.filters['income_expense'],
        )

    def category_summary(self):
        # Summary by category
        root_transactions = fetch_filtered_transactions(self.filters)

        # Remove investment, transfer, adjustment categories
        root_transactions = root_transactions[
            (root_transactions['category'] != 'Investment') &
            (root_transactions['category'] != 'Transfer') &
            (root_transactions['category'] != 'Adjustment')
            ]

        # Expense Transactions
        trans_exp = root_transactions[root_transactions['debit_account_id'] == 0]

        # Income Transactions
        trans_inc = root_transactions[
            (root_transactions['credit_account_id'] == 0) |
            (root_transactions['credit_account_id'] == 300)
            ]

        result = pd.DataFrame()
        n = 0
        for t in [trans_exp, trans_inc]:
            if n == 0:
                column = 'Expenses'
                n += 1
            else:
                column = 'Income'

            total = sum(t['amount'])
            result.at['Total', column] = '${:.2f}'.format(total)

            grouped_trans = t.groupby('category')
            for cat in grouped_trans:
                cat_trans = cat[1]
                category_sum = sum(cat_trans['amount'])
                category_percent = 100 * category_sum/total
                result.at[cat[0], column] = '${:.2f}'.format(category_sum)
                result.at[cat[0], column+" %"] = '{:.1f}%'.format(category_percent)

        # Post-processing
        result = result.fillna(value='$0.00')
        result = result.sort_index()  # sort rows alphabetically
        new_index = result.index.to_list()
        new_index.remove('Total')
        new_index.append('Total')
        result = result.reindex(index=new_index)

        result['Category'] = result.index  # Duplicate Category index labels to column
        result = result[self.category_summary_columns]  # Reorder columns

        return result

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


ANALYZE_PAGE = AnalyzePage()


@APP.route("/analyze/", methods=['GET'])
def analyze():
    """
    /analyze/<arguments>

    :return: render_template
    """

    return ANALYZE_PAGE.get()


# @APP.route("/transact/submit_transaction", methods=['POST'])
# def submit_transaction():
#     """
#     /transact/submit_transaction
#        Accessed by form
#
#     :return: redirect
#     """
#     TRANSACTION_PAGE.submit()
#     return redirect(TRANSACTION_PAGE.current_filter_url())
#
#
# @APP.route("/transact/update_transaction", methods=['POST'])
# def update_transaction():
#     TRANSACTION_PAGE.update()
#     return redirect(TRANSACTION_PAGE.current_filter_url())
#
#
# @APP.route("/transact/delete_transaction", methods=['GET'])
# def delete_transaction():
#     TRANSACTION_PAGE.delete()
#     return redirect(TRANSACTION_PAGE.current_filter_url())