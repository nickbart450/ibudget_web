import datetime
from budget_data import BudgetData
import os.path
import pandas as pd
import sqlite3 as sql

DATE_FILTERS = {'All': ['2022-12-01', '2024-01-01'],
                    'January': ['2022-12-31', '2023-02-01'],
                    'February': ['2023-02-01', '2023-03-01'],
                    'March': ['2023-03-01', '2023-04-01'],
                    'April': ['2023-04-01', '2023-05-01'],
                    'May': ['2023-05-01', '2023-06-01'],
                    'June': ['2023-06-01', '2023-07-01'],
                    'July': ['2023-07-01', '2023-08-01'],
                    'August': ['2023-08-01', '2023-09-01'],
                    'September': ['2023-09-01', '2023-10-01'],
                    'October': ['2023-10-01', '2023-11-01'],
                    'November': ['2023-11-01', '2023-12-01'],
                    'December': ['2023-12-01', '2024-01-01'],
                    'Q1': ['2022-12-01', '2023-04-01'],
                    'Q2': ['2023-04-01', '2023-07-01'],
                    'Q3': ['2023-07-01', '2023-10-01'],
                    'Q4': ['2023-10-01', '2024-01-01'],
                    }

temps_hi = [50, 55, 63, 72, 79, 86, 89, 88, 81, 72, 62, 53]
temps_lo = [28, 31, 37, 47, 56, 65, 69, 67, 60, 48, 38, 45]

def calc_gas(day):
    month = int(day.month)
    t = temps_lo[month-1]
    delta_t = abs(69-t)
    amount = 35 + (4.5 * delta_t)
    # print('Gas Bill Calc: ', amount)
    return amount

def calc_electric(day):
    month = int(day.month)
    t = temps_hi[month-1]
    delta_t = abs(60-t)
    amount = 65 + (5 * delta_t)
    # print('Electricity Bill Calc: ', amount)
    return amount

amount_calcs = {
    'calc_gas': calc_gas,
    'calc_electric': calc_electric,
                }

def delete_table(database_connector, table_name):
    query = 'DROP TABLE {}'.format(str(table_name))
    database_connector.execute(query)
    database_connector.commit()
    print('table {} deleted'.format(table_name))

def create_transactions(database_connector):
    # dates stored in text as ISO8601 strings ("YYYY-MM-DD HH:MM:SS.SSS")
    # transact_id, transaction_date, post_date, debit_account_id, credit_account_id, category, description, amount, vendor, isPosted
    query = '''CREATE TABLE TRANSACTIONS
               (transaction_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
               transaction_date TEXT NOT NULL,
               posted_date TEXT NOT NULL,
               credit_account_id INTEGER NOT NULL,
               debit_account_id INTEGER NOT NULL,
               category TEXT NOT NULL,
               description TEXT,
               amount REAL NOT NULL,
               vendor TEXT,
               is_posted INTEGER NOT NULL);
            '''
    database_connector.execute(query)
    database_connector.commit()

def create_daily_transactions(args):
    day = datetime.datetime(2023,1,1)

    for i in list(range(365)):
        d = day + datetime.timedelta(days=i)
        c = args['category']
        amount = args['amount']
        if pd.isna(args['vendor']):
            v = ''
        else:
            v = args['vendor']

        DATA.add_transaction(d, c, amount, posted_date=d, credit_account=str(args['credit_account_id']), debit_account=str(args['debit_account_id']), description=args['description'], vendor=v)
        # print('daily adding')

def create_weekly_transactions(args):
    day = datetime.datetime(2023,1,1)

    for i in list(range(365)):
        d = day + datetime.timedelta(days=i)

        if d.strftime('%A') == args['on']:
            c = args['category']

            if pd.isna(args['vendor']):
                v = ''
            else:
                v = args['vendor']

            amount = args['amount']

            DATA.add_transaction(d, c, amount, posted_date=d, credit_account=str(args['credit_account_id']), debit_account=str(args['debit_account_id']), description=args['description'], vendor=v)
            # print('weekly add')

