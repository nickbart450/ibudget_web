from components import page, config
from budget_app import APP, LOGGER
from budget_data import DATA, fetch_filtered_transactions
from flask import request, render_template, redirect, url_for, jsonify


class SetupItem:
    def __init__(self, name, data_source, setup_type):
        self.data_source = data_source
        self.name = name
        self.setup_type = setup_type
        # print('init SetupItem {}'.format(name))
        # print('data source: ', self.data_source)
        self.data = None

        if self.data_source == 'config':
            self.load_config()

    def load_config(self):
        self.data = {}
        indiv_settings = DATA.config.options(self.name)

        for t in indiv_settings:
            self.data[t] = DATA.config.get(self.name, t)


class HomeSetup(SetupItem):
    def __init__(self):
        super().__init__('home', 'config', 'individual')


class PersonalSetup(SetupItem):
    def __init__(self):
        super().__init__('personal', 'config', 'individual')


class DatabaseSetup(SetupItem):
    def __init__(self):
        super().__init__('database', 'config', 'individual')


class CategorySetup(SetupItem):
    def __init__(self):
        super().__init__('Category', 'database', 'table')
        self.data = DATA.categories.to_dict('records')

    def update_category(self, update_json):
        for row in update_json:
            response = DATA.update_category(
                row['cat_id'],
                cat_id=row['cat_id'],
                category_name=str(row['category_name']),
                description=str(row['description'])
            )
            if response != 'Success':
                print('!!!!!!!!!!! ERROR !!!!!!!!!!')
        self.data = DATA.categories.to_dict('records')


class AccountSetup(SetupItem):
    def __init__(self):
        super().__init__('Account', 'database', 'table')
        self.data = DATA.accounts.to_dict('records')

    def update_account(self, update_json):
        for row in update_json:
            response = DATA.update_account(
                row['account_id'],
                account_id=row['account_id'],
                account_name=str(row['account_name']),
                account_type=str(row['account_type']),
                transaction_type=str(row['transaction_type']),
                starting_value=str(row['starting_value']),
            )
            if response != 'Success':
                print('!!!!!!!!!!! ERROR !!!!!!!!!!')
        self.data = DATA.accounts.to_dict('records')


class LinksSetup(SetupItem):
    def __init__(self):
        super().__init__('links', 'config', 'list')

        self.data = self.get_links()

    def get_links(self):
        links_data = []
        index = 0
        for i in DATA.config['links']:
            print(i, index, DATA.config['links'][i])
            links_data.append({'link_id': index, 'link_url': DATA.config['links'][i]})
            index += 1

        return links_data

    def add_link(self, link_url):
        # print('adding link')
        key = len(DATA.config['links'])+1
        DATA.config.add_setting('links', str(key), link_url)

        self.data = []
        for i in DATA.config['links']:
            self.data.append({'link_id': i, 'link_url': DATA.config['links'][i]})

    def delete_link(self, link_id):
        # print('removing link: ', link_id)
        DATA.config.remove_option('links', link_id)
        DATA.config.write_out_config()

        self.data = []
        for i in DATA.config['links']:
            # print(i, DATA.config['links'][i])
            self.data.append({'link_id': i, 'link_url': DATA.config['links'][i]})

    def update_links(self, update_json):
        listy = []
        for l in update_json:
            listy.append(l['link_url'])

        DATA.config.update_list('links', listy)

        self.data = []
        for i in DATA.config['links']:
            # print(i, DATA.config['links'][i])
            self.data.append({'link_id': i, 'link_url': DATA.config['links'][i]})


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

        self.home = HomeSetup()
        self.personal = PersonalSetup()
        self.database = DatabaseSetup()
        self.category = CategorySetup()
        self.account = AccountSetup()
        self.links_setup = LinksSetup()

        self.setup_dict = {
            'Home':     {'name': 'home', 'type': 'individual', 'source': 'config', 'data': None},
            'Personal': {'name': 'personal', 'type': 'individual', 'source': 'config', 'data': None},
            'Database': {'name': 'database', 'type': 'individual', 'source': 'config', 'data': None},
            'Category': {'name': 'Category', 'type': 'table', 'source': 'database', 'data': None},
            'Account':  {'name': 'Account', 'type': 'table', 'source': 'database', 'data': None},
            'Links':    {'name': 'links', 'type': 'list', 'source': 'config', 'data': None},
        }

        self.top_level_items = list(self.setup_dict.keys())  # top_level_items sets the list of available tabs for setup

    def get(self):
        """Fetch appropriate data and render page from template"""
        print('Fetching {}'.format(self.name))

        render_dict = self.render_dict
        render_dict["tree_top_level"] = self.top_level_items

        render_dict['setup_dict'] = self.setup_dict
        render_dict['setup_dict']['Home']['data'] = self.home.data          # Home data is dict of setting:value
        render_dict['setup_dict']['Personal']['data'] = self.personal.data  # Personal data is dict of setting:value
        render_dict['setup_dict']['Database']['data'] = self.database.data  # Database data is dict of setting:value
        render_dict['setup_dict']['Category']['data'] = self.category.data  # Category data is list of dicts for each row in the table
        render_dict['setup_dict']['Account']['data'] = self.account.data    # Account data is list of dicts for each row in the table
        render_dict['setup_dict']['Links']['data'] = self.links_setup.data  # Link data is list of dicts {'link_id': value, 'link_url': value}
        print('Setup render_dict: ', render_dict)

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
    return jsonify({'data': SETUP_PAGE.category.data})


