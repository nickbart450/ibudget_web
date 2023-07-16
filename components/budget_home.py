from components import page
from budget_app import APP, LOGGER
from budget_data import DATA


class Home(page.Page):
    def __init__(self):
        """
        Home page

        :return:
        """
        super().__init__()
        self.template = 'index.html'
        self.name = 'home'

        self.include_retire = False

        self.accounts = None
        self.todays_accounts = None

        self.asset_accounts = None
        self.asset_account_values = None
        self.asset_accounts_no_invest = None

        self.burn_time_full = None  # only removes retirement accounts if specified in config file options
        self.burn_time_no_invest = None  # removes all investment accounts from burn time calculation (lower limit)

        self.account_vals = None

    def get(self):
        print('Fetching {}'.format(self.name))

        self.accounts = DATA.get_accounts().set_index('account_id', drop=False)
        self.accounts.index = self.accounts.index.astype(str)
        self.asset_accounts = self.accounts.loc[self.accounts['account_type'] == 'asset']
        self.asset_accounts_no_invest = self.asset_accounts.loc[self.asset_accounts['transaction_type'] != 'investment']

        # Fetch today's account values from data object
        self.todays_accounts = DATA.calculate_todays_account_values()
        for t in self.todays_accounts:
            self.todays_accounts[t] = '$ {:.2f}'.format(self.todays_accounts[t])

        self.include_retire = str(self.config['ui_settings']['include_retirement_in_burn']).lower() == "true"

        # Loop through the account values dataframe to calculate and construct CanvasJS dictionaries
        prev_date = 19700101
        self.asset_account_values = {}
        for a in list(self.asset_accounts.index):
            self.asset_account_values[str(a)] = []
        self.burn_time_full = []
        self.burn_time_no_invest = []

        self.account_vals = DATA.calculate_account_values()
        for i in self.account_vals.index:
            date = int(self.account_vals.iloc[i]['transaction_date'].strftime('%Y%m%d'))

            if date == prev_date:
                # Skip repeated dates. Only capture 1st of each day
                pass
            else:
                account_sum = 0
                account_sum_no_invest = 0
                for acc in list(self.asset_accounts.index):
                    if 'retire' in self.accounts.at[acc, 'name'].lower():
                        # pre-tax money gets adjusted here if you decide to include these accounts in your burn
                        if self.include_retire:
                            y = float(self.account_vals.at[i, str(acc)]) * (
                                    1 - float(self.config['personal']['retirement_tax_rate']))
                        else:
                            y = 0
                    else:
                        y = self.account_vals.at[i, str(acc)]

                    label = self.account_vals.at[i, 'transaction_date'].strftime('%Y-%m-%d')
                    self.asset_account_values[str(acc)].append(
                        {"y": y,
                         "label": label}
                    )
                    account_sum += y

                for acc in list(self.asset_accounts_no_invest.index):
                    account_sum_no_invest += float(self.account_vals.at[i, str(acc)])

                # Assemble Burn Time CanvasJS Line chart
                y = self.account_vals.at[i, 'transaction_date'].year
                m = self.account_vals.at[i, 'transaction_date'].month
                d = self.account_vals.at[i, 'transaction_date'].day

                monthly_expense = float(self.config['personal']['average_monthly_expend'])
                b_full = round(account_sum / monthly_expense, 2)
                self.burn_time_full.append({"year": y, "month": m, "day": d, "burn": b_full})

                b_part = round(account_sum_no_invest / monthly_expense, 2)
                self.burn_time_no_invest.append({"year": y, "month": m, "day": d, "burn": b_part})

                prev_date = date

        # Sort accounts for stacked chart based on cumulative value over the year
        account_order = [(i, sum(self.account_vals[i])) for i in list(self.asset_account_values.keys())]
        account_sums = sorted([i[1] for i in account_order], reverse=True)
        account_view_reorder = []
        for x in range(len(account_sums)):
            for y in account_order:
                if y[1] == account_sums[x]:
                    account_view_reorder.append(y[0])

        self.asset_accounts_no_invest = [i for i in account_view_reorder if
                                         i in list(self.asset_accounts_no_invest.index)]

        # Translate Account Names for Datatables Columns
        new_cols = []
        for c in self.account_vals.columns:
            try:
                c = self.accounts.at[int(c), 'name']
            except ValueError:
                pass
            except KeyError:
                pass
            new_cols.append(c)
        self.account_vals.columns = new_cols
        self.account_vals.fillna(value='')
        self.account_vals = self.account_vals

        if self.include_retire:
            include_retire_str = '[with Retirement Account(s)]'
        else:
            include_retire_str = '[excl. Retirement Account(s)]'

        # print('\nHOME page returns - ')
        # print('\naccount_values_by_transaction', self.account_vals.to_dict('records'))
        # print('\naccount_values_by_day', self.asset_account_values)
        # print('\nburn_time_by_day', self.burn_time_full)
        # print('\nburn_time_by_day sans investment', self.burn_time_no_invest)
        # print('\naccounts', self.accounts.to_dict('index'))
        # print('\naccount_values_today', self.todays_accounts)
        # print('\naccount_view_order', self.asset_accounts_no_invest)

        return self.render(
            self.template,
            account_values_today=self.todays_accounts,  # Account value dictionary for just today
            account_values_by_day=self.asset_account_values,  # Account value dictionary by day for CanvasJS stacked bar chart
            burn_time_by_day=self.burn_time_full,  # List of dictionaries describing burn time
            burn_time_by_day_no_invest=self.burn_time_no_invest,  # List of dictionaries describing burn time
            burn_time_retirement=include_retire_str,
            account_values_by_transaction=self.account_vals.to_dict('records'),  # Used in table for account value per transaction
            accounts=self.accounts.to_dict('index'),  # Used to translate account_id to name
            account_view_order=self.asset_accounts_no_invest,  # List of account ids, ordered by total value largest to smallest
        )


HOME_PAGE = Home()


@APP.route("/", methods=['GET'])
def get_home():
    return HOME_PAGE.get()
