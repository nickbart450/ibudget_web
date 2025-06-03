import os
import configparser

main_config_file = './config.ini'
environment_def_file = './environ.ini'

config_files = [
    main_config_file,
    environment_def_file
]

# Safer to add and remove elements from this section and the ini file
# TODO: Add manual "Save Config File" button to setup poge? Force a write to disk.
config_defaults = {
    'database': {
        'live': '/home/nick450/budget_db/budget_2023-2025.db',
        'home': 'C:/Users/nickd/Documents/budget_db/budget_2023-2025.db'
    },
    'home': {
        'account_values_stacked_chart_start_date': '1970-01-01',
        'account_values_stacked_chart_end_date': '2100-12-31',
        'account_values_stacked_chart_max': 100000.00,
        'burn_time_chart_max': 48,
        'burn_time_chart_interval': 6,
    },
    'personal': {
        'average_monthly_expend': 5000.00,
        'pay_day': 'Friday',
        'first_pay_day': '1970-01-01',
        'retirement_tax_rate': 0.30
    },
    'ui_settings': {'include_retirement_in_burn': 'false'},
    'ui_settings.default_filters': {'date': 'All',
                                    'account': 'All',
                                    'category': 'All',
                                    'income_expense': 'both'},
    'ui_settings.date_filters': {'all': '1970-01-01,2100-12-31',
                                 'january': 'yyyy-01-01,yyyy-01-31',
                                 'february': 'yyyy-02-01,yyyy-02-31',
                                 'march': 'yyyy-03-01,yyyy-03-31',
                                 'april': 'yyyy-04-01,yyyy-04-31',
                                 'may': 'yyyy-05-01,yyyy-05-31',
                                 'june': 'yyyy-06-01,yyyy-06-31',
                                 'july': 'yyyy-07-01,yyyy-07-31',
                                 'august': 'yyyy-08-01,yyyy-08-31',
                                 'september': 'yyyy-09-01,yyyy-09-31',
                                 'october': 'yyyy-10-01,yyyy-10-31',
                                 'november': 'yyyy-11-01,yyyy-11-31',
                                 'december': 'yyyy-12-01,yyyy-12-31',
                                 'q1': 'yyyy-01-01,yyyy-03-31',
                                 'q2': 'yyyy-04-01,yyyy-06-31',
                                 'q3': 'yyyy-07-01,yyyy-09-31',
                                 'q4': 'yyyy-10-01,yyyy-12-31'},
}


def write_out_environ():
    f = open(environment_def_file, 'a')
    f.writelines('[env]')
    f.writelines('\nenviron=live')
    f.close()


class AppConfig(configparser.ConfigParser):
    """
    A custom ConfigParser object containing values from config file

    To access setup parameters in Python code:
        From within DATA context, it is recommended to use self.config
        From within page objects, it is recommended to use self.config
        For other external references, use budget_data.CONFIG object

        Ultimately, everything points to single CONFIG object

        CONFIG['section']['setting_name'] will return the value from the config.ini file
    """

    def __init__(self):
        super().__init__()
        self.read_dict(config_defaults)
        print('Config Created')
        # print('Default Config Dict: ', {s: dict(self.items(s)) for s in self.sections()})

    def reload(self):
        self.read(config_files)
        print('Config (Re)loaded')
        # print('Reloaded Config Dict: ', {s: dict(self.items(s)) for s in self.sections()})

    def update_setting(self, config_item, config_section, new_value):
        """Updates a configuration setting (config_item) in 1 section to a new value"""

        # print('address', config_section, '.', config_item)
        # print('current_val', self[config_section][config_item])
        # print('new_value', new_value)
        self[config_section][config_item] = new_value
        # print('new_val-confirm', self[config_section][config_item])

        self.write_out_config()
        # self.reload()

        return 'Success'

    def write_out_config(self):
        self.remove_section('env')

        with open('config.ini', 'w') as configfile:
            self.write(configfile)
            print('Write Successful')


for i in range(len(config_files)):
    file = os.path.abspath(config_files[i])
    config_files[i] = file
    if not os.path.exists(file):
        print('File {} not found'.format(file))
        if file == os.path.abspath(environment_def_file):
            print('No environ.ini file found. Rebuilding assuming live environment')
            write_out_environ()
        else:
            raise FileNotFoundError(file)


if __name__ == '__main__':
    # Load Config File(s)
    # CONFIG = configparser.ConfigParser()
    CONFIG = AppConfig()
    CONFIG.read(config_files)
