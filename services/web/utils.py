# import csv
# import subprocess
import itertools
import json
import re
from html.entities import name2codepoint as n2cp

import networkx as nx
# from fuzzywuzzy import fuzz, process

import requests

RE_HTML_ENTITY = re.compile(r'&(#?)([xX]?)(\w{1,8});', re.UNICODE)

SPECIES = [
    "ath",
    "osa",
    "stu",
    "sly",
    "nta",
    "ptr",
    "vvi",
    'mdo',
    'pdul',
    'parm',
    'pavi',
    'pcer',
    'ppe',
    'psib',
    'pcox',
]


EDGE_STYLE = {
    'ACTIVATES':  {
        'color': {'color': "#008040", 'hover': '#008040', 'highlight':'#008040'},
        'arrows': {'to': {'enabled': True, 'type': 'circle'}},
    },
    'INHIBITS': {
        'color': {'color': "#cd0000", 'hover': '#cd0000', 'highlight':'#cd0000'},
        'arrows': {'to': {'enabled': True, 'type': 'bar'}}
    },
    'SUBSTRATE': {
        'color': {'color': "#5d5d5d", 'hover': '#5d5d5d', 'highlight':'#5d5d5d'},
        'arrows': {'to': {'enabled': True, 'type': 'arrow'}}
    },
    'TRANSLOCATE_FROM': {
        'color': {'color': "#5d5d5d", 'hover': '#5d5d5d', 'highlight':'#5d5d5d'},
        'arrows': {'to': {'enabled': True, 'type': 'arrow'}}
    },
    'PRODUCT': {
        'color': {'color': "#5d5d5d", 'hover': '#5d5d5d', 'highlight':'#5d5d5d'},
        'arrows': {'to': {'enabled': True, 'type': 'arrow'}}
    },
    'TRANSLOCATE_TO': {
        'color': {'color': "#5d5d5d", 'hover': '#5d5d5d', 'highlight':'#5d5d5d'},
        'arrows': {'to': {'enabled': True, 'type': 'arrow'}}
    },
    'default': {
        'color': {'color': "#000000", 'hover': '#000000', 'highlight':'#000000'},
        'arrows': {'to': {'enabled': True, 'type': 'arrow'}}
    },
}

NODE_STYLE = {
    'Complex': {
        'shape': 'box',
        'color': {'background': '#9cd6e4', 'border': '#40b0cb'}
    },
    # plant genes -- shades of green,
    'PlantCoding': {
        'shape': 'circle',
        'color': {'background': '#66CDAA', 'border': '#48c39a'}
    },
    'PlantNonCoding': {
        'shape': 'box',
        'color': {'background': '#98FB98', 'border': '#057c05'}
    },
    'PlantAbstract': {
        'shape': 'box',
        'color': {'background': '#3cb371', 'border': '#2d8755'}
    },
    # bad guys -- shades of brown/orange,
    'ForeignCoding': {
        'shape': 'box',
        'color': {'background': '#f4a460', 'border': '#ef7a17'}
    },
    'ForeignNonCoding': {
        'shape': 'box',
        'color': {'background': '#f5deb3', 'border': '#e3a228'}
    },
    'ForeignAbstract': {
        'shape': 'box',
        'color': {'background': '#bc8f8f', 'border': '#a66a6a'}
    },
    'ForeignEntity': {
        'shape': 'box',
        'color': {'background': '#cd853f', 'border': '#965e27'}
    },
    'ForeignAbiotic': {
        'shape': 'box',
        'color': {'background': '#cd3f40', 'border': '#a62b2c'}
    },
    'Metabolite': {
        'shape': 'box',
        'color': {'background': '#fff0f5', 'border': '#ff6799'}
    },
    'Process': {
        'shape': 'box',
        'color': {'background': '#c4bcff', 'border': '#6e5aff'}
    },
    # "other" type of node,
    'Reaction': {
        'shape': 'box',
        'margin':5,
        'color': {'background': '#4169e1', 'border': '#122a73'},
        'font':  {'color': "White",
                  'multi': 'html'},
        'widthConstraint': 85
    },
    # every one else,
    'default': {
        'shape': 'box',
        'color': {'background': 'White', 'border': '#6c7881'}
    }
}


