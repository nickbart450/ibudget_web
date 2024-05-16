import pandas as pd

from components import page, config
from budget_app import APP, LOGGER
from budget_data import DATA, fetch_filtered_transactions
from flask import request, render_template, redirect, url_for


class SetupPage(page.Page):
    def __init__(self):
        """
        /analyze/<arguments>
        """

        super().__init__()
        self.template = 'app_setup.html'
        self.name = 'setup'

        self.setup_dict = {
            'App': {'type': 'individual', 'data': None},
            'Category': {'type': 'table', 'data': None},
            'Account': {'type': 'table', 'data': None},
            # 'other': None,
        }

        self.top_level_items = list(self.setup_dict.keys())
        self.top_level_items = [i.title() for i in self.top_level_items]

        self.render_dict = {
            "tree_top_level": self.top_level_items,
        }

    def get(self):
        """Fetch appropriate data and render page from template"""
        mapping_dict = {
            'App': 'personal',
            'Category': 'db.Category',
            'Account': 'db.Account',
            # 'other': 'other'
        }

        for i in self.top_level_items:

            if mapping_dict[i].startswith('db'):
                print('Database Fetch')
                func_map = {
                    'Category': DATA.get_categories().to_dict('records'),
                    'Account': DATA.accounts.to_dict('records'),
                }

                db_table = mapping_dict[i].split('.')[1]

                self.setup_dict[db_table]['data'] = func_map[db_table]

            else:
                print('ConfigParser Fetch')
                if len(mapping_dict[i].split('.')) > 1:
                    #
                    options = mapping_dict[i].split('.')
                    print('options', options)

                    # key = config.CONFIG.get(options[0], options[1]).replace('\n', '').split(',')
                    # value =
                    self.setup_dict[i]['data'] = config.CONFIG.get(options[0], options[1]).replace('\n', '').split(',')

                else:
                    self.setup_dict[i]['data'] = {}

                    indiv_settings = config.CONFIG.options(mapping_dict[i])

                    # print('indiv_settings', indiv_settings)
                    # print('mapping_dict[i]', mapping_dict[i])
                    for t in indiv_settings:
                        # print('\tt', t)
                        # print(config.CONFIG.get(mapping_dict[i], t))

                        self.setup_dict[i]['data'][t] = config.CONFIG.get(mapping_dict[i], t)

        print('setup_dict', self.setup_dict)
        self.render_dict['setup_dict'] = self.setup_dict

        return render_template(self.template, **self.render_dict)

    def update(self):
        """
        TODO: Add db_propogate option to update all matching entries in transaction db to new value
        """
        def category_update(c, new):
            print('NOT IMPLEMENTED')

            c = c.replace('_', ' ')
            print('updating category', c, 'to', new)

        def account_update(a, new):
            print('NOT IMPLEMENTED')

            print('updating account', a, 'to', new)

        func_map = {
            'Category': category_update,
            'Account': account_update,
        }

        print(request.form.to_dict())

        if len(request.form.to_dict()) > 1:
            # Updating multiple values from table row
            update_form = request.form.to_dict()  # selector code
            keys = list(request.form.to_dict().keys())  # selector code
            print("update_form", update_form)
            # print("keys", keys)

            update_type = keys[0].split('.')[0]  # which section are we updating
            print("update_type", update_type)

            for i in keys:
                if len(i.split('.')) < 3:
                    # print('i too short')
                    continue

                update_id = i.split('.')[1]  # which value within that section are we updating
                # print("\tupdate_id", update_id)

                update_param = i.split('.')[2]  # which value within that section are we updating
                # print("\tupdate_param", update_param)

                new_val = update_form[i]  # new value\
                # print("\tnew_val", new_val)

                func_map[update_type](update_id, new_val)  # call appropriate handling function

        else:
            # Updating single value from list
            update_form = list(request.form.keys())[0]  # selector code

            update_type = update_form.split('.')[0]  # which section are we updating
            print("\tupdate_type", update_type)

            update_item = update_form.split('.')[1]  # which value within that section are we updating
            print("\tupdate_item", update_item)

            new_val = request.form.get(update_form)  # new value
            print("\tnew_val", new_val)

            func_map[update_type](update_item, new_val)     # call appropriate handling function

    def delete(self):
        """
        """
        def account_delete(a):
            print('NOT IMPLEMENTED')

            print('deleting account', a)

        func_map = {
            'cat_id': DATA.delete_category,
            # 'account_id': DATA.delete_account,
        }

        print(request.args.to_dict())

        delete_type = list(request.args.to_dict().keys())[0]  # which section are we updating
        delete_id = list(request.args.to_dict().values())[0]  # which value within that section are we updating
        func_map[delete_type](delete_id)     # call appropriate handling function

    def new(self):
        print(request.form.to_dict())

        func_map = {
            'cat_id': DATA.add_category,
            'account_id': DATA.add_account,
        }

        required_inputs = {
            'cat_id': ['name'],
            'account_id': ['name', 'account_type', 'transaction_type'],
        }

        key = list(request.form.keys())[0]

        for i in required_inputs[key]:
            if request.form.to_dict()[i] == '':
                # TODO: Fix behavior to prompt/warn user. JS?
                print('MISSING REQUIRED VALUES - RETURNING')
                return

        func_map[key](**request.form.to_dict())  # should only use the first entry for list entries


SETUP_PAGE = SetupPage()


@APP.route("/setup/", methods=['GET'])
def app_setup():
    """
    :return: render_template
    """

    return SETUP_PAGE.get()


@APP.route("/setup/update/", methods=['POST'])
def update():
    """

    :return: redirect
    """
    SETUP_PAGE.update()
    return redirect(url_for('app_setup'))

@APP.route("/setup/delete/", methods=['GET'])
def delete():
    """

    :return: redirect
    """
    SETUP_PAGE.delete()
    return redirect(url_for('app_setup'))

@APP.route("/setup/new/", methods=['POST'])
def new_setting():
    """

    :return: redirect
    """
    SETUP_PAGE.new()
    return redirect(url_for('app_setup'))

# @APP.route("/transact/update_transaction", methods=['POST'])
# def update_transaction():
#     TRANSACTION_PAGE.update()
#     return redirect(TRANSACTION_PAGE.current_filter_url())
#
#
# @APP.route("/transact/delete_transaction", methods=['GET'])
# def delete_transaction():
#     TRANSACTION_PAGE.delete()
#     return redirect(TRANSACTION_PAGE.current_filter_url())