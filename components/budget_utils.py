from budget_app import APP, LOGGER
from budget_data import DATA

from flask import redirect


@APP.route("/change-year-<year>&redirect=<url>", methods=['GET'])
def change_year(year, url):

    DATA.year = int(year)

    if DATA.year == 0:
        DATA.year = None

    DATA.set_year()

    return redirect('/{}'.format(url))