def edge_style(edge):

    edge_type = edge['label']

    if edge_type in EDGE_STYLE:
        return {
            'label': edge_type.replace('_', ' '),
            'color': EDGE_STYLE[edge_type]['color'],
            'arrows': EDGE_STYLE[edge_type]['arrows']
        }
    else:
        return {
            'label': edge_type.replace('_', ' '),
            'color': EDGE_STYLE["default"]['color'],
            'arrows': EDGE_STYLE["default"]['arrows']
        }

# taken from gensim.utils
def decode_htmlentities(text):
    def safe_unichr(intval):
        try:
            return chr(intval)
        except ValueError:
            # ValueError: chr() arg not in range(0x10000) (narrow Python build)
            s = "\\U%08x" % intval
            # return UTF16 surrogate pair
            return s.decode('unicode-escape')

    def substitute_entity(match):
        try:
            ent = match.group(3)
            if match.group(1) == "#":
                # decoding by number
                if match.group(2) == '':
                    # number is in decimal
                    return safe_unichr(int(ent))
                elif match.group(2) in ['x', 'X']:
                    # number is in hex
                    return safe_unichr(int(ent, 16))
            else:
                # they were using a name
                cp = n2cp.get(ent)
                if cp:
                    return safe_unichr(cp)
                else:
                    return match.group()
        except Exception:
            # in case of errors, return original input
            return match.group()
    return RE_HTML_ENTITY.sub(substitute_entity, text)


def create_undirected_graph(g):

    g = nx.Graph(g)

    return g

def create_directed_graph(g):

    g = nx.DiGraph(g) # copy

    # remove all "SUBSTRATE" and "TRANSLOCATE_FROM" edges when
    # form is not metabolite?

    edges_to_remove = [(u, v) for u, v, d in g.edges(data=True) if \
        (d['label'] in ("SUBSTRATE", "TRANSLOCATE_FROM")) and d["form"] != "metabolite"
        ]

    g.remove_edges_from(edges_to_remove)

    return g



def expand_nodes(g, nodes):
    if len(nodes) > 1:
        print('Error : expand not implemented for more than one node')
    node = nodes[0]
    ug = nx.Graph(g)

    # only double expand not Reactions
    if is_reaction(g.nodes[node]):
        k = 1
    else:
        k = 2

    # find also neighbours on the second level to connect to the rest of the graph (if possible)
    all_neighbours = set(nodes)
    fromnodes = nodes
    for i in range(k):
        neighbours = set(itertools.chain.from_iterable([ug.neighbors(node) for node in fromnodes]))  # - set(fromnodes)
        if not neighbours:
            break
        all_neighbours.update(neighbours)
        fromnodes = neighbours

    reaction_expanded_nodes = reaction_expansion(ug, all_neighbours)

    all_neighbours.update(reaction_expanded_nodes)

    potentialEdges = g.subgraph(all_neighbours).edges(data=True)
    # return g.subgraph([node] + list(ug.neighbors(node))), potentialEdges
    return g.subgraph(all_neighbours), potentialEdges

def reaction_expansion(g, nodes, ignoreDirection=True):
    reactions_to_expand_on = []
    for n in nodes:
        if is_reaction(g.nodes[n]):
            reactions_to_expand_on.append(n)

    print("reaction to expand", len(reactions_to_expand_on))

    expanded_nodes = extract_neighbourhood(g, reactions_to_expand_on, k=1, ignoreDirection=ignoreDirection)
    print("reactions expanded", len(expanded_nodes))

    return expanded_nodes

