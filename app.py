from flask import Flask

# Create Flask Object
APP = Flask(__name__,
            template_folder="./templates",
            static_folder="./static", )
