import os
import sqlite3 as sql
import pandas as pd
from budget_data import BudgetData
from components import config


# Fetch config
CONFIG = config.CONFIG
environ = CONFIG['env']['environ']

# Create Data object
DATA = BudgetData()
db_file = CONFIG['database.{}'.format(environ)]['file']
DATA.connect(db_file)
connection = DATA.dbConnection


# Tools
def delete_table(database_connector, table_name):
    query = 'DROP TABLE {}'.format(str(table_name))
    database_connector.execute(query)
    database_connector.commit()
    print('table {} deleted'.format(table_name))


def flip_transaction_account(transaction_id):
    """Swaps the credit and debit accounts for the given transaction"""
    q_fetch = '''
        SELECT * FROM TRANSACTIONS
        WHERE transaction_id = {};
        '''.format(transaction_id)

    cursor = DATA.dbConnection.cursor()
    cursor.execute(q_fetch)
    d = list(cursor.fetchone())

    q_insert = '''
        UPDATE TRANSACTIONS
        SET credit_account_id = {0},
            debit_account_id  = {1}
        WHERE transaction_id = {2};
        '''.format(d[4], d[3], transaction_id)
    cursor.execute(q_insert)
    DATA.dbConnection.commit()


def rebuild_transactions():
    FILE = './table_imports/combined_transactions_v6.csv'

    delete_table(connection, 'TRANSACTIONS')
    DATA.create_transactions(connection)
    rows_added = DATA.bulk_import(FILE, 'TRANSACTIONS')
    print(rows_added, ' rows added to TRANSACTIONS')


def add_starting_values_to_accounts(database_connector):
    statement = """
        ALTER TABLE ACCOUNTS
        ADD COLUMN starting_value NUM NOT NULL default 0
    """
    database_connector.execute(statement)
    database_connector.commit()


def update_starting_values_in_accounts(database_connector):
    accounts =  [0,     100,    101,      102,     103, 104, 201,  202, 300,    4895,   5737, 9721]
    values =    [0, 2237.19, 505.13, 12002.95, 1300.06, 500, 520, 1890,   0, -689.77, 101.18,    0]

    for a in range(len(accounts)):
        account_id = accounts[a]
        v = values[a]

        statement = """
            UPDATE accounts
            SET starting_value = {value}
            WHERE account_id = {id};
        """.format(value=v, id=account_id)
        database_connector.execute(statement)
        database_connector.commit()


def add_accounts(database_connector):
    new_accounts = {
        400: {
            'name': 'SHR 401k Retirement',
            'transaction_type': "investment",
            'account_type': "asset",
            'value_0': 28634.73
        },
        401: {
            'name': 'Fidelity Investment',
            'transaction_type': "investment",
            'account_type': "asset",
            'value_0': 2618.06
        },
        402: {
            'name': 'TD Ameritrade',
            'transaction_type': "investment",
            'account_type': "asset",
            'value_0': 3622.04
        },
        403: {
            'name' : 'Electrum Bitcoin Wallet - USD eq.',
            'transaction_type' : "investment",
            'account_type' : "asset",
            'value_0' : 2116.58
        },
    }

    for n in new_accounts:
        query = f'''INSERT INTO ACCOUNTS
                            (account_id,
                            name,
                            transaction_type,
                            account_type,
                            starting_value)
                        VALUES
                            ({int(n)},
                            "{new_accounts[n]['name']}",
                            "{new_accounts[n]['transaction_type']}",
                            "{new_accounts[n]['account_type']}",
                            {new_accounts[n]['value_0']});'''

        print('Executing: {}'.format(query))
        database_connector.execute(query)
        database_connector.commit()

    return None


if __name__ == '__main__':
    # -- Setup
    pd.set_option("display.max_rows", None, "display.max_columns", None, "display.width", 2000)  # makes pandas print full table

    # ----- TABLES -----
    # -- DELETES ALL EXISTING TABLES   ---   !!! CAUTION !!!
    # tables = DATA.quick_query('list_tables')
    # for t in tables:
    #     print('Deleting Table: ', t)
    #     delete_table(connection, t)

    # -- Build tables (TRANSACTIONS/ACCOUNTS)
    # DATA.create_fresh_database(db_file, create_tables=True)

    # -- Rebuilds TRANSACTIONS table (deletes table, recreates table, adds 1/2022-11/2022 data)
    # rebuild_transactions()


    # ----- TRANSACTIONS
    # all_transactions = DATA.get_transactions()
    # print(all_transactions.columns, all_transactions.shape)

    # -- Bulk import transactions
    # file = './table_imports/combined_transactions_v6_rest-of-Dec.csv'
    # DATA.bulk_import(file, 'TRANSACTIONS', date_columns=['transaction_date', 'posted_date'])

    # -- Add single transaction
    # DATA.add_transaction('2022-11-15', 'test', 125.67, debit_account=9721)

    # -- Delete single transaction
    # DATA.delete_transaction(1234)

    # -- Flip single transaction direction
    # flip_transaction_account(1234)

    # -- Transactions save to csv
    # all_transactions = DATA.get_transactions()
    # all_transactions.sort_values(by=['posted_date', 'transaction_id'])
    # all_transactions.to_csv('./2023_transactions.csv')

    # -- Find unique categories
    # unique_data = pd.Series({c: all_transactions[c].unique() for c in all_transactions})
    # print(unique_data['category'])

    # ----- ACCOUNTS -----
    # -- Add starting_values column to database ACCOUNTS table
    # print('Adding starting_values column to ACCOUNTS table in: ', db_file)
    # add_starting_values_to_accounts(connection)
    # update_starting_values_in_accounts(connection)
    print(DATA.accounts)

    # -- Add Accounts
    # add_accounts(connection)
    
    # -- Account Values save to csv
    SHOW_COLS = ['transaction_id',
                 'transaction_date',
                 'Skyla Home/Emergency Savings',
                 'Skyla Checking',
                 'Skyla Main Savings',
                 'Wallet',
                 'Cash Stash',
                 'TD Bank Checking',
                 'TD Bank Savings',
                 ]
    # account_values = DATA.calculate_account_values()  # [SHOW_COLS]
    # account_values.to_csv('./tools/2023_acct_values.csv')


    # ----- TESTS -----
    # - https://github.com/nickbart450/ibudget_web/issues/1#issue-1681295182
    # DATA.delete_transaction(843)
    # DATA.update_transaction(207, amount=23.09)
    # trans = DATA.get_cc_payments(9721)
    # print(trans)


    # ----- OTHER -----
    # -- Calculate CC Payment
    # account = 4895
    # for date in ['2023-01-01', '2023-02-24', '2023-02-28', '2023-12-31']:
    #     print('Acct: {} | Date: {}'.format(account, date))
    #     pay = DATA.calculate_credit_card_payment(account, date)  # Actual date w/ different post date

    # -- Quick Queries
    # print('DATA db tables:\n', DATA.quick_query('list_tables'))
    # print('DATA db accounts:\n', DATA.quick_query('show_all_accounts'))
    # print(DATA.quick_query('show_transactions_dtypes'))

    DATA.close()
