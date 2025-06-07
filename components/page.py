# page.py -- Base webpage class and associated functions for iBudget-web

# External Imports
from flask import render_template


# Internal Imports
from budget_data import CONFIG, DATA


class Page:
    def __init__(self):
        self.config = CONFIG
        self.config.reload()
        self.render_dict = {}

    def render(self, template, **kwargs):
        self.config.reload()

        # print({**kwargs})
        return render_template(
            template,
            **kwargs
        )


if __name__ == '__main__':
    print('a')
