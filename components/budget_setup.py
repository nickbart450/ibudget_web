from components import page, config
from budget_app import APP, LOGGER
from budget_data import DATA, fetch_filtered_transactions
from flask import request, render_template, redirect, url_for, jsonify


class SetupPage(page.Page):
    def __init__(self):
        """
        /setup/<arguments>

        Note: No arguments supported at this time

        TODO: update db ACCOUNTS table to add starred toggle for hiding/showing accounts in sidebar
            - rest would need to be visible in a new location. Standalone //ACCOUNTS page??
        TODO: add list of acceptable account inputs to config.ini, use these lists for dropdowns in new_setting modal
        TODO: add detection for input types: numeric, boolean, text to style setup more cleanly
        """

        super().__init__()
        self.template = 'app_setup.html'
        self.name = 'setup'

        self.setup_dict = {
            'Home': {'type': 'individual', 'data': None},
            'Personal': {'type': 'individual', 'data': None},
            'Database': {'type': 'individual', 'data': None},
            'Category': {'type': 'table', 'data': None},
            'Account': {'type': 'table', 'data': None},
            # 'other': None,
        }

        self.top_level_items = list(self.setup_dict.keys())
        # self.top_level_items = [i.title() for i in self.top_level_items]

    def get(self):
        """Fetch appropriate data and render page from template"""
        print('Fetching {}'.format(self.name))

        mapping_dict = {
            'Home': 'home',
            'Personal': 'personal',
            'Database': 'database',
            'Category': 'db.Category',
            'Account': 'db.Account',
        }

        for i in self.top_level_items:
            if mapping_dict[i].startswith('db'):
                # print('Database Fetch')
                func_map = {
                    'Category': DATA.categories.fillna("").to_dict('records'),
                    'Account': DATA.accounts.fillna("").to_dict('records'),
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

                    self.setup_dict[i]['data'] = self.config.get(options[0], options[1]).replace('\n', '').split(',')

                else:
                    self.setup_dict[i]['data'] = {}

                    indiv_settings = self.config.options(mapping_dict[i])

                    # print('indiv_settings', indiv_settings)
                    # print('mapping_dict[i]', mapping_dict[i])
                    for t in indiv_settings:
                        # print('\tt', t)
                        # print(self.config.get(mapping_dict[i], t))

                        self.setup_dict[i]['data'][t] = self.config.get(mapping_dict[i], t)

        print('setup_dict', self.setup_dict)
        LOGGER.debug('setup_dict')
        LOGGER.debug(self.setup_dict)

        render_dict = self.render_dict
        render_dict['setup_dict'] = self.setup_dict
        render_dict["tree_top_level"] = self.top_level_items

        return self.render(self.template, **render_dict)


SETUP_PAGE = SetupPage()


@APP.route("/setup/", methods=['GET'])
def app_setup():
    """
    :return: render_template
    """

    return SETUP_PAGE.get()


@APP.route("/setup/_category_table_data/", methods=['GET'])
def category_data():
    """
    API endpoint to fetch category list
    """
    return jsonify({'data': DATA.categories.to_dict('records')})


@APP.route("/setup/_account_table_data/", methods=['GET'])
def account_data():
    """
    API endpoint to fetch account list
    """
    return jsonify({'data': DATA.accounts.to_dict('records')})


@APP.route("/setup/update/", methods=['POST'])
def update_setup():
    """
    API endpoint to update settings

    TODO: Add db_propogate option to update all matching entries in transaction db to new value

    :return: redirect
    """
    confirm = []

    try:
        # print(request.get_json())
        update_json = request.get_json()
        LOGGER.debug("update_json")
        LOGGER.debug(update_json)

        for row in update_json:
            # print(row)
            if 'cat_id' in row.keys():
                # print('cat_id detected')
                response = DATA.update_category(
                    row['cat_id'],
                    cat_id=row['cat_id'],
                    category_name=str(row['category_name']),
                    description=str(row['description'])
                )
            elif 'account_id' in row.keys():
                # print('account_id detected')
                response = DATA.update_account(
                    row['account_id'],
                    account_id=row['account_id'],
                    account_name=str(row['account_name']),
                    account_type=str(row['account_type']),
                    transaction_type=str(row['transaction_type']),
                    starting_value=str(row['starting_value']),
                )
            else:
                response = "Error"
            confirm.append(response)

    except:
        func_map = {
            'home': SETUP_PAGE.config.update_setting,
            'personal': SETUP_PAGE.config.update_setting,
            'database': SETUP_PAGE.config.update_setting,
        }

        # print("update_form", request.form)
        update_form = request.form
        LOGGER.debug("update_form")
        LOGGER.debug(update_form)

        update_dict = update_form.to_dict()
        print("update_dict", update_dict)
        update_type = update_dict.pop('type')
        # print('update_type', update_type)

        for update_id in update_dict.keys():
            # print('update_id: ', update_id, 'new value: ', update_dict[update_id])
            update = {'config_section': update_type.lower(),
                      'new_value': update_dict[update_id]}

            response = func_map[update_type](update_id, **update)  # call appropriate handling function
            confirm.append(response)

    for response in confirm:
        if 'err' in response.lower():
            e_text = 'UPDATE FAILED - {}'.format(response)
            return render_template('warning.html', error_text=e_text, return_address='/setup')

    return redirect(url_for('app_setup'))


@APP.route("/setup/delete/", methods=['POST'])
def delete():
    """
    Only deletes database rows in approved tables

    :return: redirect
    """
    func_map = {
        'category': DATA.delete_category,
        'account': DATA.delete_account,
    }

    data = request.form.to_dict()
    # print(request.form.to_dict())
    LOGGER.debug('/delete request.form.to_dict()')
    LOGGER.debug(request.form.to_dict())

    delete_type = data['type']
    delete_id = data['id']

    func_map[delete_type](delete_id)  # call appropriate handling function

    return redirect(url_for('app_setup'))


@APP.route("/setup/new/", methods=['POST'])
def new_setting():
    """
    TODO: Make required inputs required in the HTML form

    Only adds database rows in approved tables

    :return: redirect
    """
    LOGGER.debug('/new request.args.to_dict()')
    LOGGER.debug(request.args.to_dict())

    func_map = {
        'cat_id': DATA.add_category,
        'account_id': DATA.add_account,
    }

    required_inputs = {
        'cat_id': ['category_name'],
        'account_id': ['account_name', 'account_type', 'transaction_type'],
    }

    key = list(request.form.keys())[0]

    missing_vals = []
    for i in required_inputs[key]:
        if request.form.to_dict()[i] == '':
            missing_vals.append(i)

    if len(missing_vals) == 0:
        # TODO: add warning page catch here
        func_map[key](**request.form.to_dict())  # should only use the first entry for list entries
        return redirect(url_for('app_setup'))
    else:
        e_text = 'MISSING REQUIRED VALUES - {}'.format(missing_vals)
        return render_template('warning.html', error_text=e_text, return_address='/setup')

