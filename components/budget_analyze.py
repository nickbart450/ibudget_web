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

        self.categories = DATA.get_categories()['category_name'].to_list()
        self.categories.sort()
        self.filters = dict(self.config['ui_settings.default_filters'])
        self.date_filters = [i.title() for i in list(DATA.date_filters.keys())]
        self.income_accts = DATA.accounts['account_id'][DATA.accounts['transaction_type'] == 'income'].to_list()
        self.category_summary_columns = ['Category', 'Expenses', 'Expenses %', 'Income', 'Income %']

        self.todays_accounts = None
        self.root_transactions = None
        self.render_dict = {
            "data_columns": self.category_summary_columns,
            "date_filters": self.date_filters,
            "accounts": ['All'] + list(DATA.accounts['account_name']),
            "categories": ['All'] + self.categories,
        }

    def current_filter_url(self):
        """Determines new url string based on currently selected page filters."""

        url = url_for('analyze') + "?date={}&account={}&date_start=&date_end=".format(
                  self.filters['date'],
                  self.filters['account'],
                  self.filters['category'],
                  # self.filters['date_start'],  # not implemented
                  # self.filters['date_end'],  # not implemented
              )
        return url

    def get(self):
        # Get Filters from URL
        if request.args.get('date') is not None:
            self.filters['date'] = request.args.get('date')

        if request.args.get('account') is not None:
            self.filters['account'] = request.args.get('account')

        if request.args.get('category') is not None:
            self.filters['category'] = request.args.get('category')

        self.render_dict["date_filter_default"] = self.filters["date"]
        self.render_dict["account_filter_default"] = self.filters["account"]
        self.render_dict["category_filter_default"] = self.filters["category"]

        # for k in self.render_dict.keys():
        #     print(k, self.render_dict[k], type(self.render_dict[k]))

        print('Fetching /analyze with filters: {}'.format(dict(self.filters)))
        LOGGER.debug('Fetching /analyze with filters: {}'.format(dict(self.filters)))

        # Calculate today's account values and format dict for page data
        self.todays_accounts = DATA.calculate_todays_account_values()
        for t in self.todays_accounts:
            self.todays_accounts[t] = '$ {:.2f}'.format(self.todays_accounts[t])
        self.render_dict["account_values_today"] = self.todays_accounts

        # Fetch transactions for analysis
        self.root_transactions = fetch_filtered_transactions(self.filters).sort_values('posted_date')

        # Fetch page data for modules
        self.category_summary()
        self.category_sum_by_month()

        active_year = DATA.year
        if DATA.year is None:
            active_year = 0

        return render_template(self.template,
                               active_year=active_year,
                               **self.render_dict)

    def category_summary(self):
        transactions = self.root_transactions.copy()

        # Remove investment, transfer, adjustment categories
        transactions = transactions[
            (transactions['category'] != 'Investment') &
            (transactions['category'] != 'Transfer') &
            (transactions['category'] != 'Adjustment')
            ]

        # Expense Transactions
        trans_exp = transactions[transactions['debit_account_id'] == 0]

        # Income Transactions
        trans_inc = transactions[
            (transactions['credit_account_id'] == 0) |
            (transactions['credit_account_id'].isin(self.income_accts))
            ]

        # Build resulting table and format text
        result = pd.DataFrame(columns=self.category_summary_columns)
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
                cat_trans = cat[1]  # Dataframe of transactions in single category
                category_sum = sum(cat_trans['amount'])

                category_percent = 0
                if total != 0:
                    category_percent = 100 * category_sum/total

                result.at[cat[0], column] = '${:.2f}'.format(category_sum)
                result.at[cat[0], column.lower()+'_percent'] = round(category_percent, 2)
                result.at[cat[0], column+" %"] = '{:.1f}%'.format(category_percent)

        # Post-processing
        result = result.sort_index()  # sort rows alphabetically
        new_index = result.index.to_list()
        new_index.remove('Total')
        new_index.append('Total')
        result = result.reindex(index=new_index)

        result['Category'] = result.index  # Duplicate Category index labels to column

        try:
            category_summary_table = result[self.category_summary_columns].fillna(value='$0.00').to_dict('records')
            expenses_pie_chart = result[['Category', 'expenses_percent']].fillna(value=0)
            expenses_pie_chart = (expenses_pie_chart
                                  .drop(expenses_pie_chart[expenses_pie_chart['expenses_percent'] == 0].index)
                                  .sort_values('expenses_percent')
                                  .to_dict('records'))

            income_pie_chart = result[['Category', 'income_percent']].fillna(value=0)
            income_pie_chart = (income_pie_chart
                                .drop(income_pie_chart[income_pie_chart['income_percent'] < 0.25].index)
                                .sort_values('income_percent')
                                .to_dict('records'))

        except KeyError as e:
            category_summary_table = pd.DataFrame(columns=self.category_summary_columns).to_dict('records')
            expenses_pie_chart = pd.DataFrame(columns=self.category_summary_columns).to_dict('records')
            income_pie_chart = pd.DataFrame(columns=self.category_summary_columns).to_dict('records')
            LOGGER.exception(e)
            LOGGER.warning('No data met current filters: {}'.format(dict(self.filters)))

        self.render_dict["data"] = category_summary_table
        self.render_dict["pie_expenses"] = expenses_pie_chart
        self.render_dict["pie_income"] = income_pie_chart

    def category_sum_by_month(self):
        months = {
            '01': 0,
            '02': 1,
            '03': 2,
            '04': 3,
            '05': 4,
            '06': 5,
            '07': 6,
            '08': 7,
            '09': 8,
            '10': 9,
            '11': 10,
            '12': 11,
                  }

        transactions = self.root_transactions.copy()

        # Remove investment, transfer, adjustment categories
        transactions = transactions[
            (transactions['category'] != 'Investment') &
            (transactions['category'] != 'Transfer') &
            (transactions['category'] != 'Adjustment')
            ]

        # Filter transactions by category
        c = self.filters['category']
        if c.lower() != 'all':
            transactions = transactions[transactions['category'] == c]

        # Add YYYY-MM date code column to transactions datatable
        transactions['year_month'] = transactions['posted_date'].apply(lambda row: row[0:7])
        transactions_grouped = transactions.groupby('year_month')

        # Build output table
        result = pd.DataFrame(columns=['date_code', 'income_sum', 'expense_sum'])
        first_month = int(list(transactions_grouped.groups)[0][-2:])
        last_month = int(list(transactions_grouped.groups)[-1][-2:])
        first_year = list(transactions_grouped.groups)[0][:4]
        last_year = list(transactions_grouped.groups)[-1][:4]
        m_list = [list(transactions_grouped.groups)[0]]
        m, y = first_month, int(first_year)
        for i in range(1, 100):
            m_list .append("{0}-{1:0=2d}".format(y, m))

            if m == 12:
                y += 1
                m = 0

            m += 1

        for m in m_list:
            if m > "{0}-{1:0=2d}".format(last_year, last_month):
                break

            try:
                month_trans = transactions_grouped.get_group(m)

                # Expense Transactions
                trans_exp = month_trans[month_trans['debit_account_id'] == 0]

                # Income Transactions
                trans_inc = month_trans[
                    (month_trans['credit_account_id'] == 0) |
                    (month_trans['credit_account_id'].isin(self.income_accts))
                    ]

                result.at[m, 'date_code'] = "{}-{}".format(m[0:4], months[m[-2:]])
                result.at[m, 'income_sum'] = round(sum(trans_inc['amount']), 2)
                result.at[m, 'expense_sum'] = round(sum(trans_exp['amount']), 2)

            except KeyError:
                result.at[m, 'date_code'] = "{}-{}".format(m[0:4], months[m[-2:]])
                result.at[m, 'income_sum'] = 0
                result.at[m, 'expense_sum'] = 0

        self.render_dict["area_category"] = result.to_dict("records")


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