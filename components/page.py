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
        self.links = []

    def render(self, template, **kwargs):
        # print({**kwargs})
        self.config.reload()

        self.links = [i[1] for i in DATA.config.items('links')]

        return render_template(
            template,
            links=self.links,
            **kwargs
        )


if __name__ == '__main__':
    print('a')
