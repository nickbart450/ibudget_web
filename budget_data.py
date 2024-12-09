# budget_data.py
__version__ = '0.1.1'

import os.path
ROOT = os.path.dirname(os.path.realpath(__file__))
os.chdir(ROOT)


import warnings
import datetime
import pandas as pd
import sqlite3 as sql
import logging
from components import config

QUERIES = {'show_transactions_dtypes': '''PRAGMA table_info(TRANSACTIONS);''',
           'show_all_transactions': '''SELECT * from TRANSACTIONS''',
           'show_all_accounts': '''SELECT * from ACCOUNTS''',
           'list_tables': '''SELECT
                      name
                  FROM
                      sqlite_schema
                  WHERE
                      type ='table' AND
                      name NOT LIKE 'sqlite_%';''',
           }

TRANSACTION_TABLE_COLS = ['transaction_id',
                          'transaction_date',
                          'posted_date',
                          'credit_account_id',
                          'debit_account_id',
                          'category',
                          'description',
                          'amount',
                          'vendor',
                          'is_posted']


class BudgetData:
    """
    Default date filters are 2024
    """

    def __init__(self, app_config):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('budget_data -- DEBUG LOGGING MODE')
        self.logger.info('budget_data -- INFO LOGGING MODE')

        # Load config settings
        self.config = app_config

        # Parse date filters from config
        self.year = None
        self.default_year = 2024
        self.date_filters = self.parse_date_filters()

        # Initialize empty vars
        self.dbConnection = None
        self.dbConnected = False
        self.db_version = None
        self.connection_attempts = 0

        self.transactions = None
        self.accounts = None
        self.account_values = None
        self.categories = None

    def __del__(self):
        self.close()

    def connect(self, db_file):
        print('connecting to {}'.format(db_file))
        self.logger.info('Connecting to SQLite3 db at: {}'.format(db_file))
        self.logger.debug('db SQL version: {}'.format(self.db_version))

        self.connection_attempts += 1
        try:
            if os.path.exists(os.path.abspath(db_file)):
                self.logger.info('Attempting to open {}'.format(os.path.abspath(db_file)))
                self.dbConnection = sql.connect(db_file, check_same_thread=False)
                test_query = 'SELECT sqlite_version();'
                test_cursor = self.dbConnection.cursor()
                self.db_version = test_cursor.execute(test_query).fetchall()[0]
                self.dbConnected = True
                print('Successfully Connected')
                self.logger.info('Successfully Connected')
            elif os.path.exists(os.path.abspath('./budget_example.db')):
                self.logger.debug(
                    'Primary connection failed, attempting to open {}'.format(os.path.abspath('./budget_example.db')))
                self.dbConnection = sql.connect('./budget_example.db', check_same_thread=False)
                test_query = 'SELECT sqlite_version();'
                test_cursor = self.dbConnection.cursor()
                self.db_version = test_cursor.execute(test_query).fetchall()[0]
                self.dbConnected = True
                print('Successfully Connected to Example db')
                self.logger.info('Successfully Connected to Example db')
            else:
                print('Database connection issues. Attempting creation of blank db...')
                if self.connection_attempts <= 5:
                    self.logger.warning(
                        'No database file found, attempting to create fresh, empty database at {}'.format(
                            os.path.abspath('./iBudget_web.db')))

                    # Build new database file with appropriate tables to make app work
                    self.create_fresh_database(os.path.abspath('./iBudget_web.db'), create_tables=True)

                    # Update config file to reference new database file on subsequent launches
                    # Overwrites config.ini file location with new database file
                    env = self.config['env']['environ']
                    self.config['database.{}'.format(env)]['file'] = os.path.abspath('./iBudget_web.db')
                    self.config.remove_section('env')

                    # with open(config.main_config_file, 'w') as f:
                    #     self.config.write(f)
                    self.config.write_out_config()

                    self.config.add_section('env')
                    self.config.set('env', 'environ', env)

                    # Reattempt connection to new file
                    self.connect('./iBudget_web.db')
                else:
                    self.logger.warning('attempted db connection/creation 5 times, quitting')
                    self.dbConnected = False
                    return False

            if self.dbConnected:
                self.get_transactions()
                return True
            else:
                return False

        # Handle errors
        except sql.Error as e:
            self.logger.warning('Failed db connection/creation with error: {}'.format(e))
            self.dbConnected = False
            return None

    def close(self):
        if self.dbConnected:
            self.dbConnection.close()
            self.dbConnected = False
            # print('SQLite Connection closed')
            self.logger.info('SQLite Connection closed')
        else:
            # print('No SQLite Connection to close')
            self.logger.info('No SQLite Connection to close')
        return None

    def get_accounts(self):
        """Returns a pandas dataframe version of the database table. Index is account_id."""
        if not self.dbConnected:
            raise RuntimeError('database not connected')

        self.dbConnection.row_factory = sql.Row  # Sets the direction of returned data to work with pd.from_dict
        accounts = self.dbConnection.cursor().execute('''SELECT * FROM ACCOUNTS''').fetchall()
        account_table = pd.DataFrame([dict(row) for row in accounts])

        account_table = account_table.set_index('account_id', drop=False)
        self.accounts = account_table
        return account_table

    def add_account(self, name, account_type, transaction_type, account_id='', starting_value=0):
        """
        account_type examples: asset, liability, revenue, other
        transaction_type examples: external, bank, cash, income,  investment, credit_line, credit_card
        """

        print('adding account')
        if account_id != '':
            print('account_id check:', self.account_id_unique_check(account_id))

        # if name == '' or account_type == '' or transaction_type == '':

        subquery_1 = "name, account_type, transaction_type"
        subquery_2 = "'{name}', '{account_type}', '{transaction_type}'"
        values_dict = {
            'name': str(name),
            'account_type': str(account_type),
            'transaction_type': str(transaction_type)
        }

        if account_id != '':
            subquery_1 += ", account_id"
            subquery_2 += ", {account_id}"
            values_dict['account_id'] = int(account_id)

        query = """INSERT INTO accounts ({})
             VALUES ({});""".format(subquery_1, subquery_2.format(**values_dict))

        print(query)
        self.logger.debug('add_category query:\n{}'.format(query))

        # Execute query and commit to db
        cursor = self.dbConnection.cursor()
        cursor.execute(query)
        self.dbConnection.commit()

        account_id = cursor.lastrowid

        print('added account to db:')
        print('\taccount_id: ', account_id)
        print('\tname: ', name)
        print('\ttransaction_type: ', transaction_type)
        print('\taccount_type: ', account_type)
        print('\tstarting_value: ', starting_value)

        # Refresh category table
        self.get_accounts()

        return account_id

    def update_account(self, old_id, account_id=None, name=None, account_type=None, transaction_type=None, starting_value=None):
        loc = locals().copy()

        old_id = int(old_id)

        accounts = self.get_accounts()
        account = accounts[accounts['account_id'] == old_id].T.squeeze().to_dict()
        # print('account update data:', accounts)

        if account_id is not None and account_id != '':
            account['account_id'] = int(account_id)
        else:
            self.logger.exception('Account ID cannot be None. Please specify account_id before proceeding.')
            return 'ERROR - Account ID cannot be None. Please specify account_id before proceeding.'

        params = ()
        columns = []
        for key in loc:
            if key == 'self' or key == 'old_id':
                continue

            # print(key, loc[key])

            if key is not None and key != 'None':
                if key == '':
                    account[key] = None
                else:
                    account[key] = loc[key]

                columns.append(key)
                params = params + (account[key],)

        q_update = """
            UPDATE ACCOUNTS
            SET {}=?
            WHERE account_id = {};""".format('=?, '.join(columns), old_id)

        # print(q_update)
        # print(params)

        self.logger.debug('update_transaction query:\n{}'.format(q_update))
        self.logger.debug('update_transaction params:\n{}'.format(params))

        cursor = self.dbConnection.cursor()
        cursor.execute(q_update, params)
        self.dbConnection.commit()

        print('Updated account in db:')
        print('\taccount_id - OLD: ', old_id)
        print('\taccount_id - NEW: ', account['account_id'])
        print('\tname: ', account['name'])
        print('\taccount_type: ', account['account_type'])
        print('\ttransaction_type: ', account['transaction_type'])
        print('\tstarting_value: ', account['starting_value'])

        # Refresh account table
        self.get_accounts()

        return 'Success'

    def delete_account(self, account_id):
        account_id = int(account_id)

        # Commit deletion to database
        self.logger.info('Deleting Account: {}'.format(account_id))
        query = '''DELETE FROM ACCOUNTS
                WHERE account_id={};'''.format(account_id)
        cursor = self.dbConnection.cursor()
        cursor.execute(query)
        self.dbConnection.commit()

        self.get_accounts()  # Refresh accounts table
        return None

    def account_id_unique_check(self, account_id):
        current_ids = self.get_accounts()['account_id'].to_list()
        return account_id in current_ids

    def get_categories(self):
        """Returns a pandas dataframe version of the database table. Index is cat_id."""
        if not self.dbConnected:
            raise RuntimeError('database not connected')

        self.dbConnection.row_factory = sql.Row  # Sets the direction of returned data to work with pd.from_dict
        categories = self.dbConnection.cursor().execute('''SELECT * FROM CATEGORIES''').fetchall()
        category_table = pd.DataFrame([dict(row) for row in categories])

        # category_table = category_table.set_index('cat_id', drop=False)
        self.categories = category_table
        return category_table

    def add_category(self, name, cat_id='', description=''):
        subquery_1 = "(name)"
        subquery_2 = "('{name}')"
        values_dict = {'name': str(name)}

        if cat_id != '' and description != '':
            subquery_1 = "(cat_id, name, description)"
            subquery_2 = "('{cat_id}', '{name}', '{description}')"

            values_dict['cat_id'] = int(cat_id)
            values_dict['description'] = str(description)

        elif cat_id != '' and description == '':
            subquery_1 = "(cat_id, name)"
            subquery_2 = "('{cat_id}', '{name}')"

            values_dict['cat_id'] = int(cat_id)

        elif cat_id == '' and description != '':
            subquery_1 = "(name, description)"
            subquery_2 = "('{name}', '{description}')"

            values_dict['description'] = str(description)

        query = '''INSERT INTO CATEGORIES {}
                VALUES {};'''.format(subquery_1, subquery_2.format(**values_dict))

        self.logger.debug('add_category query:\n{}'.format(query))

        # Execute query and commit to db
        cursor = self.dbConnection.cursor()
        cursor.execute(query)
        self.dbConnection.commit()

        category_id = cursor.lastrowid

        print('added category to db:')
        print('\tcategory_id: ', category_id)
        print('\tname: ', name)
        print('\tdescription: ', description)

        # Refresh category table
        self.get_categories()

        return category_id

    def update_category(self, old_id, cat_id=None, name=None, description=None):
        old_id = int(old_id)

        categories = self.get_categories()
        category = categories[categories['cat_id'] == old_id].T.squeeze().to_dict()
        # print('category update data:', category)

        if cat_id is not None and cat_id != '':
            category['cat_id'] = int(cat_id)
        else:
            self.logger.exception('Category ID cannot be None. Please specify cat_id before proceeding.')
            return "ERROR - Category ID cannot be None. Please specify cat_id before proceeding."

        if name is not None and name != 'None':
            if name == '':
                category['name'] = None
            else:
                category['name'] = str(name)

        if description is not None and description != 'None':
            if description == '':
                category['description'] = None
            else:
                category['description'] = str(description)

        q_update = """
            UPDATE CATEGORIES
            SET name=?, description=?
            WHERE cat_id = {};""".format(old_id)
        params = (category['name'], category['description'])

        if cat_id != old_id:
            q_update = """
                UPDATE CATEGORIES
                SET cat_id = ?, name = ?, description = ?
                WHERE cat_id = {};""".format(old_id)
            params = (category['cat_id'], category['name'], category['description'])

        self.logger.debug('update_transaction query:\n{}'.format(q_update))
        self.logger.debug('update_transaction params:\n{}'.format(params))

        cursor = self.dbConnection.cursor()
        cursor.execute(q_update, params)
        self.dbConnection.commit()

        print('Updated category in db:')
        print('\tcategory_id - OLD: ', old_id)
        print('\tcategory_id - NEW: ', category['cat_id'])
        print('\tname: ', category['name'])
        print('\tdescription: ', category['description'])

        # Refresh category table
        self.get_categories()

        return 'Success'

    def delete_category(self, category_id):
        category_id = int(category_id)

        # Commit deletion to database
        self.logger.info('Deleting Category: {}'.format(category_id))
        query = '''DELETE FROM CATEGORIES
                WHERE cat_id={};'''.format(category_id)
        cursor = self.dbConnection.cursor()
        cursor.execute(query)
        self.dbConnection.commit()

        self.get_categories()  # Refresh categories table
        return None

    def get_transactions(self, date_filter=None, start_date=None, end_date=None, date_type='transaction_date',
                         account_filter='All', expense_income_filter='both', category_filter='All',
                         append_total=False):  # alternative date_type: posted_date
        """ Can provide either filter code string (ex. 'January', 'Q3') defined by date_filters dict
                            OR  start and end dates of format 'YYYY-mm-dd'
        """

        query = """SELECT * from TRANSACTIONS
                   {fill}
                   ORDER BY transaction_date ASC;
                """

        # Query Database, Filtering by Date - other filters handled on the dataframe after
        if date_filter == 'Date Filter' or date_filter == 'All':
            date_filter = 'all'

        if date_filter == 'all' and self.year is not None:
            # If self.year is set to reduce transmitted data, alter input 'all' to selected year only
            # print('get_transactions - overriding date_filter to', self.year)
            years = {2023: 'all_23',
                     2024: 'all_24'}
            date_filter = years[self.year]

        # else:
        #     print('get_transactions no year override')

        if date_filter is not None:
            date_filter = date_filter.lower()
            d1 = self.date_filters[date_filter][0]
            d2 = self.date_filters[date_filter][1]
            query = query.format(fill="""WHERE {0} BETWEEN '{1} 00:00:00' AND '{2} 00:00:00'""")
            query = query.format(date_type, d1, d2)
        elif start_date is not None or end_date is not None:
            if start_date is None:
                d1 = '1970-01-01'
                d2 = end_date
            elif end_date is None:
                d1 = start_date
                d2 = '2100-12-31'
            else:
                d1 = start_date
                d2 = end_date
            query = query.format(fill="""WHERE {0} BETWEEN '{1} 00:00:00' AND '{2} 00:00:00'""")
            query = query.format(date_type, d1, d2)
        else:
            query = query.format(fill='')
            # raise Exception("Please provide date range or filter code")

        date_cols = ['transaction_date', 'posted_date']
        df = pd.read_sql(query, self.dbConnection, parse_dates=date_cols)

        # Account Filter
        accounts = self.get_accounts()
        if account_filter == 'All' or account_filter == 'Account Filter':
            account = list(accounts['account_id'])
        elif isinstance(account_filter, int) and account_filter in list(accounts['account_id']):
            account = [account_filter]
        else:
            account = [int(accounts[accounts['name'] == account_filter]['account_id'])]

        debit_truth_series = []
        for i in df.index:
            if df.at[i, 'debit_account_id'] in account:
                debit_truth_series.append(True)
            else:
                debit_truth_series.append(False)

        credit_truth_series = []
        for i in df.index:
            if df.at[i, 'credit_account_id'] in account:
                credit_truth_series.append(True)
            else:
                credit_truth_series.append(False)

        joint_truth_series = []
        for i in list(range(len(debit_truth_series))):
            if debit_truth_series[i]:
                joint_truth_series.append(True)
            elif credit_truth_series[i]:
                joint_truth_series.append(True)
            else:
                joint_truth_series.append(False)

        df = df[joint_truth_series]

        # Expense/Income Filter
        if expense_income_filter == 'expenses':
            df = df[df['debit_account_id'] == 0]

        elif expense_income_filter == 'income':
            df = pd.concat([df[df['credit_account_id'] == 0], df[df['credit_account_id'] == 300]])

        # Category filter
        if category_filter != 'All' and category_filter is not None:
            df = df[df['category'] == str(category_filter)]

        # Append Total
        if append_total:
            col_names = ['amount']
            df = self.append_total(df, col_names)
            df.fillna('', inplace=True)

        if len(df) == 0:
            return None
        else:
            df = df.set_index('transaction_id', drop=False)  # Keeping transaction_id column for legacy compatibility
            self.transactions = df
            return df

    def bulk_import(self, file, table, date_columns=False):
        # Load data from csv
        df = pd.read_csv(file, encoding="ISO-8859-1")

        # Convert date columns to proper dtype
        if date_columns:
            for date_col in date_columns:
                df[date_col] = pd.to_datetime(df[date_col])  # , format="%Y-%m-%d"
        else:
            print('no date column conversion')
            self.logger.debug('no date column conversion')

        # Add data to sqlite db
        rows_changed = df.to_sql(table, self.dbConnection, schema='budget', if_exists='append', index=False)
        self.dbConnection.commit()
        return rows_changed

    def add_transaction(self, transaction_date, category, amount, posted_date=False, credit_account=False,
                        debit_account=False, description=None, vendor=None, is_posted=False):
        transaction_date = pd.to_datetime(transaction_date)

        # handle post date
        if posted_date:
            posted_date = pd.to_datetime(posted_date)
        else:
            posted_date = pd.to_datetime(transaction_date) + pd.Timedelta(days=2)

        # handle accounts
        if credit_account and debit_account:
            if credit_account == debit_account:
                raise RuntimeError('debit_account must be different from credit_account')
            else:
                pass

        elif credit_account and not debit_account:
            self.logger.info('credit_account ONLY provided')
            debit_account = 0
        elif debit_account and not credit_account:
            self.logger.info('debit_account ONLY provided')
            credit_account = 0
        else:
            raise RuntimeError('Please specify at least one account as debit_account or credit_account')

        # convert is_posted
        if is_posted:
            is_posted = 1
        else:
            is_posted = 0

        if description is None:
            description = ''

        query = '''INSERT INTO TRANSACTIONS
                    (transaction_date,
                    posted_date,
                    credit_account_id,
                    debit_account_id,
                    category,
                    description,
                    amount,
                    vendor,
                    is_posted)
                VALUES
                    ("{t_date}",
                    "{p_date}",
                    {c_account_id},
                    {d_account_id},
                    "{category}",
                    "{description}",
                    {amount},
                    "{vendor}",
                    {is_posted});'''.format(
            t_date=transaction_date,
            p_date=posted_date,
            c_account_id=int(credit_account),
            d_account_id=int(debit_account),
            category=category,
            description=description,
            amount=amount,
            vendor=vendor,
            is_posted=is_posted,
        )
        self.logger.debug('add_transaction query:\n{}'.format(query))

        # Execute query and commit to db
        cursor = self.dbConnection.cursor()
        cursor.execute(query)
        self.dbConnection.commit()

        transaction_id = cursor.lastrowid

        print('added transaction to db:')
        print('\ttransaction_id: ', transaction_id)
        print('\ttransaction_date: ', transaction_date)
        # print('\tposted_date: ', posted_date)
        # print('\tcredit_account: ', credit_account)
        # print('\tdebit_account: ', debit_account)
        # print('\tamount: ', amount)
        print('\tcategory: ', category)
        print('\tdescription: ', description)
        # print('\tvendor: ', vendor)
        # print('\tposted_flag: ', is_posted)

        # Refresh transaction table
        self.get_transactions()

        # Determine CC update necessity
        transaction_id = cursor.lastrowid
        accounts = self.accounts.set_index('account_id')
        credit_account_type = accounts.at[credit_account, 'transaction_type']
        debit_account_type = accounts.at[debit_account, 'transaction_type']

        # Check account types
        account_type_checks = [credit_account_type, debit_account_type]
        if 'credit_card' in account_type_checks:
            self.update_credit_card_payment(transaction_id)

        return transaction_id

    def update_transaction(self, transaction_id, transaction_date=None, posted_date=None, category=None, amount=None,
                           credit_account=None, debit_account=None, description=None, vendor=None, is_posted=None):
        """
        Updates provided values for specific transaction_id

        :param transaction_id:    required
        :param transaction_date:
        :param category:
        :param amount:
        :param posted_date:
        :param credit_account:
        :param debit_account:
        :param description:
        :param vendor:
        :param is_posted:
        :return:
        """
        # Get current transaction details
        transaction = self.get_transaction(self.dbConnection, int(transaction_id))

        # Fetch the latest accounts table and store previous account types before updating transaction
        accounts = self.get_accounts().set_index('account_id')

        # Convert account name inputs to id #s
        if credit_account is not None:
            credit_account = int(accounts[accounts['name'] == credit_account].index.values[0])
        if debit_account is not None:
            debit_account = int(accounts[accounts['name'] == debit_account].index.values[0])

        # Check for duplicate accounts
        if credit_account is not None and debit_account is not None and credit_account == debit_account:
            raise RuntimeError('debit_account must be different from credit_account')

        # Store account types from old transaction to monitor changes
        old_credit_account_type = accounts.at[int(transaction['credit_account_id']), 'transaction_type']
        old_debit_account_type = accounts.at[int(transaction['debit_account_id']), 'transaction_type']
        credit_account_type = old_credit_account_type
        debit_account_type = old_debit_account_type

        # If the account is changing, store both accounts to recalculate any relevant credit card payments
        recalc_accounts = []
        if credit_account is not None and credit_account != int(transaction['credit_account_id']):
            recalc_accounts.append(credit_account)
            recalc_accounts.append(int(transaction['credit_account_id']))

            transaction['credit_account_id'] = credit_account

            credit_account_type = accounts.at[transaction['credit_account_id'], 'transaction_type']
        else:
            pass
            # print('\tno change to credit account')

        if debit_account is not None and debit_account != int(transaction['debit_account_id']):
            recalc_accounts.append(debit_account)
            recalc_accounts.append(int(transaction['debit_account_id']))

            transaction['debit_account_id'] = debit_account

            debit_account_type = accounts.at[transaction['debit_account_id'], 'transaction_type']
        else:
            pass
            # print('\tno change debit account')
        recalc_accounts = list(set(recalc_accounts))

        # Handle inputs
        if transaction_date is not None:
            transaction['transaction_date'] = pd.to_datetime(transaction_date)

        if posted_date is not None:
            transaction['posted_date'] = pd.to_datetime(posted_date)

        if category is not None:
            transaction['category'] = category

        if amount is not None:
            transaction['amount'] = amount

        if description is not None:
            transaction['description'] = description

        if vendor is not None:
            transaction['vendor'] = vendor

        # convert is_posted
        if is_posted is not None:
            if is_posted:
                transaction['is_posted'] = 1
            else:
                transaction['is_posted'] = 0

        print('Updating transaction:')
        print('\ttransaction_id:..... ', transaction_id)
        print('\ttransaction_date:... ', transaction['transaction_date'])
        # print('\tposted_date:........ ', transaction['posted_date'])
        print('\tcredit_account:..... ', transaction['credit_account_id'])
        print('\tdebit_account:...... ', transaction['debit_account_id'])
        print('\tcategory:........... ', transaction['category'])
        print('\tdescription:........ ', transaction['description'])
        print('\tamount:.............  ${:.2f}'.format(float(transaction['amount'])))
        # print('\tvendor:............. ', transaction['vendor'])
        # print('\tposted_flag:........ ', transaction['is_posted'])

        q_update = """
            UPDATE TRANSACTIONS
            SET transaction_date = "{t_date}",
                posted_date = "{p_date}",
                credit_account_id = {c_account_id},
                debit_account_id = {d_account_id},
                category = "{category}",
                description = "{description}",
                amount = {amount},
                vendor = "{vendor}",
                is_posted = {is_posted}
            WHERE transaction_id = {transaction_id};""".format(
            t_date=transaction['transaction_date'],
            p_date=transaction['posted_date'],
            c_account_id=transaction['credit_account_id'],
            d_account_id=transaction['debit_account_id'],
            category=transaction['category'],
            description=transaction['description'],
            amount=transaction['amount'],
            vendor=transaction['vendor'],
            is_posted=transaction['is_posted'],
            transaction_id=transaction_id,
        )
        self.logger.debug('update_transaction query:\n{}'.format(q_update))

        cursor = self.dbConnection.cursor()
        cursor.execute(q_update)
        self.dbConnection.commit()

        self.get_transactions()  # Refresh transaction table

        # Check for CC accounts in transaction and update relevant payments
        # print('credit_account_type OLD/NEW {}/{}'.format(str(old_credit_account_type), str(credit_account_type)))
        # print('debit_account_type OLD/NEW {}/{}'.format(str(old_debit_account_type), str(debit_account_type)))
        account_type_checks = [credit_account_type, old_credit_account_type, debit_account_type, old_debit_account_type]
        cc_accounts = accounts.loc[accounts['transaction_type'] == 'credit_card']
        if len(recalc_accounts) > 0:
            for a in recalc_accounts:
                if a in list(cc_accounts.index):
                    c = recalc_accounts.index(a)
                    tot = len(recalc_accounts)
                    print('Recalculating Credit Card Payment from update_transaction {}/{}'.format(c + 1, tot))
                    self.update_credit_card_payment(transaction_id, account=a)
        elif 'credit_card' in account_type_checks and transaction['category'] != 'Credit Card Payment':
            self.update_credit_card_payment(transaction_id)

        return None

    def delete_transaction(self, transaction_id):
        transaction_id = int(transaction_id)

        # First set amount to 0 and recalculate CC transaction, if required.
        self.update_transaction(transaction_id, amount=0)

        # Then commit deletion to database
        self.logger.info('Deleting Transaction: {}'.format(transaction_id))
        query = '''DELETE FROM TRANSACTIONS
                WHERE transaction_id={};'''.format(transaction_id)
        cursor = self.dbConnection.cursor()
        cursor.execute(query)
        self.dbConnection.commit()

        self.get_transactions()  # Refresh transaction table
        return None

    def general_query(self, query, commit=True, date_columns=None):
        # try:
        #     result = pd.read_sql_query(query, self.dbConnection, parse_dates=date_columns)
        # except Exception as e:
        #     print(e)
        result = self.dbConnection.execute(query).fetchall()

        if commit:
            self.dbConnection.commit()

        return result

    def quick_query(self, query_code, commit=True):
        query = QUERIES[query_code]
        try:
            result = pd.read_sql_query(query, self.dbConnection)
        except:
            result = self.general_query(query, commit=commit)

        return result

    def calculate_account_values(self, append_transaction_details=False):
        """
        Returns dataframe of account values over time. Index is sequential after reordering transactions chronologically

        Returned columns:
        ['transaction_id', 'transaction_date', 'posted_date', '0', '100', '101', '102', '103', '104', '201', '202',
        '300', '4895', '5737', '9721', 'is_posted']

        :param append_transaction_details: Adds columns for transaction data alongside account values
        :return: pandas.DataFrame
        """
        # Fetch transactions from db and order them by date
        transactions = self.get_transactions().copy().sort_index()
        transactions = transactions.sort_values(by=['posted_date', 'transaction_date'])

        # Fetch account info from database
        accounts = self.get_accounts().set_index('account_id')

        # Setup transient series to use through iterations
        account_values = pd.DataFrame()  # Setup dataframe
        starting_vals_dict = {
            'transaction_id': 'start',
            'transaction_date': 'start',
            'posted_date': 'start'}
        try:
            for v in accounts.index:
                starting_vals_dict[str(v)] = [float(accounts.at[v, 'starting_value'])]
            values = pd.Series(pd.DataFrame.from_dict(starting_vals_dict).iloc[0])
        except KeyError as err:
            if 'starting_value' in str(err):
                print('WARNING! Old database detected. Please update account table with starting_value column')
                self.logger.warning('Old database detected. Please update account table with starting_value column')
                raise RuntimeError('missing starting_value column in ACCOUNTS table of db')
            else:
                raise RuntimeError('Unknown db error while accessing starting values')

        # -- Main Loop: iterates over each transaction to calculate account value over time
        for i in transactions.index:
            # Find Accounts
            transaction_id = i
            transaction_date = transactions.at[i, 'transaction_date']
            posted_date = transactions.at[i, 'posted_date']
            debit_account = int(transactions.at[i, 'debit_account_id'])
            credit_account = int(transactions.at[i, 'credit_account_id'])

            if debit_account not in accounts.index.to_list() or credit_account not in accounts.index.to_list():
                # Catch when encounter missing/deleted accounts
                print('no account for this id, skipping')
                continue

            # Find before value of accounts
            debit_acct_0 = values[str(debit_account)]
            credit_acct_0 = values[str(credit_account)]

            # Calculate after value of accounts
            values['transaction_id'] = transaction_id

            values['transaction_date'] = transaction_date
            values['posted_date'] = posted_date

            values[str(debit_account)] = round(float(debit_acct_0) + float(transactions.at[i, 'amount']), 2)
            values[str(credit_account)] = round(float(credit_acct_0) - float(transactions.at[i, 'amount']), 2)

            # Append is_posted column
            values['is_posted'] = transactions.at[i, 'is_posted']

            # Append that new set of values to the history dataframe
            account_values = pd.concat([account_values, values.to_frame().T])

        if append_transaction_details:
            account_values.set_index('transaction_id', inplace=True)
            account_values = pd.concat([account_values, transactions], axis=1)

        # Reset index of table so it is sequential
        account_values.reset_index(inplace=True, drop=True)

        self.account_values = account_values
        return account_values

    def calculate_todays_account_values(self):
        today = datetime.datetime.today()
        self.logger.info("Calculating Today's Account Values {}...".format(today))

        account_values = self.calculate_account_values()

        posted_today = None
        # Find the latest posted transaction
        for a in account_values.iterrows():
            post_date = pd.to_datetime(a[1].posted_date)
            date_check = pd.Timedelta(days=0) < (today - post_date)  # < pd.Timedelta(days=4)
            post_check = a[1].is_posted == 1

            # print(a[1].transaction_id, a[1].posted_date, a[1].is_posted, post_check, date_check)
            if date_check and post_check:
                self.logger.debug(posted_today)
                posted_today = a[1]

        todays_values = {}
        total_assets = 0
        total_liabilities = 0
        total_retirement = 0
        if posted_today is not None:
            accounts = self.accounts.set_index('account_id', drop=False)
            accounts = accounts.sort_values('account_type')
            for account in accounts['account_id']:
                if accounts.at[account, 'account_type'] == 'asset':
                    v = posted_today[str(account)]
                    account_name = accounts.at[account, 'name']
                    todays_values[account_name] = float(v)

                    asset_accounts = accounts.loc[accounts['account_type'] == 'asset']
                    total_assets = sum(posted_today[list(asset_accounts.index.astype(str))])

                elif accounts.at[account, 'account_type'] == 'retirement':
                    v = posted_today[str(account)]
                    account_name = accounts.at[account, 'name']
                    todays_values[account_name] = float(v)

                    retirement_accounts = accounts.loc[accounts['account_type'] == 'retirement']
                    total_retirement = sum(posted_today[list(retirement_accounts.index.astype(str))])

                elif accounts.at[account, 'account_type'] == 'liability':
                    v = posted_today[str(account)]
                    account_name = accounts.at[account, 'name']
                    todays_values[account_name] = float(v)

                    liability_accounts = accounts.loc[accounts['account_type'] == 'liability']
                    total_liabilities = sum(posted_today[list(liability_accounts.index.astype(str))])

            todays_values['Total Liabilities'] = total_liabilities
            todays_values['Total Assets'] = total_assets
            todays_values['Total Retirement'] = total_retirement
        else:
            todays_values['error'] = 0

        return todays_values

    def calculate_credit_card_payment(self, account_id, payment_date):
        """
        Payment assumed to happen BEFORE the transactions post on the day of the payment even if it technically POSTS
        after the other transactions. The CC company seems to post everything towards EOD and I pay in the AM, so the
        amount paid is determined before they post.

        :param account_id:
        :param payment_date:
        :return:
        """
        accounts = self.get_accounts().set_index('account_id')
        account_id = int(account_id)
        payment_date = pd.to_datetime(payment_date)

        # Use cached transactions dataframe from predecessor function
        transactions = self.transactions.copy()

        # Find any existing payments
        # Fetch DataFrame of payment transactions and reset index such that it matches the index of list payment_dates
        # Yes, payment_dates is unnecessary and maybe a little clunky, but it is easier for now and not causing issues
        #   so it stays. In the future, a refactor here could clean up this section.
        payments = self.get_cc_payments(account_id).reset_index(drop=True)
        payment_dates = list(payments['transaction_date'])  # List of payment dates

        # Set default values
        previous_payment_id = None
        previous_payment_date = '1970-01-01'
        credit_balance = 0  # Set default credit balance

        if account_id in accounts.index and payment_date <= min(payment_dates):
            # If payment is first of the year, lookup starting value from accounts db table

            # print('generating first payment for {}'.format(accounts.at[account_id, 'name']))
            credit_balance = float(accounts.at[account_id, 'starting_value'])
        elif account_id in accounts.index and payment_date in payment_dates:
            # If the requested date matches an existing date in payments list, find that transaction id and store it
            previous_payment_index = payment_dates.index(payment_date) - 1
            previous_payment_date = pd.to_datetime(payment_dates[previous_payment_index])
            previous_payment_id = int(payments.at[previous_payment_index, 'transaction_id'])
        elif account_id in accounts.index and min(payment_dates) < payment_date <= max(payment_dates):
            # Wind up here if calculating payment BETWEEN any existing payment transactions
            previous_payment_date = None
            for x in range(len(payment_dates)):
                if payment_dates[x] < payment_date < payment_dates[x + 1]:
                    previous_payment_date = payment_dates[x]

            previous_payment_index = payment_dates.index(previous_payment_date)
            previous_payment_id = int(payments.at[previous_payment_index, 'transaction_id'])
        else:
            # Wind up here if calculating payment AFTER all existing payment transactions
            # OR if the account doesn't exist
            previous_payment_date = max(payment_dates)
            previous_payment_index = payment_dates.index(previous_payment_date)
            previous_payment_id = int(payments.at[previous_payment_index, 'transaction_id'])

        truth_series_c = (transactions['posted_date'].between(
            previous_payment_date, payment_date - pd.Timedelta(days=1))) \
                         & (transactions['credit_account_id'] == int(account_id))

        truth_series_d = (transactions['posted_date'].between(previous_payment_date,
                                                              payment_date - pd.Timedelta(days=1))) \
                         & (transactions['debit_account_id'] == int(account_id)) \
                         & (transactions.index != previous_payment_id) \
                         & (transactions['category'] != 'Credit Card Payment')

        # Expenses:
        credit_transactions = transactions.loc[truth_series_c, :]
        # print(credit_transactions)
        # credit_transactions.to_csv('./credit_transacts.csv')

        # Rewards/Returns:
        debit_transactions = transactions.loc[truth_series_d, :]
        # print(debit_transactions)

        credits_sum = round(sum(credit_transactions['amount']), 2)
        debits_sum = round(sum(debit_transactions['amount']), 2)
        payment_amount = round(credits_sum - credit_balance - debits_sum, 2)

        self.logger.info('\nNew Payment:  {} -- id: n/a\nPrev payment: {} -- id: {}\n'.format(payment_date,
                                                                                              # payment_id,
                                                                                              previous_payment_date,
                                                                                              previous_payment_id))
        print('\nNew Payment:  {} -- id: n/a\nPrev payment: {} -- id: {}'.format(payment_date,
                                                                                 # payment_id,
                                                                                 previous_payment_date,
                                                                                 previous_payment_id))
        # print('credits_sum: $', credits_sum, ':: debits_sum:  $', debits_sum)
        print('\tPayment:  $ {:.2f}\n'.format(payment_amount))
        return payment_amount

    def update_credit_card_payment(self, modified_transaction_id, account=None):
        """
        When passed a transaction id for a modified transaction, the appropriate CC payment transaction amount gets
        updated. Specify an account for updates where the transaction was moved away from that account.

        :param modified_transaction_id:
        :param account:
        :return:
        """
        print('Recalculating upcoming credit card payment -- {} modified'.format(modified_transaction_id))
        self.logger.info('Recalculating upcoming credit card payment -- {} modified'.format(modified_transaction_id))

        transactions = self.transactions.copy()
        transaction = transactions.loc[int(modified_transaction_id), :]

        if transaction['category'] == 'Credit Card Payment':
            print('-- Credit Card Payment Updated, Skipping Recalc --')
            self.logger.info('-- Credit Card Payment Updated, Skipping Recalc --')
            return None

        credit_account = int(transaction['credit_account_id'])
        debit_account = int(transaction['debit_account_id'])
        post_date = pd.to_datetime(transaction['posted_date'])

        accounts = self.get_accounts().set_index('account_id')
        cc_accounts = accounts.loc[accounts['transaction_type'] == 'credit_card']
        # print('Account columns', accounts.columns)  # ['name', 'transaction_type', 'account_type', 'starting_value']

        if account is None:
            if credit_account in list(cc_accounts.index):
                account_id = int(credit_account)
            elif debit_account in list(cc_accounts.index):
                account_id = int(debit_account)
            else:
                raise RuntimeError('Unknown Account ID')
        else:
            account_id = int(account)

        cc_payments = self.get_cc_payments(account_id).reset_index(drop=True)
        if len(cc_payments) == 0 or post_date > max(cc_payments['transaction_date']):
            print('\nCREATING NEW CC PAYMENT')
            t_date = pd.to_datetime(transaction['transaction_date'])

            payment_account = accounts.loc[accounts['transaction_type'] == 'income']
            pay_dates = transactions.loc[transactions['credit_account_id'] == int(payment_account.index[0])][
                'transaction_date']
            payment_date = None
            for d in pay_dates.index:
                if pay_dates[d] > t_date:  # Find next paycheck after the transaction and set CC payment date
                    payment_date = pay_dates[d]
                    break
            if payment_date is None:
                payment_date = t_date  # Fallback to the date of the modified transaction instead of crashing

            payment_id = self.add_transaction(payment_date,
                                              'Credit Card Payment',
                                              10.00,
                                              posted_date=payment_date,
                                              debit_account=account_id,
                                              description='CC Payment',
                                              vendor=accounts.loc[account_id]['name'])
        else:
            # Find payment date and calculate payment amount
            payment_date = payment_id = None
            # print('cc_payments', cc_payments)
            for i in cc_payments.index:
                if post_date < min(cc_payments['transaction_date']):
                    payment_date = min(cc_payments['transaction_date'])
                    payment_id = cc_payments.loc[cc_payments['transaction_date'] == payment_date, 'transaction_id']
                elif cc_payments.at[i, 'transaction_date'] <= post_date < cc_payments.iloc[i + 1]['transaction_date']:
                    payment = cc_payments.iloc[i + 1]  # should be i+1 (later payment)
                    payment_date = payment['transaction_date']
                    payment_id = payment['transaction_id']
                else:
                    pass

        if payment_date is None or payment_id is None:
            raise RuntimeError('Could not determine payment date or payment_id')

        print('STEP 1 - Calculate Payment Amount')
        amount = self.calculate_credit_card_payment(account_id, payment_date)

        print('STEP 2 - Update Database CC Payment')
        self.update_transaction(int(payment_id), amount=amount)

        return amount

    def calculate_burn_from_date(self, date, include_retirement=False):
        """
            INACTIVE -- Work in Progress function

            Returns dataframe of account values over time. Index is sequential after reordering transactions chronologically

            Returned columns:
                ['transaction_id', 'transaction_date', 'posted_date', '0', '100', '101', '102', '103', '104', '201', '202',
                '300', '4895', '5737', '9721', 'is_posted']

            :param date: Date after which no income occurs
            :return: pandas.DataFrame
        """
        # Fix type of date input
        date = pd.to_datetime(date)

        # Fetch account info from database
        accounts = self.get_accounts().set_index('account_id')
        asset_accounts = accounts.loc[accounts['account_type'] == 'asset']
        asset_accounts_no_invest = asset_accounts.loc[asset_accounts['transaction_type'] != 'investment']

        # Setup transient series to use through iterations
        account_values: pd.DataFrame = pd.DataFrame()  # Setup dataframe
        starting_vals_dict = {
            'transaction_id': 'start',
            'transaction_date': 'start',
            'posted_date': 'start'}
        try:
            for v in accounts.index:
                starting_vals_dict[str(v)] = [float(accounts.at[v, 'starting_value'])]
            values = pd.Series(pd.DataFrame.from_dict(starting_vals_dict).iloc[0])
        except KeyError as err:
            if 'starting_value' in str(err):
                print('WARNING! Old database detected. Please update account table with starting_value column')
                self.logger.warning('Old database detected. Please update account table with starting_value column')
                raise RuntimeError('missing starting_value column in ACCOUNTS table of db')
            else:
                raise RuntimeError('Unknown db error while accessing starting values')

        # -- Main Loop: iterates over each transaction to calculate account value over time
        i = 0
        monthly_expense = float(self.config['personal']['average_monthly_expend'])

        # Fetch transactions from db and order them by date
        transactions = self.get_transactions(start_date=date).copy().sort_index()
        # print(transactions)
        transactions = transactions.sort_values(by=['posted_date', 'transaction_date'])

        last = transactions.iloc[-1]
        outstanding_transactions = transactions.copy()
        for transaction_id in transactions.index:
            # print(transaction_id)
            transaction_date = transactions.at[transaction_id, 'transaction_date']
            posted_date = transactions.at[transaction_id, 'posted_date']
            debit_account = int(transactions.at[transaction_id, 'debit_account_id'])  # To
            credit_account = int(transactions.at[transaction_id, 'credit_account_id'])  # From

            # Find before value of accounts
            debit_acct_0 = values[str(debit_account)]
            credit_acct_0 = values[str(credit_account)]

            # Update value dictionary information
            values['transaction_id'] = transaction_id
            values['transaction_date'] = transaction_date
            values['posted_date'] = posted_date
            values['is_posted'] = transactions.at[transaction_id, 'is_posted']

            # Calculate new account values
            values[str(debit_account)] = round(float(debit_acct_0) + float(transactions.at[transaction_id, 'amount']),
                                               2)
            values[str(credit_account)] = round(float(credit_acct_0) - float(transactions.at[transaction_id, 'amount']),
                                                2)

            # Calculate Combined Account Values Loop
            account_sum = 0
            for acc in list(asset_accounts.index):
                if 'retire' in accounts.at[acc, 'name'].lower():
                    # pre-tax money gets adjusted here if you decide to include these accounts in your burn
                    if include_retirement:
                        y = float(values[str(acc)]) * (1 - float(self.config['personal']['retirement_tax_rate']))
                    else:
                        y = 0
                else:
                    y = values[str(acc)]

                account_sum += round(y, 2)
            values['account_sum'] = account_sum

            account_sum_no_invest = 0
            for acc in list(asset_accounts_no_invest.index):
                account_sum_no_invest += float(values[str(acc)])

            account_sum_no_invest = round(account_sum_no_invest, 2)
            values['account_sum_no_invest'] = account_sum_no_invest

            # Calculate Burn Loop
            outstanding_expenses = outstanding_transactions.loc[transactions['debit_account_id'] == 0]

            expense_sum = 0
            burn_time, burn_time_full, burn_time_part = 0, 0, 0
            full_set = False
            no_invest_set = False
            for e in outstanding_expenses.iterrows():
                expense_sum += round(float(e[1]['amount']), 2)

                if expense_sum > account_sum_no_invest and not no_invest_set:
                    # Result.value is in nanoseconds. Converting ns to months (assumed 30 days/month)
                    burn_time_part = pd.Timedelta(e[1]['transaction_date'] - transaction_date).value / (
                                30 * 24 * 3600 * 1000000000)
                    no_invest_set = True

                if expense_sum > account_sum and not full_set:
                    # Result.value is in nanoseconds. Converting ns to months (assumed 30 days/month)
                    burn_time_full = pd.Timedelta(e[1]['transaction_date'] - transaction_date).value / (
                                30 * 24 * 3600 * 1000000000)
                    full_set = True

                if e[1]['transaction_id'] == outstanding_expenses.iloc[-1]['transaction_id']:
                    # Result.value is in nanoseconds. Converting ns to months (assumed 30 days/month)
                    burn_time = pd.Timedelta(last['transaction_date'] - transaction_date).value / (
                                30 * 24 * 3600 * 1000000000)
                    if not full_set:
                        burn_time_full = burn_time + (account_sum - expense_sum) / monthly_expense
                        full_set = True

                    if not no_invest_set:
                        burn_time_part = burn_time + (account_sum_no_invest - expense_sum) / monthly_expense
                        no_invest_set = True

                if full_set and no_invest_set:
                    break

            values['burntime_full'] = burn_time_full
            values['burntime_no_invest'] = burn_time_part

            # Drop
            outstanding_transactions = outstanding_transactions.drop(transaction_id)

            # Append that new set of values to the history dataframe
            account_values = pd.concat([account_values, values.to_frame().T])

            i += 1

        # Append other info from transactions table
        account_values.set_index('transaction_id', inplace=True)
        account_val_cols = list(account_values.columns)
        append_cols = [i for i in transactions.columns if i not in account_val_cols]
        account_values = pd.concat([account_values, transactions.loc[list(account_values.index), append_cols]], axis=1)

        # Reset index of table so it is sequential
        account_values.reset_index(inplace=True, drop=True)

        self.account_values = account_values
        return account_values

    def category_summary(self, date_filter='all'):
        from tabulate import tabulate
        transactions = self.get_transactions(date_filter=date_filter)
        cat_width = 30
        amount_width = 10

        transactions = transactions.loc[
            (transactions['category'] != 'Investment') &
            (transactions['category'] != 'Transfer') &
            (transactions['category'] != 'Transfer ')
            ]

        out_transactions = transactions.loc[transactions['debit_account_id'] == 0]
        in_transactions = transactions.loc[
            (transactions['credit_account_id'] == 0) |
            (transactions['credit_account_id'] == 300)
            ]

        # categories = sorted(transactions.category.unique())
        categories = self.categories
        summary = pd.DataFrame()  # columns=categories

        for category in categories:
            if category in in_transactions['category'].unique():
                summary.at[category, 'inflow'] = round(
                    sum(in_transactions[in_transactions['category'] == category].amount), 2)  # row/column
            if category in out_transactions['category'].unique():
                summary.at[category, 'outflow'] = round(
                    sum(out_transactions[out_transactions['category'] == category].amount), 2)  # row/column

        summary = summary.fillna(0)
        print(tabulate(summary))

        summary['total'] = summary['inflow'] - summary['outflow']
        # print(sum(summary['total']))

        debit_sum = round(sum(out_transactions.amount), 2)
        credit_sum = round(sum(in_transactions.amount), 2)
        print('\nNet Debits (outflow): ${:.2f}'.format(debit_sum))
        print('Net Credits (inflow): ${:.2f}'.format(credit_sum))
        print('Net Delta   (in-out): ${:.2f}'.format(credit_sum - debit_sum))
        return None

    def get_cc_payments(self, account):
        if account not in list(self.get_accounts().index):
            warnings.warn('Incorrect account id entered')
            return

        transactions = self.get_transactions(account_filter=account)
        payments = transactions[
            (transactions['debit_account_id'] == account) & (transactions['category'] == 'Credit Card Payment')]
        return payments

    def set_year(self, year: int):
        print('setting active year to', year)
        self.year = year
        self.parse_date_filters()

    def parse_date_filters(self):
        # print('parsing date filters')

        year = self.year
        if year is None:
            # print('year is None, using default year')
            year = self.default_year

        # print('active year', year)

        date_filters = {}
        for k in self.config['ui_settings.date_filters']:
            date_filters[k] = self.config['ui_settings.date_filters'][k].replace('yyyy', '{}'.format(year)).split(',')

        # print('date_filters', date_filters)
        self.date_filters = date_filters

        return date_filters

    @staticmethod
    def create_fresh_database(filepath, create_tables=False):
        """
        Function that builds a starter database when none exists at startup
        """
        try:
            conn = sql.connect(filepath)
            print("Database formed at: {}".format(os.path.abspath(filepath)))

            if create_tables:
                create_accounts_query = '''CREATE TABLE ACCOUNTS
                                   (account_id INTEGER PRIMARY KEY NOT NULL,
                                   name TEXT NOT NULL,
                                   transaction_type TEXT NOT NULL,
                                   account_type TEXT NOT NULL,
                                   starting_value REAL NOT NULL
                                   );
                                '''
                conn.execute(create_accounts_query)

                add_account_query = '''INSERT INTO ACCOUNTS
                                    (account_id,
                                    name,
                                    transaction_type,
                                    account_type,
                                    starting_value
                                    )
                                    VALUES
                                    ({account_id},
                                    '{name}',
                                    '{transaction_type}',
                                    '{account_type}',
                                    '{start_value}');'''
                add_external = add_account_query.format(
                    account_id=0,
                    name='External',
                    transaction_type='external',
                    account_type='other',
                    start_value=0.00,
                )
                conn.execute(add_external)

                add_test = add_account_query.format(
                    account_id=100,
                    name='Checking',
                    transaction_type='bank',
                    account_type='asset',
                    start_value=0.00,
                )
                conn.execute(add_test)
                conn.commit()

                create_transactions_query = '''CREATE TABLE TRANSACTIONS
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
                conn.execute(create_transactions_query)

                add_transaction_query = '''INSERT INTO TRANSACTIONS
                                                    (transaction_date,
                                                    posted_date,
                                                    credit_account_id,
                                                    debit_account_id,
                                                    category,
                                                    description,
                                                    amount,
                                                    vendor,
                                                    is_posted)
                                                VALUES
                                                    ("{t_date}",
                                                    "{p_date}",
                                                    {c_account_id},
                                                    {d_account_id},
                                                    "{category}",
                                                    "{description}",
                                                    {amount},
                                                    "{vendor}",
                                                    {is_posted});'''.format(
                    t_date='2000-01-01',
                    p_date='2000-01-01',
                    c_account_id=100,
                    d_account_id=100,
                    category='Setup',
                    description='description',
                    amount=0,
                    vendor='vendor',
                    is_posted=1,
                )
                conn.execute(add_transaction_query)
                conn.commit()

                print("Database tables created")

                return True

        except Exception as e:
            print("Database not formed")
            print(e)
            return False

    @staticmethod
    def append_total(data, column_names):
        total_index = max(data.index) + 1
        for c in column_names:
            data.loc[total_index, c] = sum(data[c])
        # data.loc[max(data.index) + 1, 'description'] = 'Total'
        return data

    @staticmethod
    def filter_by_category(data, category):
        if category == "All":
            pass
        else:
            data = data[data['category'] == category]
        return data

    @staticmethod
    def get_transaction(db_connection, transaction_id, logger=None):
        if logger is not None:
            logger.info('getting details for transaction {}'.format(transaction_id))

        cols = TRANSACTION_TABLE_COLS

        query = f"""SELECT * from TRANSACTIONS
                   WHERE transaction_id={transaction_id};
                """
        c = db_connection.cursor()
        c.execute(query)
        db_row = c.fetchone()[:]
        data = {}
        i = 0
        for c in cols:
            data[c] = db_row[i]
            i += 1
        return data


class Account:
    def __init__(self, account_id: int, database: BudgetData):
        self.account_id = int(account_id)

        account = database.get_accounts().loc[account_id]
        self.name = account['name']
        self.starting_balance = account['starting_value']
        self.transaction_type = account['transaction_type']
        self.account_type = account['account_type']

        self.transactions = database.get_transactions(account_filter=account_id)
        self.balance = 0

        print('\nConfiguring account {} from database...'.format(self.account_id))
        print('account id:', self.account_id,
              '\naccount name:', self.name,
              '\nstarting balance:', self.starting_balance,
              '\ntransaction type:', self.transaction_type,
              '\nacccount type:', self.account_type)
        if self.transactions is None:
            print('No transactions')
        else:
            print('transactions df info', self.transactions.info())


class CreditCard(Account):
    def __init__(self, account_id, database):
        super().__init__(account_id, database)


def fetch_filtered_transactions(filters):
    # Fetch filtered results
    result = DATA.get_transactions(
        date_filter=filters['date'],
        start_date=None,
        end_date=None,
        date_type='transaction_date',
        account_filter=filters['account'],
        expense_income_filter=filters['income_expense'],
        category_filter=filters['category'],
        append_total=False)

    if result is None:
        print('Empty DataFrame after filters')
        return pd.DataFrame(columns=TRANSACTION_TABLE_COLS)

    else:
        result = result.copy()

        # Reformat amount column
        result['amount_string'] = result['amount'].map('$ {:,.2f}'.format)

        # Reformat date columns
        result['transaction_date'] = result['transaction_date'].dt.strftime('%Y-%m-%d')
        result['posted_date'] = result['posted_date'].dt.strftime('%Y-%m-%d')

        # Reformat is_posted column
        result['is_posted'] = result['is_posted'].replace([0, 1], ['', 'checked'])

        # Append account names
        account_id_list = [0] + list(DATA.accounts['account_id'])
        account_translate_dict = {}
        for i in list(range(len(account_id_list))):
            account_translate_dict[account_id_list[i]] = (['All'] + list(DATA.accounts['name']))[i]
        result['credit_account_name'] = result['credit_account_id'].replace(account_translate_dict)
        result['debit_account_name'] = result['debit_account_id'].replace(account_translate_dict)

        return result


CONFIG = config.AppConfig()  # THIS IS THE MAIN CONFIG OBJECT FOR THE PROJECT
DATA = BudgetData(CONFIG)

environ = CONFIG['env']['environ']
DB_FILE = CONFIG['database'][environ]
DATA.connect(DB_FILE)

if __name__ == "__main__":
    print('Config environment: {}'.format(CONFIG['env']['environ']))

    # help(pd.set_option)
    pd.set_option('display.max_rows', 1000)
    pd.set_option('display.min_rows', 50)
    pd.options.display.width = 0
    pd.set_option('display.max_columns', 30)

    # -- ADD
    # DATA.add_transaction('2023-06-15', 'Test', 123, credit_account=9721)
    # print(DATA.get_transactions(account_filter=9721))
    # print(DATA.get_cc_payments(account=9721))

    # -- DELETE
    # for i in [872]:
    #     DATA.delete_transaction(i)
    # print(DATA.get_transactions(account_filter=9721))
    # print(DATA.get_cc_payments(account=9721))

    # -- UPDATE
    # DATA.update_transaction(896)

    # print(DATA.get_transactions(account_filter=9721))
    # print(DATA.get_cc_payments(account=4895))
    # print(DATA.calculate_credit_card_payment(4895, '2023-11-02'))

    # -- TOOLS
    # COPY HERE: ['q1', 'q2', 'q3', 'q4', 'all']['january', 'february', 'march', 'april', 'may', 'june']['july', 'august', 'september', 'october', 'november', 'december']
    # for n in ['july', 'august', 'september', 'october', 'november', 'december', 'all']:
    #     print('\n\t{}'.format(n.upper()))
    #     DATA.category_summary(date_filter=n)

    # DATA.get_transactions().to_csv('./2023transacts.csv')

    # DATA.calculate_account_values(append_transaction_details=True).to_csv('./2023_account_vals.csv')

    # --- SANDBOX ---
    # date = pd.to_datetime('2023-09-01')
    # print(DATA.get_transactions(start_date=date))
    # burn_table = DATA.calculate_burn_from_date('2023-09-01')
    # print(burn_table.columns)
    # print(burn_table[['transaction_date', 'account_sum', 'account_sum_no_invest', 'burntime_full', 'burntime_no_invest']])

    # print(DATA.get_accounts())
    print(DATA.get_transactions(category_filter='Transfer'))
    # print(DATA.quick_query('list_tables'))
    # print(DATA.get_categories())

    DATA.close()
