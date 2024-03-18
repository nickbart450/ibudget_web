import pandas as pd
from budget_data import BudgetData
from components import config


if __name__ == "__main__":
    CONFIG = config.CONFIG

    environ = CONFIG['env']['environ']
    DB_FILE = CONFIG['database.{}'.format(environ)]['file']

    DATA = BudgetData()
    DATA.connect(DB_FILE)
    print('Config environment: {}'.format(CONFIG['env']['environ']))

    # help(pd.set_option)
    pd.set_option('display.max_rows', 1000)
    pd.set_option('display.min_rows', 50)
    pd.options.display.width = 0
    pd.set_option('display.max_columns', 30)

    # ------------------------------------------------------------------------------------------
    # 2024-03-17
    # Category Table Creation
    preQ = "DROP TABLE IF EXISTS CATEGORIES"
    DATA.general_query(preQ, commit=True)

    Q = """CREATE TABLE CATEGORIES
        (cat_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, name TEXT UNIQUE, description TEXT);"""
    DATA.general_query(Q, commit=True)

    categories = CONFIG['ui_settings']['categories'].replace('\n', '').split(',')
    for c in categories:
        print(c, '::: ')
        DATA.add_category(c)

    print('CATEGORIES----------------------------------------')
    print(DATA.get_categories())

    # Account Table Updates
    Q1 = """UPDATE accounts
         SET name='Schwab Investment'
         WHERE
         name='TD Ameritrade';"""

    Q2 = """INSERT INTO accounts (account_id, name, transaction_type, account_type)
         VALUES (301, 'Westinghouse Pay Account', 'income', 'revenue');"""

    # Transaction Table Updates
    Q3 = """UPDATE transactions
         SET category='Fuel'
         WHERE
         category='Gas';"""

    Q6 = """UPDATE categories
         SET name='Fuel'
         WHERE
         name='Gas';"""

    Q4 = """UPDATE transactions
         SET category='Mortgage/Rent'
         WHERE
         category='Mortgage';"""

    Q5 = """UPDATE categories
         SET name='Mortgage/Rent'
         WHERE
         name='Mortgage';"""

    # Update sidebar visibility level to hide old accounts
    # Q = """UPDATE accounts
    #     SET sidebar_visible=0
    #     WHERE
    #     account_id=300 OR account_id=301 OR account_id=403 OR account_id=5737 OR account_id=9721;"""

    QUERIES = [Q1, Q2, Q3, Q4, Q5, Q6]
    for q in QUERIES:
        DATA.general_query(q, commit=True)

    print('ACCOUNTS----------------------------------------')
    print(DATA.get_accounts())
    print('UPDATED CATEGORIES----------------------------------------')
    print(DATA.get_categories())

    DATA.close()
