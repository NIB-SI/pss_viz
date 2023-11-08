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
]


EDGE_STYLE = {
    'ACTIVATES':  {
        'color': {'color': "#008040", 'hover': '#008040'},
        'arrows': {'to': {'enabled': True, 'type': 'circle'}},
    },
    'INHIBITS': {
        'color': {'color': "#cd0000", 'hover': '#cd0000'},
        'arrows': {'to': {'enabled': True, 'type': 'bar'}}
    },
    'SUBSTRATE': {
        'color': {'color': "#485056", 'hover': '#485056'},
        'arrows': {'to': {'enabled': True, 'type': 'arrow'}}
    },
    'TRANSLOCATE_FROM': {
        'color': {'color': "#5d5d5d", 'hover': '#49606d'},
        'arrows': {'to': {'enabled': True, 'type': 'arrow'}}
    },
    'PRODUCT': {
        'color': {'color': "#485056", 'hover': '#485056'},
        'arrows': {'to': {'enabled': True, 'type': 'arrow'}}
    },
    'TRANSLOCATE_TO': {
        'color': {'color': "#5d5d5d", 'hover': '#49606d'},
        'arrows': {'to': {'enabled': True, 'type': 'arrow'}}
    },
    'default': {
        'color': {'color': "#000000", 'hover': '#000000'},
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
    # every one else,
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
    'default': {
        'shape': 'box',
        'color': {'background': 'White', 'border': '#6c7881'}
    }
}


def edge_style(edge_type):

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


def expand_nodes(g, nodes):
    if len(nodes) > 1:
        print('Error : expand not implemented for more than one node')
    node = nodes[0]
    ug = nx.Graph(g)

    # only double expand not Reactions
    if 'Reaction' in g.nodes[node]['labels']:
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


def extract_subgraph(g, nodes, k=2, ignoreDirection=True):
    nodes = [node for node in nodes if node in g.nodes]

    if ignoreDirection:
        g = nx.Graph(g)
    all_neighbours = set(nodes)
    fromnodes = nodes
    for i in range(k):
        neighbours = set(itertools.chain.from_iterable([g.neighbors(node) for node in fromnodes]))  # - set(fromnodes)
        if not neighbours:
            break
        all_neighbours.update(neighbours)
        fromnodes = neighbours
    result = g.subgraph(all_neighbours).copy()
    return result

def reaction_expansion(g, nodes, ignoreDirection=True):
    reactions_to_expand_on = []
    for n in nodes:
        if 'Reaction' in g.nodes[n]['labels']:
            reactions_to_expand_on.append(n)

    print("reaction to expand", len(reactions_to_expand_on))

    expanded_nodes = extract_subgraph(g, reactions_to_expand_on, k=1, ignoreDirection=ignoreDirection).nodes()
    print("reactions expanded", len(expanded_nodes))

    return expanded_nodes


def extract_shortest_paths(g, query_nodes, ignoreDirection=True):
    if ignoreDirection:
        searchable_g = nx.Graph(g)
    else:
        searchable_g = g

    # print('--->', query_nodes)
    if len(query_nodes) == 1:
        if 'Reaction' in g.nodes[list(query_nodes)[0]]['labels']:
            subgraph = extract_subgraph(g, query_nodes, k=1, ignoreDirection=ignoreDirection)
        else:
            subgraph = extract_subgraph(g, query_nodes, k=2, ignoreDirection=ignoreDirection)
        paths_nodes = subgraph.nodes()
    else:
        paths_nodes = []
        for fr, to in itertools.combinations(query_nodes, 2):
            try:
                paths = [p for p in nx.all_shortest_paths(searchable_g, source=fr, target=to)]
                # print(paths)
                paths_nodes.extend([item for path in paths for item in path])
            except nx.NetworkXNoPath:
                print('No paths:', fr, to)
                pass
        # add back also nodes with no paths
        # this also covers the case with no paths at all
        paths_nodes = set(paths_nodes).union(query_nodes)
        reaction_expanded_nodes = reaction_expansion(g, paths_nodes)

        # print("before", len(paths_nodes))
        paths_nodes.update(reaction_expanded_nodes)
        # print("after", len(paths_nodes))

    return g.subgraph(paths_nodes).copy()


# def visualize_graphviz(g, path, output='pdf'):
#     dotfile = path + '.dot'
#     nx.drawing.nx_pydot.write_dot(g, dotfile)
#     subprocess.call(['dot', '-T{}'.format(output), dotfile, '-o', '{}.{}'.format(path, output)])  # , cwd=outdir)

def parseJSON(url=None, path=None, headers={}):
    '''Try url first, if failed, fall back to path

    Graph is directed (for orientation of edges in viz), but needs to be
    undirected in any queries.
    '''

    nodes = []
    edges = []
    g = nx.DiGraph()

    if not (path or url):
        raise Exception("ERROR: at least path or url")

    success = False
    if url:
        try:
            response = requests.get(url, headers=headers)
            if response.ok:
                success = True
                for line in response.text.split("\n"):
                    line = json.loads(line)
                    if line['type'] == 'node':
                        nodes.append(line)
                    elif line['type'] == 'relationship':
                        edges.append(line)
                    else:
                        raise ValueError('Unknown line')
                    # print(line)
        except requests.exceptions.ConnectionError as e:
            print(f"Could not fetch file from {url}. Using a local copy.")
            # raise e

    if not success:
        with open(path) as fp:
            for line in fp:
                # current_app.logger.info(line)
                line = json.loads(line)
                if line['type'] == 'node':
                    nodes.append(line)
                elif line['type'] == 'relationship':
                    edges.append(line)
                else:
                    raise ValueError('Unknown line')
                # print(line)

    for node in nodes:
        # g.add_node(node['id'], name=node['properties']['name'], labels=node['labels'])
        node['properties']['name'] = decode_htmlentities(node['properties']['name'])
        node['properties']['functional_cluster_id'] = node['properties'].get('functional_cluster_id', '')
        node['properties']['description'] = decode_htmlentities(node['properties'].get('description', ''))
        node['properties']['evidence_sentence'] = decode_htmlentities(node['properties'].get('evidence_sentence', ''))
        g.add_node(node['id'], labels=node['labels'], **node['properties'])

    for edge in edges:
        # if edge['start']['id'] not in g.nodes:
        #     print('UNKNOWN START NODE: ', edge['start']['id'])
        # if edge['end']['id'] not in g.nodes:
        #     print('UNKNOWN END NODE: ', edge['end']['id'])
        props = edge['properties'] if 'properties' in edge else {}
        g.add_edge(edge['start']['id'], edge['end']['id'], label=edge['label'], **props)

    return nodes, edges, g


def graph2json(nodelist, edgelist, g, query_nodes=[]):
    groups = set()
    for node in nodelist:
        groups.add(fetch_group(node['labels']))
    groups_json = {}
    for elt in groups:
        if elt in NODE_STYLE:
            groups_json[elt] = NODE_STYLE[elt]
        else:
            groups_json[elt] = NODE_STYLE['default']

    nlist = []
    for nodeid, attrs in g.nodes(data=True):
        group = fetch_group(attrs['labels'])

        nodeData = {'id': nodeid, 'name': attrs['name'], 'group': group,}

        for atr in ['name', 'short_name', 'description', 'evidence_sentence', 'reaction_type', 'functional_cluster_id', 'reaction_id']:
            nodeData[atr] = attrs.get(atr, '')

        for atr in ['synonyms', 'external_links']:
            nodeData[atr] = attrs.get(atr, [])

        label = attrs['name']
        label_parts = [x for x in re.split(r'(\[.+\])', label) if x.strip()]
        if len(label_parts) == 1:
            label = label_parts[0]
        elif len(label_parts) == 2:
            # label = '<b>{}</b>\n{}'.format(label_parts[0], label_parts[1].replace(',', ', '))
            label = label_parts[0]
        else:
            print('Warning: strangely formatted label: ', label)

        if group == "Reaction":
            nodeData['label'] = f"<b>{label}</b>\n{attrs.get('reaction_type', '')}"

        else:
            nodeData['label'] = label

        nodeData['_homologues'] = {}
        for sp in SPECIES:
            key = f'{sp}_homologues'
            if key in attrs:
                nodeData['_homologues'][sp] = ', '.join(attrs[key])

        if nodeid in query_nodes:
            nodeData['color'] = {'background': groups_json[group]['color']['background'],
                                 'border': 'red',
                                 'highlight': {'border': 'red'},  # this does not work, bug in vis.js
                                 'hover': {'border': 'red'}}  # this does not work, bug in vis.js
            nodeData['borderWidth'] = 2

        nlist.append(nodeData)

    elist = []
    for fr, to, attrs in g.edges(data=True):
        edge_type = attrs['label']
        d = edge_style(edge_type)
        d['from'] = fr
        d['to'] = to
        elist.append(d)

    return {'network': {'nodes': nlist, 'edges': elist}, 'groups': groups_json}

def fetch_group(labels):
    index_labels = ['Family', 'Plant', 'Foreign', 'Node', 'FunctionalCluster']
    for x in labels:
        if not (x in index_labels):
            return x

    # just in case
    return labels[0]

def get_autocomplete_node_data(g):
    data = []
    for nodeid, attrs in g.nodes(data=True):
        elt = {'id': nodeid}
        for atr in ['name', 'synonyms', 'description', 'evidence_sentence', 'functional_cluster_id'] + [f'{sp}_homologues' for sp in SPECIES]:
            elt[atr] = attrs.get(atr, '')
        elt['synonyms'] = ', '.join(elt['synonyms'])
        data.append(elt)
    return {'node_data': data}

if __name__ == '__main__':
    ns, es, g = parseJSON('data/PSS-reactions.json')
    j = graph2json(ns, es, g)
    nd = get_autocomplete_node_data(g)
