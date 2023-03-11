from budget_app import APP
from budget_data import DATA
from flask import request, redirect, url_for


@APP.route("/transact/submit_transaction", methods=['POST'])
def submit_transaction():
    """
    /transact/submit_transaction

    Accessed by form

    :return: redirect
    """
    print('POSTing transaction')
    transaction_date = request.form['date']
    posted_date = request.form['post_date']
    credit_account = request.form['account-credit']
    debit_account = request.form['account-debit']
    amount = request.form['amount']
    category = request.form['category']
    description = request.form['description']
    vendor = request.form['vendor']
    posted_flag = request.form.get('is_posted_selector')

    if posted_flag == 'on':
        posted_flag = True
    else:
        posted_flag = False

    credit_account = int(DATA.accounts[DATA.accounts['name'] == credit_account]['account_id'])

    if debit_account == '':
        debit_account = None
    else:
        debit_account = int(DATA.accounts[DATA.accounts['name'] == debit_account]['account_id'])

    DATA.add_transaction(
        transaction_date=transaction_date,
        category=category,
        amount=amount,
        posted_date=posted_date,
        credit_account=credit_account,
        debit_account=debit_account,
        description=description,
        vendor=vendor,
        is_posted=posted_flag)
    return redirect(url_for('data_transactions'))


@APP.route("/transact/update_transaction", methods=['POST'])
def update_transaction():
    print('POSTing transaction update')
    transaction_id = request.args.get('transaction_id')

    transaction_date = request.form['date']
    posted_date = request.form['post_date']
    credit_account = request.form['account-credit']
    debit_account = request.form['account-debit']
    amount = request.form['amount']
    category = request.form['category']
    description = request.form['description']
    vendor = request.form['vendor']
    posted_flag = request.form.get('is_posted_selector')
    if posted_flag == 'on':
        posted_flag = True
    else:
        posted_flag = False

    DATA.update_transaction(transaction_id,
                            transaction_date=transaction_date,
                            posted_date=posted_date,
                            category=category,
                            amount=amount,
                            credit_account=credit_account,
                            debit_account=debit_account,
                            description=description,
                            vendor=vendor,
                            is_posted=posted_flag)

    return redirect(url_for('data_transactions'))


@APP.route("/transact/delete_transaction", methods=['GET'])
def delete_transaction():
    print('Deleting transaction')
    transaction_id = request.args.get('transaction_id')
    DATA.delete_transaction(transaction_id)
    return redirect(url_for('data_transactions'))