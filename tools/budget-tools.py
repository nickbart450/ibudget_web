import os
import os.path
os.chdir('../')

import datetime
from budget_data import BudgetData
import budget_server
import config
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

# Tools
def create_fresh_database(filepath, create_tables=False):
    # file = "./budget_example.db"
    file = filepath

    try:
        conn = sql.connect(file)
        print("Database formed at: {}".format(os.path.abspath(file)))
        if create_tables:
            create_transactions(conn)
            create_accounts(conn)
    except:
        print("Database not formed")


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


def create_accounts(database_connector):
    # dates stored in text as ISO8601 strings ("YYYY-MM-DD HH:MM:SS.SSS")
    # transact_id, transaction_date, post_date, debit_account_id, credit_account_id, category, description, amount, vendor, isPosted
    query = '''CREATE TABLE ACCOUNTS
               (account_id INTEGER PRIMARY KEY NOT NULL,
               name TEXT NOT NULL,
               transaction_type TEXT NOT NULL,
               account_type TEXT NOT NULL
               );
            '''
    database_connector.execute(query)
    database_connector.commit()


def bulk_import(file, table, convert_date_columns=False):
    if convert_date_columns:
        rows_altered = DATA.bulk_import(file, table, date_columns=['transaction_date', 'posted_date'])
    else:
        rows_altered = DATA.bulk_import(file, table)
    return rows_altered


def flip_transaction_account(transaction_id):
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
    create_transactions(connection)
    rows_added = bulk_import(FILE, 'TRANSACTIONS', convert_date_columns=True)
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


if __name__ == '__main__':
    # -- Setup
    # pd.set_option("display.max_rows", None, "display.max_columns", None)  # makes pandas print full table

    # Fetch config
    CONFIG = config.CONFIG
    environ = CONFIG['env']['environ']

    # Create Data object
    DATA = BudgetData()
    db_file_ = CONFIG['database.{}'.format(environ)]['file']
    DATA.connect(db_file_)
    connection = DATA.dbConnection

    # -- Add starting_values column to database ACCOUNTS table
    # print('Adding starting_values column to ACCOUNTS table in: ', db_file_)
    # add_starting_values_to_accounts(connection)
    # update_starting_values_in_accounts(connection)

    # -- Calculate CC Payment
    # pay = DATA.calculate_credit_card_payment(4895, '2023-02-09')
    # print('Payment: ', pay)


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
    STARTING_VALUES_2022 = {'transaction_id': 'start',
                       'transaction_date': 'start',
                       'posted_date': 'start',
                       '0': 0.00,  # External Accounts
                       '100': 2152.98,  # Main Skyla Checking
                       '101': 1005.00,  # Main Skyla Savings
                       '102': 14000.00,  # House/Emergency Skyla Savings
                       '103': 1480.00,  # TD Bank Checking
                       '104': 500.00,  # TD Savings
                       '201': 130.00,
                       '202': 2700.00,
                       '300': 0.00,
                       '4895': 0.00,
                       '5737': 0.00,
                       '9721': 0.00,
                       # 'Retirement'     : 0.00,
                       # 'Fidelity'       : 15000.00,
                       # 'TD Ameritrade'  : 0.00,
                       # 'Electrum Wallet': 0.135,
                       # 'Binance'        : 0.00,
                       # 'FTX'            : 0.00,
                       }
    # account_values = DATA.calculate_account_values(STARTING_VALUES_2022, date_filter='All')  # [SHOW_COLS]
    # account_values.to_csv('./2022_acct_values.csv')

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
    # vals = DATA.calculate_account_values(STARTING_VALUES_2023)
    # vals.to_csv('./2023_account_values.csv')


    # -- Transactions save to csv
    # all_transactions = DATA.get_transactions()
    # all_transactions.sort_values(by=['posted_date', 'transaction_id'])
    # all_transactions.to_csv('./2023_transactions.csv')


    # -- DELETES ALL EXISTING TABLES   ---   !!! CAUTION !!!
    # for t in tables:
    #     print('Deleting Table: ', t)
    #     delete_table(connection, t)

    # -- Build tables (TRANSACTIONS/ACCOUNTS)
    # create_transactions(connection)
    # create_accounts(connection)


    # -- Rebuilds TRANSACTIONS table (deletes table, recreates table, adds 1/2022-11/2022 data)
    # rebuild_transactions()


    # -- Bulk import transactions
    # file = './table_imports/combined_transactions_v6_rest-of-Dec.csv'
    # DATA.bulk_import(file, 'TRANSACTIONS', date_columns=['transaction_date', 'posted_date'])


    # -- Quick Queries
    print('DATA db tables:\n', DATA.quick_query('list_tables'))
    print('DATA db accounts:\n', DATA.quick_query('show_all_accounts'))
    # print(DATA.quick_query('show_transactions_dtypes'))


    # -- Flip single transaction direction
    # flip_transaction_account(729)


    # -- Add single transaction
    # DATA.add_transaction('2022-11-15', 'test', 125.67, debit_account=9721)


    # -- Delete single transaction
    # DATA.delete_transaction(676)


    # -- Custom SQL queries
    add_to_accounts_query = '''INSERT INTO ACCOUNTS
                        (account_id,
                        name,
                        transaction_type,
                        account_type,
                        )
                    VALUES
                        ({account_id},
                        '{name}',
                        '{transaction_type}',
                        '{account_type}',
                        );'''.format(account_id=1, name='test', transaction_type='cash', account_type='other')

    # update_accounts_query = """UPDATE TRANSACTIONS
    #                             SET
    #                                 amount=1907.70
    #                             WHERE
    #                                 category='Job Pay'
    #                             AND
    #                                 is_posted=0
    #                         """
    # cursor = DATA.dbConnection.cursor()
    # cursor.execute(update_accounts_query)
    # DATA.dbConnection.commit()

    DATA.close()
