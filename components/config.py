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


def write_out_config(new_config):
    with open('config.ini', 'w') as configfile:
        new_config.write(configfile)


def reload():
    global CONFIG
    CONFIG = configparser.ConfigParser()
    CONFIG.read(config_files)
    return CONFIG


def update_setting(config_item, config_section, new_value):
    global CONFIG
    # print('address', config_section, '.', config_item)
    # print('new_value', new_value)
    # print('current_val', CONFIG[config_section][config_item])
    CONFIG[config_section][config_item] = new_value

    # print('new_val', CONFIG[config_section][config_item])

    CONFIG.remove_section('env')

    write_out_config(CONFIG)
    print('Write Successful')
    return 'Success'


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

# Load Config File(s)
CONFIG = configparser.ConfigParser()
CONFIG.read(config_files)
