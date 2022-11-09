import os
import json
import itertools
import networkx as nx

from flask import Flask, flash, g, redirect, render_template, request, session

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

    @app.route('/get_node_data', methods=['GET', 'POST'])
    def node_data():
        return pss.node_search_data

    @app.route('/get_network', methods=['GET', 'POST'])
    def draw_network():
        return pss.full_json

    @app.route('/search', methods=['GET', 'POST'])
    def search():
        try:
            data = request.get_json(force=False)
            query_nodes = set(data.get('nodes'))
        except Exception as e:
            return {'error': 'Invalid query data'}

        subgraph = utils.extract_shortest_paths(pss._graph, query_nodes, ignoreDirection=True)
        return utils.graph2json(pss._n, pss._e, subgraph, query_nodes=query_nodes)

    @app.route('/expand', methods=['GET', 'POST'])
    def expand():
        try:
            data = request.get_json(force=False)
            query_nodes = set(data.get('nodes'))
        except Exception as e:
            return {'error': 'Invalid query data'}

        # potential edges are on the second level and may link to the existing graph
        subgraph, potentialEdges = utils.expand_nodes(pss._graph, list(query_nodes))

        # write potential edges in JSON
        elist = []
        for fr, to, attrs in potentialEdges:
            edge_type = attrs['label']
            d = utils.edge_style(edge_type)
            d['from'] = fr
            d['to'] = to
            elist.append(d)

        json_data = utils.graph2json(pss._n, pss._e, subgraph)
        json_data['network']['potential_edges'] = elist
        return json_data

    @app.route('/')
    @cross_origin()
    def main():

        if '_user_id' in session:
            headers = {'Userid': session['_user_id']}
        else:
            headers = {}

        # refresh pss
        pss.load(headers=headers)

        return render_template('index.html')

    return app

app = create_app()
