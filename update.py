from budget_app import APP
from flask import request
import subprocess


@APP.route("/update_server", methods=['POST'])
def git_update():
    """
    Git webhook receiving address

    :return:
    """
    print('Receiving webhook from GitHub')
    if request.method == 'POST':
        subprocess.call(['git', 'pull'])
        return 'Updated PythonAnywhere successfully', 200
    else:
        return 'Wrong event type', 400
