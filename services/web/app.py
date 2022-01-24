import os
import json
import itertools
import networkx as nx

from flask import Flask, flash, g, redirect, render_template, request, session
from flask import Blueprint

import redis

from flask_cors import CORS, cross_origin

try:
    from . import utils
except ImportError:
    import utils

PSS_URL = "http://web:5000/downloads/pss/pss-pssviz.json"
BASEDIR = os.path.dirname(__file__)


from flask_session import Session
sess = Session()

class PSS(object):
    """docstring for PSS"""
    def __init__(self):
        self.load()

    def load(self, headers={}):
        self._n, self._e, self._graph = utils.parseJSON(
             url=PSS_URL,
             path=os.path.join(BASEDIR, 'data/PSS-reactions.json'),
             headers=headers)
        self.full_json = utils.graph2json(self._n, self._e, self._graph)
        self.node_search_data = utils.get_autocomplete_node_data(self._graph)

# make global, update local
pss = PSS()

bp = Blueprint('bp', __name__,
               url_prefix='/biomine',
               static_folder='static/')

@bp.route('/get_node_data', methods=['GET', 'POST'])
def node_data():
    return pss.node_search_data

@bp.route('/get_network', methods=['GET', 'POST'])
def draw_network():
    return pss.full_json


@bp.route('/search', methods=['GET', 'POST'])
def search():
    try:
        data = request.get_json(force=False)
        query_nodes = set(data.get('nodes'))
    except Exception as e:
        return {'error': 'Invalid query data'}

    subgraph = utils.extract_shortest_paths(pss._graph, query_nodes, ignoreDirection=True)
    return utils.graph2json(pss._n, pss._e, subgraph, query_nodes=query_nodes)


@bp.route('/expand', methods=['GET', 'POST'])
def expand():
    try:
        data = request.get_json(force=False)
        query_nodes = set(data.get('nodes'))
    except Exception as e:
        return {'error': 'Invalid query data'}

    subgraph = utils.expand_nodes(pss._graph, list(query_nodes))
    return utils.graph2json(pss._n, pss._e, subgraph)


@bp.route('/')
@cross_origin()
def main():
    if '_user_id' in session:
        headers = headers={'Userid':session['_user_id']}
    else:
        headers = {}

    # refresh pss
    pss.load(headers=headers)

    return render_template('index.html')

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)

    rport = 6379
    rs = redis.Redis(host='redis', port=rport)
    try:
        rs.ping()
    except redis.exceptions.ConnectionError:
        print(f'Warning: Redis is not running on port {rport}. Not using this setting.')
    else:
        app.config.from_mapping(
            # Flask Session settings
            SESSION_TYPE = 'redis',
            SESSION_REDIS = redis.Redis(host='redis', port=rport)
        )
    sess.init_app(app)
    app.register_blueprint(bp)

    return app

app = create_app()
