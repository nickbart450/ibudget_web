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


def reload():
    global CONFIG
    CONFIG = configparser.ConfigParser()
    CONFIG.read(config_files)
    return CONFIG


# Load Config File(s)
CONFIG = configparser.ConfigParser()
CONFIG.read(config_files)
