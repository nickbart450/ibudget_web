from budget_app import APP, LOGGER
from budget_data import DATA

from flask import redirect


@APP.route("/change-year-<year>&redirect=<url>", methods=['GET'])
def change_year(year, url):
    DATA.set_year(int(year))

    return redirect('/{}'.format(url))
