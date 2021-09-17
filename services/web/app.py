import os
import json
import networkx as nx

from flask import Flask, flash, g, redirect, render_template, request, session
from flask_cors import CORS, cross_origin

from . import utils

BASEDIR = os.path.dirname(__file__)
with open(os.path.join(BASEDIR, 'data/pis.json')) as fp:
    pis_json = json.load(fp)


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    @app.route('/get_network', methods=['GET', 'POST'])
    def draw_network():
        return pis_json

    @app.route('/')
    @cross_origin()
    def main():
        return render_template('index.html')

    return app
