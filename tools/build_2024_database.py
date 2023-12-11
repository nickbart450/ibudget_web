import datetime
from budget_data import BudgetData
import os.path
import pandas as pd
import sqlite3 as sql

DATE_FILTERS = {'All': ['2023-12-31', '2025-01-01'],
                    'January': ['2023-12-31', '2024-02-01'],
                    'February': ['2024-02-01', '2024-03-01'],
                    'March': ['2024-03-01', '2024-04-01'],
                    'April': ['2024-04-01', '2024-05-01'],
                    'May': ['2024-05-01', '2024-06-01'],
                    'June': ['2024-06-01', '2024-07-01'],
                    'July': ['2024-07-01', '2024-08-01'],
                    'August': ['2024-08-01', '2024-09-01'],
                    'September': ['2024-09-01', '2024-10-01'],
                    'October': ['2024-10-01', '2024-11-01'],
                    'November': ['2024-11-01', '2024-12-01'],
                    'December': ['2024-12-01', '2024-01-01'],
                    'Q1': ['2023-12-01', '2024-04-01'],
                    'Q2': ['2024-04-01', '2024-07-01'],
                    'Q3': ['2024-07-01', '2024-10-01'],
                    'Q4': ['2024-10-01', '2025-01-01'],
                    }

temps_hi = [50, 55, 63, 72, 79, 86, 89, 88, 81, 72, 62, 53]
temps_lo = [28, 31, 37, 47, 56, 65, 69, 67, 60, 48, 38, 45]

def calc_gas(day):
    month = int(day.month)
    t = temps_lo[month-1]
    delta_t = abs(69-t)
    amount = 35 + (4.2 * delta_t)
    # print('Gas Bill Calc: ', amount)
    return amount

def calc_electric(day):
    month = int(day.month)
    t = temps_hi[month-1]
    delta_t = abs(60-t)
    amount = 60 + (4.75 * delta_t)
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

def rebuild_transactions():
    delete_table(connection, 'TRANSACTIONS')
    create_transactions(connection)

def create_daily_transactions(args):
    day = datetime.datetime(2024,1,1)

    for i in list(range(365)):
        d = day + datetime.timedelta(days=i)
        c = args['category']
        amount = args['amount']
        if pd.isna(args['vendor']):
            v = ''
        else:
            v = args['vendor']

        DATA.add_transaction(d, c, amount, posted_date=d, credit_account=args['credit_account_id'],
                             debit_account=args['debit_account_id'], description=args['description'], vendor=v)
        print('daily adding')

def create_weekly_transactions(args):
    day = datetime.datetime(2024,1,1)

    for i in list(range(365)):
        d = day + datetime.timedelta(days=i)

        if d.strftime('%A') == args['on']:
            c = args['category']

            if pd.isna(args['vendor']):
                v = ''
            else:
                v = args['vendor']

            amount = args['amount']

            DATA.add_transaction(d, c, amount, posted_date=d, credit_account=args['credit_account_id'],
                                 debit_account=args['debit_account_id'], description=args['description'], vendor=v)
            print('weekly add')

def create_biweekly_transactions(args):
    day = datetime.datetime(2024,1,1)

    if pd.isna(args['starts']):
        start_date = datetime.datetime(2024,1,1)
    else:
        print('using delayed start | ', args['starts'])
        start_date = datetime.datetime(2024, int(args['starts'].split('-')[0]), int(args['starts'].split('-')[1]))

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

                DATA.add_transaction(d, c, amount, posted_date=d, credit_account=args['credit_account_id'],
                                     debit_account=args['debit_account_id'], description=args['description'], vendor=v)
                print('biweekly - adding')
            else:
                k = 0
                pass

def create_monthly_transactions(args):
    day = datetime.datetime(2024,1,1)

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

            DATA.add_transaction(d, c, a, posted_date=d, credit_account=args['credit_account_id'], debit_account=args['debit_account_id'], description=args['description'], vendor=v)
            print('monthly add')

def create_annually_transactions(args):
    day = datetime.datetime(2024,1,1)

    date = datetime.datetime(2024, int(args['on'].split('-')[0]), int(args['on'].split('-')[1]))

    if pd.isna(args['vendor']):
        v = ''
    else:
        v = args['vendor']

    c = args['category']
    amount = args['amount']

    DATA.add_transaction(date, c, amount, posted_date=date, credit_account=args['credit_account_id'],
                         debit_account=args['debit_account_id'], description=args['description'], vendor=v)
    print('Annual add')

def build_2024_transactions(file):
    recurring = pd.read_csv(file)
    print(recurring)
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
        print('calling: ', frequency[template['frequency']], template)
        frequency[template['frequency']](template)


if __name__ == '__main__':
    pd.set_option("display.max_rows", None, "display.max_columns", None)

    DATA = BudgetData()
    DATA.connect('/mnt/Data-x/Documents/1-Financial/2024/budget_2023-2024.db')
    connection = DATA.dbConnection

    # -- Delete & Recreate Transactions Table
    # rebuild_transactions()

    # -- Build Transactions Table from Recurring Payments template
    # build_2024_transactions('/mnt/Data-x/Documents/1-Projects/Code/ibudget_web/table_imports/2024_recurring.csv')

    # -- Read & Output Transactions Table
    t = DATA.get_transactions()
    t.sort_values(by=['posted_date'], inplace=True)
    t.to_csv('./2024_transactions.csv')

    # -- Update Credit Card Payments
    # payments = DATA.get_cc_payments(4895)
    # print(payments)
    # for i in payments.index:
    #     if i >= 674:
    #         amount = DATA.calculate_credit_card_payment(4895, payments.loc[i]['transaction_date'])
    #         DATA.update_transaction(i, amount=amount)

    # -- Calculate Account Values over time
    a = DATA.calculate_account_values(append_transaction_details=True)
    a.to_csv('../2024_account_values.csv')

    DATA.close()