def extract_query(g, query_nodes, ignoreDirection=True, search_type=None, k=1):
    '''
    k --> neighbourhood distance (number steps)
    '''
    # print('--->', query_nodes)


    if search_type is None:
        if len(query_nodes) == 1:
            search_type = "neighbourhood"
        else:
            search_type = "paths"

    if search_type == "neighbourhood":
        nodes = extract_neighbourhood(g, query_nodes, k=k, ignoreDirection=ignoreDirection)
    else:
        nodes = extract_shortest_paths(g, query_nodes, ignoreDirection=ignoreDirection)

    reaction_expanded_nodes = reaction_expansion(g, nodes)

    # print("before", len(paths_nodes))
    nodes.update(reaction_expanded_nodes)
    # print("after", len(paths_nodes))

    return g.subgraph(nodes).copy()

def extract_neighbourhood(g, nodes, k=2, ignoreDirection=True):
    nodes = [node for node in nodes if node in g.nodes]

    if ignoreDirection:
        searchable_g = create_undirected_graph(g)
    else:
        searchable_g = create_directed_graph(g)

    all_neighbours = set(nodes)
    fromnodes = nodes
    for _ in range(k):
        neighbours = set(itertools.chain.from_iterable([searchable_g.neighbors(node) for node in fromnodes]))  # - set(fromnodes)
        if not neighbours:
            break
        all_neighbours.update(neighbours)
        fromnodes = neighbours

    print(all_neighbours)

    return all_neighbours

def extract_shortest_paths(g, query_nodes, ignoreDirection=True):
    if ignoreDirection:
        searchable_g = create_undirected_graph(g)
    else:
        searchable_g = create_directed_graph(g)

    paths_nodes = []
    if ignoreDirection:
        # use combinations for undirected graph (order does not matter)
        iterator = itertools.combinations(query_nodes, 2)
    else:
        # use permutations for directed graph (order matters, use both A --> B and B --> A)
        iterator = itertools.permutations(query_nodes, 2)
    for fr, to in iterator:
        try:
            paths = [p for p in nx.all_shortest_paths(searchable_g, source=fr, target=to)]
            # print(paths)
            paths_nodes.extend([item for path in paths for item in path])
        except nx.NetworkXNoPath:
            print('No paths:', g.nodes()[fr]["name"], g.nodes()[to]["name"])
            pass
    # add back also nodes with no paths
    # this also covers the case with no paths at all
    nodes = set(paths_nodes).union(query_nodes)

    return nodes


# def visualize_graphviz(g, path, output='pdf'):
#     dotfile = path + '.dot'
#     nx.drawing.nx_pydot.write_dot(g, dotfile)
#     subprocess.call(['dot', '-T{}'.format(output), dotfile, '-o', '{}.{}'.format(path, output)])  # , cwd=outdir)

# the fields of an edge sent to the browser (the reaction graph's edge fields)
EDGE_ATTRIBUTES = ['role', 'location', 'location_putative', 'organ', 'organ_putative', 'form', 'identifiers']

# style groups of the node types that have none of their own
GROUP = {'reaction': 'Reaction', 'MetaboliteFamily': 'Metabolite'}


def node_group(node_type):
    return GROUP.get(node_type, node_type)


def is_reaction(attrs):
    return attrs.get('node_type') == 'reaction'


def parseJSON(url=None, path=None, headers={}):
    '''The PSS reaction graph (pss-export's reaction-graph-json: {"nodes": [...], "edges": [...]}), from
    url, or if that fails, from path. Nodes are keyed by their id (entity name or reaction id). Returns
    nodes, edges, the graph, and whether it is the local backup (path).

    Graph is directed (for orientation of edges in viz), but needs to be
    undirected in any queries.
    '''

    if not (path or url):
        raise Exception("ERROR: at least path or url")

    data = None
    if url:
        try:
            response = requests.get(url, headers=headers)
            if response.ok:
                data = response.json()
        except (requests.exceptions.ConnectionError, ValueError) as e:
            print(f"Could not fetch the reaction graph from {url} ({e}). Using a local copy.")

    backup = data is None
    if backup:
        with open(path) as fp:
            data = json.load(fp)

    g = nx.DiGraph()
    for node in data['nodes']:
        attrs = {k: v for k, v in node.items() if v not in (None, [])}
        attrs['name'] = node['id']
        attrs['label'] = node['display_label'] or node['id']
        if node['node_type'] == 'reaction':
            attrs['reaction_id'] = node['id']
        attrs['description'] = decode_htmlentities(node.get('description') or '')
        attrs['evidence_sentence'] = decode_htmlentities(node.get('evidence_sentence') or '')
        g.add_node(node['id'], **attrs)

    for edge in data['edges']:
        g.add_edge(edge['source'], edge['target'], label=edge['edge_type'],
                   **{k: edge.get(k) for k in EDGE_ATTRIBUTES})

    return data['nodes'], data['edges'], g, backup