@APP.route("/setup/_account_table_data/", methods=['GET'])
def account_data():
    """
    API endpoint to fetch account list
    """
    return jsonify({'data': SETUP_PAGE.account.data})


@APP.route("/setup/_links_table_data/", methods=['GET'])
def links_data():
    """
    API endpoint to fetch link list
    """
    return jsonify({'data': SETUP_PAGE.links_setup.data})


@APP.route("/setup/update/", methods=['POST'])
def update_setup():
    """
    API endpoint to update settings

    TODO: Add db_propogate option to update all matching entries in transaction db to new value

    :return: redirect
    """
    if request.is_json:
        update_json = request.get_json()
        LOGGER.debug("update_json")
        LOGGER.debug(update_json)
        print('update_json', update_json)

        if 'cat_id' in update_json[0].keys():
            SETUP_PAGE.category.update_category(update_json)
        elif 'account_id' in update_json[0].keys():
            SETUP_PAGE.account.update_account(update_json)
        elif 'link_id' in update_json[0].keys():
            SETUP_PAGE.links_setup.update_links(update_json)

    else:
        update_form = request.form
        LOGGER.debug("update_form")
        LOGGER.debug(update_form)
        # print("update_form", request.form)

        update_dict = update_form.to_dict()
        # print("update_dict", update_dict)
        update_type = update_dict.pop('type')
        # print('update_type', update_type)

        for update_id in update_dict.keys():
            update = {'config_section': update_type.lower(),
                      'new_value': update_dict[update_id]}

            SETUP_PAGE.config.update_setting(update_id, **update)  # call appropriate handling function

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
    # print(request.form.to_dict())

    func_map = {
        'cat_id': DATA.add_category,
        'account_id': DATA.add_account,
        'link_url': SETUP_PAGE.links_setup.add_link,
    }

    required_inputs = {
        'cat_id': ['category_name'],
        'account_id': ['account_name', 'account_type', 'transaction_type'],
        'link_url': ['link_url'],
    }

    key = list(request.form.keys())[0]

    missing_vals = []
    for i in required_inputs[key]:
        if request.form.to_dict()[i] == '':
            missing_vals.append(i)

    if len(missing_vals) == 0:
        func_map[key](**request.form.to_dict())  # should only use the first entry for list entries
        return redirect(url_for('app_setup'))
    else:
        e_text = 'MISSING REQUIRED VALUES - {}'.format(missing_vals)
        return render_template('warning.html', error_text=e_text, return_address='/setup')


@APP.route("/setup/delete/", methods=['POST'])
def delete():
    """
    Only deletes database rows in approved tables

    :return: redirect
    """
    func_map = {
        'category': DATA.delete_category,
        'account': DATA.delete_account,
        'Links': SETUP_PAGE.links_setup.delete_link,
    }

    data = request.form.to_dict()
    # print('DELETE\n', request.form.to_dict())
    LOGGER.debug('/delete request.form.to_dict()')
    LOGGER.debug(request.form.to_dict())

    delete_type = data['type']
    delete_id = data['id']

    func_map[delete_type](delete_id)  # call appropriate handling function

    return redirect(url_for('app_setup'))
