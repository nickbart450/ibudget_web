# page.py -- Base webpage class and associated functions for iBudget-web
# External Imports

from flask import render_template


# Internal Imports
from components import config


class Page:
    def __init__(self):
        self.config = config.reload()

    def render(self, template, **kwargs):
        self.config = config.reload()

        return render_template(
            template,
            **kwargs
        )


if __name__ == '__main__':
    print('a')
