from components.config import CONFIG
from budget_app import APP, LOGGER
from budget_data import DATA, fetch_filtered_transactions
from flask import request, render_template, redirect, url_for

CATEGORIES = CONFIG['ui_settings']['categories'].replace('\n', '')
CATEGORIES = CATEGORIES.split(',')

FILTERS = dict(CONFIG['ui_settings.default_filters'])


@APP.route("/transact/", methods=['GET'])
def data_transactions():
    """
    /transact/<arguments>

    :return:
    """
    global FILTERS

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
    result = fetch_filtered_transactions(FILTERS)

    todays_accounts = DATA.calculate_todays_account_values()
    for t in todays_accounts:
        todays_accounts[t] = '$ {:.2f}'.format(todays_accounts[t])

    if result is None or len(result) == 0:
        print('WARNING! No transactions meet current filters. Redirecting back to /transact')
        LOGGER.warning('No transactions meet current filters. Redirecting back to /transact')
        LOGGER.warning('Current Filters: {}'.format(dict(FILTERS)))
        FILTERS = dict(CONFIG['ui_settings.default_filters'])  # reset filters to default and reset page
        return redirect(url_for('data_transactions'))
    elif len(result) > 0:
        result.fillna(value='')
        return render_template(
            'transactions_table.html',
            data=result.to_dict('records'),
            date_filter=date_filters,
            accounts=['All'] + list(DATA.accounts['name']),
            account_values_today=todays_accounts,  # Account value dictionary for just today
            categories=CATEGORIES,
            date_filter_default=FILTERS['date'],
            account_filter_default=FILTERS['account'],
            category_filter_default=FILTERS['category'],
            income_expense_filter_default=FILTERS['income_expense'],
        )
    else:
        # Really unlikely to wind up here, but want to recover safely nonetheless
        LOGGER.error('No transactions meet current filters. Redirecting back to /transact')
        FILTERS = dict(CONFIG['ui_settings.default_filters'])  # reset filters to default and reset page
        return redirect(url_for('data_transactions'))
