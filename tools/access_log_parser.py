#access_log_parser.py

import requests
LOG_URL = r"https://www.pythonanywhere.com/user/nick450/files/var/log/nick450.pythonanywhere.com.access.log"


import re
LOG_FILE = r"D:\BartlettSync\code\ibudget_web\tools\access_log.log"

METHODS = ['GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH']

if __name__ == '__main__':
    with open(LOG_FILE, 'r') as log_file:
        events = log_file.readlines()

    ip_addresses = []
    for e in events:
        e = e.split('-')

        ip_address = e[0].replace(' ', '')
        ip_addresses.append(ip_address)

        if e[1] != ' ':
            user = e[1].split(' ')[1]
            for m in METHODS:
                try:
                    x = re.split(m, e[1])
                    print(ip_address, user, m, x[1])

                except:
                    pass
        else:
            user = 'n/a'
            for m in METHODS:
                try:
                    x = re.split(m, e[2])
                    print(ip_address, user, m, x[1])

                except:
                    pass


    # for a in set(ip_addresses):
    #     print(a)
