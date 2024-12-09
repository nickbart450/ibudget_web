import os
import configparser

main_config_file = './config.ini'
environment_def_file = './environ.ini'

config_files = [
    main_config_file,
    environment_def_file
]


def write_out_environ():
    f = open(environment_def_file, 'a')
    f.writelines('[env]')
    f.writelines('\nenviron=live')
    f.close()


class AppConfig(configparser.ConfigParser):
    """
    To access setup parameters in Python code:
        From within DATA context, it is recommended to use self.config, the custom ConfigParser object containing values from config file
        For other external references, use budget_data.CONFIG object

        config['section']['setting_name'] will return the value from the config.ini file
    """
    def __init__(self):
        super().__init__()
        self.reload()

    def reload(self):
        self.read(config_files)
        # print('Config Reloaded')

    def update_setting(self, config_item, config_section, new_value):
        # print('address', config_section, '.', config_item)
        # print('current_val', self[config_section][config_item])
        # print('new_value', new_value)
        self[config_section][config_item] = new_value

        # print('new_val-confirm', self[config_section][config_item])

        self.remove_section('env')
        self.write_out_config()
        self.reload()

        return 'Success'

    def write_out_config(self):
        with open('config.ini', 'w') as configfile:
            self.write(configfile)
            # print('Write Successful')


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
