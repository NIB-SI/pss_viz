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
        # backup: the local copy (data/PSS-reactions.json), when PSS_URL can't be read
        self._n, self._e, self._graph, self.backup = utils.parseJSON(
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
        directed_search = data.get('directed_search')
        force_neighbourhood = data.get('force_neighbourhood', False)

    except Exception as e:
        return {'error': 'Invalid query data'}

    ignoreDirection = not directed_search

    if force_neighbourhood:
        # force a neighbourhood search
        search_type = "neighbourhood"
    else:
        # let the search type be determined by the query
        search_type = None

    subgraph = utils.extract_query(pss._graph, query_nodes, ignoreDirection=ignoreDirection, search_type=search_type)
    return utils.graph2json(pss._n, pss._e, subgraph, query_nodes=query_nodes)


@bp.route('/expand', methods=['GET', 'POST'])
def expand():
    try:
        data = request.get_json(force=False)
        query_nodes = set(data.get('nodes'))
    except Exception as e:
        return {'error': 'Invalid query data'}

    # potential edges are on the second level and may link to the existing graph
    subgraph, potentialEdges = utils.expand_nodes(pss._graph, list(query_nodes))

    # write potential edges in JSON
    elist = [utils.edge_data(fr, to, attrs) for fr, to, attrs in potentialEdges]

    json_data = utils.graph2json(pss._n, pss._e, subgraph)
    json_data['network']['potential_edges'] = elist
    return json_data

@bp.route('/')
@cross_origin()
def main():
    logged_in = '_user_id' in session

    # Forward the browser's own session cookie on this server-to-server call
    # so skm-web can authenticate the request the normal way (current_user),
    # instead of relaying a self-reported user id via a custom header.
    headers = {'Cookie': request.headers.get('Cookie', '')}

    # refresh pss
    pss.load(headers=headers)

    return render_template('index.html', logged_in=logged_in, backup=pss.backup, pss_url=PSS_URL)

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    # web analytics: the Umami instance of skm.nib.si (no tag without a website id)
    app.config['UMAMI_SCRIPT_URL'] = os.environ.get('UMAMI_SCRIPT_URL', 'https://skm.nib.si/analytics/script.js')
    app.config['UMAMI_WEBSITE_ID'] = os.environ.get('UMAMI_WEBSITE_ID', '')
    CORS(app)

    rport = 6379
    rs = redis.Redis(host='redis', port=rport, password=os.environ.get('REDIS_PASSWORD') or None)
    try:
        rs.ping()
        print("Redis is running!")
    except redis.exceptions.ConnectionError:
        print(f'Warning: Redis is not running on port {rport}. Not using this setting.')
    else:
        app.config.from_mapping(
            # Flask Session settings
            SESSION_TYPE = 'redis',
            SESSION_REDIS = rs,
        )
        sess.init_app(app)
    app.register_blueprint(bp)
    return app

app = create_app()
