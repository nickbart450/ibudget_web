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
            'Database': {'type': 'individual', 'data': None},
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
            'Database': 'database',
            'Category': 'db.Category',
            'Account': 'db.Account',
            # 'other': 'other'
        }

        for i in self.top_level_items:

            if mapping_dict[i].startswith('db'):
                # print('Database Fetch')
                func_map = {
                    'Category': DATA.get_categories().fillna("").to_dict('records'),
                    'Account': DATA.get_accounts().fillna("").to_dict('records'),
                }

                key_map = {
                    'Category': 'cat_id',
                    'Account': 'account_id',
                }

                db_table = mapping_dict[i].split('.')[1]

                self.setup_dict[db_table]['data'] = func_map[db_table]
                self.setup_dict[db_table]['id_key'] = key_map[db_table]

            else:
                # print('ConfigParser Fetch')
                if len(mapping_dict[i].split('.')) > 1:
                    options = mapping_dict[i].split('.')
                    # print('options', options)

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

        func_map = {
            'Category': DATA.update_category,
            'Account': DATA.update_account,
            'personal': config.update_setting,
        }

        update_form = request.form
        # print("update_form", request.form)

        keys = list(update_form.keys())

        for k in keys:
            # print(k, request.form.get(k))
            if request.form.get(k) == 'Update':
                update_type = k.split('.')[0]
                update_id = k.split('.')[1]

        # print("update_type", update_type)
        # print("update_id", update_id)

        update_dict = update_form.to_dict()
        print('update_dict', update_dict)

        if len(list(update_dict.keys())[0].split('.')) == 2:
            # If dictionary keys are x.y addresses - need to parse form table data
            new_vals = {}
            for i in list(update_dict.keys()):
                if i.split('.')[0] == update_id:
                    update_param = i.split('.')[1]  # which value within that section are we updating
                    new_vals[update_param] = update_dict[i]

        elif len(list(update_dict.keys())[0].split('.')) == 1:
            new_vals = {'config_section': 'personal',
                        'new_value': update_dict[update_id]}
        else:
            print('whoopsies')
            return

        print('new_vals', new_vals)

        func_map[update_type](update_id, **new_vals)  # call appropriate handling function


    def delete(self):
        """
        """
        func_map = {
            'cat_id': DATA.delete_category,
            'account_id': DATA.delete_account,
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
def update_setting():
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
