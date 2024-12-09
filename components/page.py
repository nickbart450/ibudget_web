# page.py -- Base webpage class and associated functions for iBudget-web
# External Imports

from flask import render_template


# Internal Imports
from budget_data import CONFIG


class Page:
    def __init__(self):
        self.config = CONFIG

    def render(self, template, **kwargs):
        self.config.reload()

        return render_template(
            template,
            **kwargs
        )


if __name__ == '__main__':
    print('a')
