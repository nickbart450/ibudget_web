from components.config import CONFIG
from budget_app import APP, LOGGER
from budget_data import DATA
from flask import render_template


@APP.route("/", methods=['GET'])
def get_home():
    """
    Home page

    :return:
    """
    print('Fetching HOME')
    result = DATA.calculate_account_values()

    accounts = DATA.get_accounts().set_index('account_id', drop=False)
    accounts.index = accounts.index.astype(str)
    asset_accounts = accounts.loc[accounts['account_type'] == 'asset']
    asset_accounts_no_invest = asset_accounts.loc[asset_accounts['transaction_type'] != 'investment']

    # Fetch today's account values from data object
    todays_accounts = DATA.calculate_todays_account_values()
    for t in todays_accounts:
        todays_accounts[t] = '$ {:.2f}'.format(todays_accounts[t])

    # Loop through the account values dataframe to calculate and construct CanvasJS dictionaries
    prev_date = 19700101
    asset_account_values = {}
    for a in list(asset_accounts.index):
        asset_account_values[str(a)] = []
    burn_time_full = []
    burn_time_no_invest = []
    for i in result.index:
        date = int(result.iloc[i]['transaction_date'].strftime('%Y%m%d'))

        if date == prev_date:
            pass
        else:
            account_sum = 0
            account_sum_no_invest = 0
            for acc in list(asset_accounts.index):
                if '401k' in accounts.at[acc, 'name']:
                    # pre-tax money gets adjusted here
                    y = float(result.at[i, str(acc)])*(1-float(CONFIG['personal']['retirement_tax_rate']))
                else:
                    y = result.at[i, str(acc)]

                label = result.at[i, 'transaction_date'].strftime('%Y-%m-%d')
                asset_account_values[str(acc)].append(
                    {"y": y,
                     "label": label}
                )
                account_sum += y

            for acc in list(asset_accounts_no_invest.index):
                account_sum_no_invest += float(result.at[i, str(acc)])

            # Assemble Burn Time CanvasJS Line chart
            y = result.at[i, 'transaction_date'].year
            m = result.at[i, 'transaction_date'].month
            d = result.at[i, 'transaction_date'].day

            monthly_expense = float(CONFIG['personal']['average_monthly_expend'])
            b_full = round(account_sum/monthly_expense, 2)
            burn_time_full.append({"year": y, "month": m, "day": d, "burn": b_full})

            b_part = round(account_sum_no_invest/monthly_expense, 2)
            burn_time_no_invest.append({"year": y, "month": m, "day": d, "burn": b_part})

            prev_date = date

    # Sort accounts for stacked chart
    account_order = [(i, sum(result[i])) for i in list(asset_account_values.keys())]
    account_sums = sorted([i[1] for i in account_order], reverse=True)
    account_view_reorder = []
    for x in range(len(account_sums)):
        for y in account_order:
            if y[1] == account_sums[x]:
                account_view_reorder.append(y[0])

    asset_accounts_no_invest = [i for i in account_view_reorder if i in list(asset_accounts_no_invest.index)]

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

    # print('\nHOME page returns - ')
    # print('\naccount_values_by_transaction', result.to_dict('records'))
    # print('\naccount_values_by_day', asset_account_values)
    # print('\nburn_time_by_day', burn_time_full)
    # print('\nburn_time_by_day sans investment', burn_time_no_invest)
    # print('\naccounts', accounts.to_dict('index'))
    # print('\naccount_values_today', todays_accounts)
    # print('\naccount_view_order', asset_accounts_no_invest)

    return render_template(
        'index.html',
        account_values_by_day=asset_account_values,  # Account value dictionary by day for CanvasJS stacked bar chart
        burn_time_by_day=burn_time_full,  # List of dictionaries describing burn time
        burn_time_by_day_no_invest=burn_time_no_invest,  # List of dictionaries describing burn time
        account_values_by_transaction=result.to_dict('records'),  # Used in table for account value per transaction
        accounts=accounts.to_dict('index'),  # Used to translate account_id to name
        account_values_today=todays_accounts,  # Account value dictionary for just today
        account_view_order=asset_accounts_no_invest,  # List of account ids, ordered by total value largest to smallest
    )
