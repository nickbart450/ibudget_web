# page.py -- Base webpage class and associated functions for iBudget-web

# External Imports
from flask import render_template


# Internal Imports
from budget_data import CONFIG
from budget_data import DATA


class Page:
    def __init__(self):
        self.config = CONFIG
        self.config.reload()

        self.todays_accounts = None
        self.todays_accounts_show = {}
        self.todays_accounts_hidden = {}

    def render(self, template, **kwargs):
        self.config.reload()

        return render_template(
            template,
            **kwargs
        )

    def get_todays_accounts(self):
        # Fetch today's account values from data object
        # self.todays_accounts is dict with keys of account_id and values
        self.todays_accounts = DATA.calculate_todays_account_values()
        for t in self.todays_accounts:
            if "total" in str(t).lower():
                self.todays_accounts_show[t] = '$ {:.2f}'.format(self.todays_accounts[t])
                continue

            account_name = DATA.accounts.at[t, 'account_name']

            if DATA.accounts.at[t, 'hidden']:
                self.todays_accounts_hidden[account_name] = '$ {:.2f}'.format(self.todays_accounts[t])
            else:
                self.todays_accounts_show[account_name] = '$ {:.2f}'.format(self.todays_accounts[t])


if __name__ == '__main__':
    import pandas as pd
    pd.set_option("display.max_rows", None, "display.max_columns", None, "display.width", 2000)  # makes pandas print full table
    p = Page()
    p.get_todays_accounts()