def create_biweekly_transactions(args):
    day = datetime.datetime(2023,1,1)

    if pd.isna(args['starts']):
        start_date = datetime.datetime(2023,1,1)
    else:
        print('using delayed start | ', args['starts'])
        start_date = datetime.datetime(2023, int(args['starts'].split('-')[0]), int(args['starts'].split('-')[1]))

    k = 0
    for i in list(range(365)):
        d = day + datetime.timedelta(days=i)

        if d >= start_date:
            start_flag = True
        else:
            start_flag = False

        if d.strftime('%A') == args['on'] and start_flag:
            k+=1
            if k == 1:
                c = args['category']

                if pd.isna(args['vendor']):
                    v = ''
                else:
                    v = args['vendor']

                amount = args['amount']
                try:
                    amount = float(amount)
                except Exception as e:
                    if 'calculate_credit_card_payment' in amount:
                        amount = amount.split(':')

                        amount = DATA.calculate_credit_card_payment(amount[1], d)
                    else:
                        amount = amount_calcs[amount](d)

                DATA.add_transaction(d, c, amount, posted_date=d, credit_account=str(args['credit_account_id']),
                                     debit_account=str(args['debit_account_id']), description=args['description'],
                                     vendor = v)
                # print('biweekly - adding')
            else:
                k = 0
                pass

def create_monthly_transactions(args):
    day = datetime.datetime(2023,1,1)

    for i in list(range(365)):
        d = day + datetime.timedelta(days=i)

        if int(d.day) == int(args['on']):
            c = args['category']

            a = args['amount']
            try:
                a = float(a)
            except Exception as e:
                a = amount_calcs[a](d)

            if pd.isna(args['vendor']):
                v = ''
            else:
                v = args['vendor']

            DATA.add_transaction(d, c, a, posted_date=d, credit_account=str(args['credit_account_id']), debit_account=str(args['debit_account_id']), description=args['description'], vendor=v)
            # print('monthly add')

def create_annually_transactions(args):
    day = datetime.datetime(2023,1,1)

    date = datetime.datetime(2023, int(args['on'].split('-')[0]), int(args['on'].split('-')[1]))

    for i in list(range(365)):
        d = day + datetime.timedelta(days=i)

        if d == date:
            c = args['category']

            if pd.isna(args['vendor']):
                v = ''
            else:
                v = args['vendor']

            amount = args['amount']

            DATA.add_transaction(d, c, amount, posted_date=d, credit_account=str(args['credit_account_id']), debit_account=str(args['debit_account_id']), description=args['description'], vendor=v)
            # print('Annual add')

def build_2023_transactions(file):
    recurring = pd.read_csv(file)
    frequency = {
        'daily': create_daily_transactions,
        'weekly': create_weekly_transactions,
        'bi-weekly': create_biweekly_transactions,
        'monthly': create_monthly_transactions,
        'annually': create_annually_transactions,
                 }

    for i in recurring.index:
        template = recurring.iloc[i]

        # if template['frequency'] == 'daily':
        #     break
        print('calling: ', frequency[template['frequency']])
        frequency[template['frequency']](template)

def rebuild_transactions():
    delete_table(connection, 'TRANSACTIONS')
    create_transactions(connection)


if __name__ == '__main__':
    # pd.set_option("display.max_rows", None, "display.max_columns", None)

    DATA = BudgetData(DATE_FILTERS)
    DATA.connect('../budget_2023.db')
    connection = DATA.dbConnection

    # -- Delete & Recreate Transactions Table
    # rebuild_transactions()

    # -- Build Transactions Table from Recurring Payments template
    # build_2023_transactions('../table_imports/2023_recurring.csv')

    # -- Read & Output Transactions Table
    # t = DATA.get_transactions()
    # t.sort_values(by=['posted_date', 'transaction_id'], inplace=True)
    # t.to_csv('../2023_transactions.csv')

    # -- Calculate Account Values over time
    STARTING_VALUES_20xx = {'transaction_id': 'start',
                            'transaction_date': 'start',
                            'posted_date': 'start',
                            '0': 0.00,  # External Accounts
                            '100': 2250.00,  # Main Skyla Checking
                            '101': 500.00,  # Main Skyla Savings
                            '102': 15000.00,  # House/Emergency Skyla Savings
                            '103': 1250.00,  # TD Bank Checking
                            '104': 1000.00,  # TD Savings
                            '201': 525.00,
                            '202': 2000.00,
                            '300': 0.00,
                            '4895': 0.00,
                            '5737': 0.00,
                            '9721': 0.00}

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
    a = DATA.calculate_account_values(STARTING_VALUES_2023, append_transaction_details=True)
    a.to_csv('../2023_account_values.csv')

    DATA.close()