def edge_data(fr, to, attrs):
    ''' An edge for the browser '''
    return {**{k: attrs.get(k) for k in EDGE_ATTRIBUTES}, **edge_style(attrs), 'from': fr, 'to': to}


def graph2json(nodelist, edgelist, g, query_nodes=None):
    if query_nodes is None:
        query_nodes = []

    groups = set()
    for node in nodelist:
        groups.add(node_group(node['node_type']))
    groups_json = {}
    for elt in groups:
        if elt in NODE_STYLE:
            groups_json[elt] = NODE_STYLE[elt]
        else:
            groups_json[elt] = NODE_STYLE['default']

    nlist = []
    for nodeid, attrs in g.nodes(data=True):
        group = node_group(attrs['node_type'])

        nodeData = {
            'id': nodeid,
            'name': attrs['name'],
            'type': group
        }

        for atr in [
            'label',
            'short_name',
            'description',
            'evidence_sentence',
            'reaction_type',
            'functional_cluster_id',
            'reaction_id',
            'pathway',
            'reaction_mechanism',
            'reaction_effect'
            ]:
            nodeData[atr] = attrs.get(atr, '')

        for atr in [
            'synonyms',
            'external_links',
            'mapman'
            ]:
            nodeData[atr] = attrs.get(atr, [])

        if group == "Reaction":
            nodeData['label'] = f"<b>{nodeData['label']}</b>\n{attrs.get('reaction_type', '')}"

        nodeData['_homologues'] = {}
        has_group = True # style group
        for sp in SPECIES:
            key = f'{sp}_homologues'
            if key in attrs:
                has_group = False

                nodeData['color'] = {'background': groups_json[group]['color']['background'],
                                     'border': groups_json[group]['color']['border']}

                nodeData['_homologues'][sp] = ', '.join(attrs[key])

        if nodeid in query_nodes:
            nodeData['color'] = {'background': groups_json[group]['color']['background'],
                                 'border': 'red',
                                 'highlight': {'border': 'red'},  # this does not work, bug in vis.js
                                 'hover': {'border': 'red'}}  # this does not work, bug in vis.js
            nodeData['borderWidth'] = 2
            nodeData['query_node'] = True
        else:
            nodeData['query_node'] = False

        if has_group:
            nodeData['group'] = group

        nlist.append(nodeData)

    elist = [edge_data(fr, to, attrs) for fr, to, attrs in g.edges(data=True)]

    return {'network': {'nodes': nlist, 'edges': elist}, 'groups': groups_json}

def get_autocomplete_node_data(g):
    data = []
    for nodeid, attrs in g.nodes(data=True):
        elt = {'id': nodeid}
        for atr in ['name', 'reaction_id', 'label', 'synonyms', 'description', 'evidence_sentence', 'functional_cluster_id', 'external_links'] + [f'{sp}_homologues' for sp in SPECIES]:
            elt[atr] = attrs.get(atr, '')
        elt['synonyms'] = ', '.join(elt['synonyms'])
        elt['external_links'] = ', '.join(elt['external_links'])
        # all its gene ids, to search by gene id
        elt['genes'] = ' '.join(g for sp in SPECIES for g in (attrs.get(f'{sp}_homologues') or []))

        data.append(elt)
    return {'node_data': data}

if __name__ == '__main__':
    ns, es, g, _ = parseJSON(path='data/PSS-reactions.json')
    j = graph2json(ns, es, g)
    nd = get_autocomplete_node_data(g)
