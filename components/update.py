from budget_app import APP, LOGGER

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
    if request.method == 'POST':
        x_hub_signature = request.headers.get('X-Hub-Signature')
        LOGGER.debug('x_hub_signature: ', x_hub_signature)

        if not is_valid_signature(x_hub_signature, request.data):
            LOGGER.error('failed signature check on webhook post')
            return 'Invalid Signature', 401

        else:
            print('*** Received UPDATE webhook from GitHub')
            LOGGER.debug('*** Received UPDATE webhook from GitHub')
            subprocess.call(['git', 'pull'])
            return 'Updated PythonAnywhere successfully', 200

    else:
        return 'Wrong event type', 400


def is_valid_signature(x_hub_signature, data, private_key='jwtmJPl0P6AmtCqg_l3Fag'):
    # x_hub_signature and data are from the webhook payload
    hash_algorithm, github_signature = x_hub_signature.split('=', 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    LOGGER.debug('algorithm = {}'.format(algorithm))
    LOGGER.debug('signature = {}'.format(github_signature))

    encoded_key = bytes(private_key, 'latin-1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    LOGGER.debug('hmac compare', hmac.compare_digest(mac.hexdigest(), github_signature))

    return hmac.compare_digest(mac.hexdigest(), github_signature)
