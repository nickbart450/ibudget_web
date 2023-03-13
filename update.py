from budget_app import APP

from flask import request
import subprocess
import hmac
import hashlib


@APP.route("/update_server", methods=['POST'])
def git_update():
    """
    Git webhook receiving address

    :return:
    """
    print('Receiving webhook from GitHub')
    if request.method == 'POST':
        x_hub_signature = request.headers.get('X - Hub - Signature')
        if not is_valid_signature(x_hub_signature, request.data):
            return 'Invalid Signature', 401
        else:
            subprocess.call(['git', 'pull'])
            return 'Updated PythonAnywhere successfully', 200
    else:
        return 'Wrong event type', 400


def is_valid_signature(x_hub_signature, data, private_key='jwtmJPl0P6AmtCqg_l3Fag'):
    # x_hub_signature and data are from the webhook payload
    hash_algorithm, github_signature = x_hub_signature.split('=', 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, 'latin-1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    print('hmac compare', hmac.compare_digest(mac.hexdigest(), github_signature))
    return hmac.compare_digest(mac.hexdigest(), github_signature)
