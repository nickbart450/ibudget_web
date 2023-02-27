# budget_data.py
__version__ = '0.1.1'

import os.path
import pandas as pd
import sqlite3 as sql
import logging
# import configparser
import config

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


class BudgetData:
    """
    Default date filters are 2023
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('budget_data -- DEBUG LOGGING MODE')
        self.logger.info('budget_data -- INFO LOGGING MODE')

        # Load config settings
        self.config = config.CONFIG

        # Parse date filters from config
        self.date_filters = {}
        for k in self.config['ui_settings.date_filters']:
            self.date_filters[k] = self.config['ui_settings.date_filters'][k].split(',')

        self.dbConnection = None
        self.dbConnected = False
        self.connection_attempts = 0

        self.transaction_cache = None

    def connect(self, db_file):
        self.connection_attempts += 1
        try:
            if os.path.exists(os.path.abspath(db_file)):
                self.logger.info('Attempting to open {}'.format(os.path.abspath(db_file)))
                self.dbConnection = sql.connect(db_file, check_same_thread=False)
                test_query = 'SELECT sqlite_version();'
                test_cursor = self.dbConnection.cursor()
                self.db_version = test_cursor.execute(test_query).fetchall()[0]
                self.dbConnected = True
                self.logger.info('Successfully Connected')
                return True
            elif os.path.exists(os.path.abspath('./budget_example.db')):
                self.logger.debug('Primary connection failed, attempting to open {}'.format(os.path.abspath('./budget_example.db')))
                self.dbConnection = sql.connect('./budget_example.db', check_same_thread=False)
                test_query = 'SELECT sqlite_version();'
                test_cursor = self.dbConnection.cursor()
                self.db_version = test_cursor.execute(test_query).fetchall()[0]
                self.dbConnected = True
                self.logger.info('Successfully Connected to Example db')
                return True
            else:
                if self.connection_attempts <= 5:
                    self.logger.warning('No database file found, attempting to create fresh, empty database at {}'.format(os.path.abspath(db_file)))
                    self.create_fresh_database(os.path.abspath(db_file), create_tables=True)
                    self.connect(db_file)  # reattempt connection
                else:
                    self.logger.warning('attempted db connection/creation 5 times, quitting')
                    self.dbConnected = False
                    return None

        # Handle errors
        except sql.Error as e:
            self.logger.warning('Failed db connection/creation with error: {}'.format(e))
            self.dbConnected = False
            return None

    def close(self):
        if self.dbConnected:
            self.dbConnection.close()
            self.dbConnected = False
            self.logger.info('SQLite Connection closed')
        else:
            # print('No SQLite Connection to close')
            self.logger.info('No SQLite Connection to close')

    def get_accounts(self):
        if self.dbConnected:
            self.dbConnection.row_factory = sql.Row  # Sets the direction of returned data to work with pd.from_dict
            accounts = self.dbConnection.cursor().execute('''SELECT * FROM ACCOUNTS''').fetchall()
            account_table = pd.DataFrame([dict(row) for row in accounts])
            return account_table
        else:
            raise RuntimeError('database not connected')

    def get_transactions(self, date_filter=None, start_date=None, end_date=None, date_type='transaction_date',
                         account_filter='All', expense_income_filter='Both',
                         append_total=False):  # alternative date_type: posted_date
        """ Can provide either filter code string (ex. 'January', 'Q3') defined by date_filters dict
                            OR  start and end dates of format 'YYYY-mm-dd'
        """

        query = """SELECT * from TRANSACTIONS
                   {fill}
                   ORDER BY transaction_date ASC;
                """

        # Query (Date Filter happens here)
        if date_filter == 'Date Filter':
            date_filter = 'all'

        if date_filter is not None:
            date_filter = date_filter.lower()
            d1 = self.date_filters[date_filter][0]
            d2 = self.date_filters[date_filter][1]
            query = query.format(fill="""WHERE {0} BETWEEN '{1}' AND '{2}'""")
            query = query.format(date_type, d1, d2)
        elif start_date is not None and end_date is not None:
            d1 = start_date
            d2 = end_date
            query = query.format(fill="""WHERE {0} BETWEEN '{1}' AND '{2}'""")
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
        else:
            account = [int(accounts[accounts['name'] == account_filter]['account_id'])]

        debit_truth_series = []
        for i in df.index:
            if df.iloc[i].debit_account_id in account:
                debit_truth_series.append(True)
            else:
                debit_truth_series.append(False)

        credit_truth_series = []
        for i in df.index:
            if df.iloc[i].credit_account_id in account:
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
        if expense_income_filter == 'Expenses':
            df = df[df['debit_account_id'] == 0]

        elif expense_income_filter == 'Income':
            df = pd.concat([df[df['credit_account_id'] == 0], df[df['credit_account_id'] == 300]])

        # Append Total
        if append_total:
            col_names = ['amount']
            df = self.append_total(df, col_names)
            df.fillna('', inplace=True)

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
        # accounts = self.get_accounts()
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

        print('adding transaction:')
        print('\ttransaction_date: ', transaction_date)
        print('\tposted_date: ', posted_date)
        print('\tcredit_account: ', credit_account)
        print('\tdebit_account: ', debit_account)
        print('\tamount: ', amount)
        print('\tcategory: ', category)
        print('\tdescription: ', description)
        print('\tvendor: ', vendor)
        print('\tposted_flag: ', is_posted)

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

        cursor = self.dbConnection.cursor()
        cursor.execute(query)
        self.dbConnection.commit()

    def update_transaction(self, transaction_id, transaction_date=None, category=None, amount=None, posted_date=False,
                           credit_account=False,
                           debit_account=False, description=None, vendor=None, is_posted=None):
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
        transaction = self.get_transaction(self.dbConnection, transaction_id)

        if transaction_date:
            transaction_date = pd.to_datetime(transaction_date)
        else:
            transaction_date = transaction['transaction_date']

        if category is None:
            category = transaction['category']

        if amount is None:
            amount = transaction['amount']

        # handle post date
        if posted_date:
            posted_date = pd.to_datetime(posted_date)
        else:
            posted_date = transaction['posted_date']
            # posted_date = pd.to_datetime(transaction_date) + pd.Timedelta(days=2)

        # handle accounts
        accounts = self.get_accounts()
        if credit_account and debit_account:
            if credit_account == debit_account:
                raise RuntimeError('debit_account must be different from credit_account')
            else:
                credit_account = int(accounts[accounts['name'] == credit_account]['account_id'])
                debit_account = int(accounts[accounts['name'] == debit_account]['account_id'])
        elif credit_account and not debit_account:
            self.logger.info('credit_account ONLY provided')
            credit_account = int(accounts[accounts['name'] == credit_account]['account_id'])
            debit_account = 0
        elif debit_account and not credit_account:
            self.logger.info('debit_account ONLY provided')
            credit_account = 0
            debit_account = int(accounts[accounts['name'] == debit_account]['account_id'])
        else:
            credit_account = transaction['credit_account_id']
            debit_account = transaction['debit_account_id']
            # raise RuntimeError('Please specify at least one account as debit_account or credit_account')

        if description is None:
            description = transaction['description']

        if vendor is None:
            vendor = transaction['vendor']

        # convert is_posted
        if is_posted is None:
            is_posted = transaction['is_posted']
        else:
            if is_posted:
                is_posted = 1
            else:
                is_posted = 0

        print('Updating transaction:')
        print('\ttransaction_id: ', transaction_id)
        print('\ttransaction_date: ', transaction_date)
        print('\tposted_date: ', posted_date)
        print('\tcredit_account: ', credit_account)
        print('\tdebit_account: ', debit_account)
        print('\tamount: ', amount)
        print('\tcategory: ', category)
        print('\tdescription: ', description)
        print('\tvendor: ', vendor)
        print('\tposted_flag: ', is_posted)

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
            t_date=transaction_date,
            p_date=posted_date,
            c_account_id=credit_account,
            d_account_id=debit_account,
            category=category,
            description=description,
            amount=amount,
            vendor=vendor,
            is_posted=is_posted,
            transaction_id=transaction_id,
        )
        self.logger.debug('update_transaction query:\n{}'.format(q_update))

        cursor = self.dbConnection.cursor()
        cursor.execute(q_update)
        self.dbConnection.commit()

    def delete_transaction(self, id):
        query = '''DELETE FROM TRANSACTIONS
                WHERE transaction_id={};'''.format(id)
        cursor = self.dbConnection.cursor()
        cursor.execute(query)
        self.dbConnection.commit()
        self.logger.info('Deleting Transaction: {}'.format(id))

    def general_query(self, query, date_columns=None):
        try:
            result = pd.read_sql_query(query, self.dbConnection, parse_dates=date_columns)
        except Exception as e:
            result = self.dbConnection.execute(query).fetchall()
        self.dbConnection.commit()

        return result

    def quick_query(self, query_code):
        return self.general_query(QUERIES[query_code])

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
        transactions = self.get_transactions()
        transactions.sort_values(by=['transaction_date', 'transaction_id'], inplace=True)

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
            transaction_id = int(transactions.iloc[i]['transaction_id'])
            transaction_date = transactions.iloc[i]['transaction_date']
            posted_date = transactions.iloc[i]['posted_date']
            debit_account = int(transactions.iloc[i]['debit_account_id'])
            credit_account = int(transactions.iloc[i]['credit_account_id'])

            # Find before value of accounts
            debit_acct_0 = values[str(debit_account)]
            credit_acct_0 = values[str(credit_account)]

            # Calculate after value of accounts
            values['transaction_id'] = transaction_id

            values['transaction_date'] = transaction_date
            values['posted_date'] = posted_date

            values[str(debit_account)] = round(float(debit_acct_0) + float(transactions.iloc[i]['amount']), 2)
            values[str(credit_account)] = round(float(credit_acct_0) - float(transactions.iloc[i]['amount']), 2)

            # Append that new set of values to the history dataframe
            account_values = pd.concat([account_values, values.to_frame().T])

        if append_transaction_details:
            details_list = [
                'credit_account_id',
                'debit_account_id',
                'category',
                'description',
                'amount',
                'vendor',
                'is_posted',
            ]
            account_values.set_index('transaction_id', inplace=True)
            transactions.set_index('transaction_id', inplace=True)
            account_values = pd.concat([account_values, transactions], axis=1)

        else:
            # Append is_posted column
            account_values['is_posted'] = list(transactions['is_posted'])

        # Reset index of table so it is sequential
        account_values.reset_index(inplace=True, drop=True)

        return account_values

    def calculate_credit_card_payment(self, account_id, payment_date, use_cached=False):
        """
        Payment assumed to happen BEFORE the transactions post on the day of the payment even if it technically POSTS
        after the other transactions. The CC company seems to post everything towards EOD and I pay in the AM, so the
        amount paid is determined before they post.

        :param use_cached:
        :param account_id:
        :param payment_date:
        :return:
        """
        accounts = self.get_accounts().set_index('account_id')
        account_id = int(account_id)
        payment_date = pd.to_datetime(payment_date)

        # Use cached transactions dataframe from predecessor function
        if use_cached:
            transactions = self.transaction_cache
        else:
            transactions = self.get_transactions()

        # Find any existing payments
        payments = self.get_cc_payments(transactions, account_id)  # Fetch DataFrame of payment transactions
        payment_dates = list(payments['posted_date'])  # List of payment dates

        # Set default values
        previous_payment_id = None
        previous_payment_date = '1970-01-01'
        credit_balance = 0  # Set default credit balance

        if payment_date in list(payments['transaction_date']):
            # If the requested date matches an existing date in payments list, find that transaction id and store it

            # Determine previous payment id #
            previous_payment_index = payment_dates.index(payment_date) - 1
            previous_payment_date = pd.to_datetime(payment_dates[previous_payment_index])
            previous_payment_id = int(payments.iloc[previous_payment_index]['transaction_id'])
        elif payment_date < min(payment_dates) and account_id in accounts.index:
            # If payment is first of the year, lookup starting value from accounts db table

            # print('generating first payment for {}'.format(accounts.at[account_id, 'name']))
            credit_balance = float(accounts.at[account_id, 'starting_value'])
        elif min(payment_dates) < payment_date < max(payment_dates):
            # Wind up here if calculating payment BETWEEN any existing payment transactions
            for x in range(len(payment_dates)):
                if payment_dates[x] < payment_date < payment_dates[x+1]:
                    previous_payment_date = payment_dates[x]
                    previous_payment_index = payment_dates.index(previous_payment_date)
                    previous_payment_id = int(payments.iloc[previous_payment_index]['transaction_id'])
                else:
                    print('something is wrong if you are here!')
        else:
            # Wind up here if calculating payment AFTER all existing payment transactions
            previous_payment_date = max(payment_dates)
            previous_payment_index = payment_dates.index(previous_payment_date)
            previous_payment_id = int(payments.iloc[previous_payment_index]['transaction_id'])

        self.logger.info('\nNew Payment:  {} -- id: n/a\nPrev payment: {} -- id: {}\n'.format(payment_date,
                                                                                              # payment_id,
                                                                                              previous_payment_date,
                                                                                              previous_payment_id))
        print('\nNew Payment:  {} -- id: n/a\nPrev payment: {} -- id: {}\n'.format(payment_date,
                                                                                   # payment_id,
                                                                                   previous_payment_date,
                                                                                   previous_payment_id))

        truth_series_c = (transactions['posted_date'].between(
            previous_payment_date, payment_date - pd.Timedelta(days=1))) \
            & (transactions['credit_account_id'] == int(account_id))

        truth_series_d = (transactions['posted_date'].between(previous_payment_date,
                                                              payment_date - pd.Timedelta(days=1))) \
                          & (transactions['debit_account_id'] == int(account_id)) \
                          & (transactions['transaction_id'] != previous_payment_id) \
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

        # print('credits_sum: $', credits_sum, ':: debits_sum:  $', debits_sum)
        # print('PAYMENT:  $ {:.2f}\n'.format(payment_amount))
        return payment_amount

    def update_credit_card_payment(self, modified_transaction_id):
        """
        When passed a transaction id for a modified transaction, the appropriate CC payment transaction amount gets
        updated.

        :param modified_transaction_id:
        :return:
        """
        self.logger.info('\nRecalculating upcoming credit card payment -- {}'.format(modified_transaction_id))
        modified_transaction_id = int(modified_transaction_id)

        self.transaction_cache = self.get_transactions()
        accounts = self.get_accounts()

        transaction = self.transaction_cache.loc[self.transaction_cache['transaction_id'] == modified_transaction_id]
        transaction_account = int(transaction['credit_account_id'])

        if str(accounts[accounts['account_id'] == transaction_account]['account_type'].values[0]) == 'liability':
            # print('Modified Transaction: {} -- {} -- {}'.format(modified_transaction_id,
            #                                                     str(transaction['description'].values[0]),
            #                                                     transaction['posted_date'].values[0]))  # numpy.datetime64

            account_id = transaction['credit_account_id'].values[0]
            post_date = transaction['posted_date'].values[0]

            cc_payments = self.get_cc_payments(self.transaction_cache, account_id)
            payment_date = None
            for i in cc_payments.index:
                if cc_payments.iloc[i]['posted_date'] <= post_date < cc_payments.iloc[i + 1]['posted_date']:
                    payment_date = cc_payments.iloc[i + 1]['posted_date']
                    payment_id = cc_payments.iloc[i + 1]['transaction_id']

            if payment_date is None:
                payment_date = cc_payments.iloc[0]['posted_date']
                payment_id = cc_payments.iloc[0]['transaction_id']

            amount = self.calculate_credit_card_payment(account_id, payment_date, use_cached=True)

            self.update_transaction(payment_id, amount=amount)

            return amount

    def category_summary(self, date_filter='all'):
        transactions = self.get_transactions(date_filter=date_filter)
        cat_width = 30
        amount_width = 10

        for i in transactions.category.unique():
            str_1 = '{}{}'.format('_' * (cat_width - len(i) - 9), i)
            str_2 = '${:.2f}'.format(round(sum(transactions[transactions['category'] == i].amount), 2))
            print('Category:', str_1, 'Amount:', '_' * (amount_width - len(str_2)), str_2)

        debit_sum = round(sum(transactions[transactions['debit_account_id'] == 0].amount), 2)
        credit_sum = round(sum(transactions[(transactions['credit_account_id'] == 0) |
                                            (transactions['credit_account_id'] == 300)].amount), 2)
        print('Net Debits (outflow): ${:.2f}'.format(debit_sum))
        print('Net Credits (inflow): ${:.2f}'.format(credit_sum))
        print('Net Delta   (in-out): ${:.2f}'.format(credit_sum-debit_sum))

    @staticmethod
    def get_cc_payments(transactions, account):
        payments = transactions[
            (transactions['debit_account_id'] == int(account)) & (transactions['category'] == 'Credit Card Payment')]
        payments.reset_index(drop=True, inplace=True)

        return payments

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
                                   account_type TEXT NOT NULL
                                   );
                                '''
                conn.execute(create_accounts_query)

                add_account_query = '''INSERT INTO ACCOUNTS
                                    (account_id,
                                    name,
                                    transaction_type,
                                    account_type
                                    )
                                    VALUES
                                    ({account_id},
                                    '{name}',
                                    '{transaction_type}',
                                    '{account_type}');'''.format(
                    account_id=100,
                    name='test',
                    transaction_type='cash',
                    account_type='other'
                )
                conn.execute(add_account_query)
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

                # self.add_transaction('2000-01-01', 'Test Category', '0.00')

        except Exception as e:
            print("Database not formed")
            print(e)

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

        cols = ['transaction_id',
                'transaction_date',
                'posted_date',
                'credit_account_id',
                'debit_account_id',
                'category',
                'description',
                'amount',
                'vendor',
                'is_posted']

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


if __name__ == "__main__":
    CONFIG = config.CONFIG

    environ = CONFIG['env']['environ']
    print('Config environment: {}'.format(CONFIG['env']['environ']))

    DATA = BudgetData()
    db_file_ = CONFIG['database.{}'.format(environ)]['file']
    DATA.connect(db_file_)
    connection = DATA.dbConnection

    # ['q1', 'q2', 'q3', 'q4', 'all']
    for n in ['january', 'february', 'march', 'april', 'all']:
        print('\n\t{}'.format(n.upper()))
        DATA.category_summary(date_filter=n)

    DATA.close()
