import os
import json
import itertools
import networkx as nx

from flask import Flask, flash, g, redirect, render_template, request, session
from flask import Blueprint
from flask_cors import CORS, cross_origin

try:
    from . import utils
except ImportError:
    import utils

BASEDIR = os.path.dirname(__file__)
# with open(os.path.join(BASEDIR, 'data/pss_visjs.json')) as fp:
#     pss_visjs = json.load(fp)
# with open(os.path.join(BASEDIR, 'data/pss_g6.json')) as fp:
#     pss_g6 = json.load(fp)

#_n, _e, _graph = utils.parseJSON(os.path.join(BASEDIR, 'data/PSS-latest.json'))
_n, _e, _graph = utils.parseJSON(os.path.join(BASEDIR, 'data/PSS-reactions.json'))
full_json = utils.graph2json(_n, _e, _graph)
node_search_data = utils.get_autocomplete_node_data(_graph)

bp = Blueprint('bp', __name__,
               url_prefix='/biomine',
               static_folder='static/')

@bp.route('/get_node_data', methods=['GET', 'POST'])
def node_data():
    return node_search_data

@bp.route('/get_network', methods=['GET', 'POST'])
def draw_network():
    return full_json

# @app.route('/get_network_g6', methods=['GET', 'POST'])
# def draw_network_g6():
#     return {} #pss_g6

@bp.route('/search', methods=['GET', 'POST'])
def search():
    try:
        data = request.get_json(force=False)
        query_nodes = set(data.get('nodes'))
    except Exception as e:
        return {'error': 'Invalid query data'}

    subgraph = utils.extract_shortest_paths(_graph, query_nodes, ignoreDirection=True)
    return utils.graph2json(_n, _e, subgraph)

@bp.route('/')
@cross_origin()
def main():
    return render_template('index.html')

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    # @app.route('/full')
    # @cross_origin()
    # def draw_full():
    #     return full_json
    #
    app.register_blueprint(bp)
    return app

app = create_app()
