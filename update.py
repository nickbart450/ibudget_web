from budget_app import APP, ROOT
from flask import request
import subprocess


@APP.route("/update_server", methods=['POST'])
def git_update():
    """
    Git webhook receiving address

    :return:
    """
    print('Receiving UPDATE hook from GitHub!')
    if request.method == 'POST':
        r = subprocess.call(['git', 'pull'])
        print('Subprocess Return: ', r)
        return 'Updated PythonAnywhere successfully', 200
    else:
        return 'Wrong event type', 400
