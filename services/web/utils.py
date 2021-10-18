import csv
import subprocess
import itertools
import json
import re
from html.entities import name2codepoint as n2cp

import networkx as nx
# from fuzzywuzzy import fuzz, process

RE_HTML_ENTITY = re.compile(r'&(#?)([xX]?)(\w{1,8});', re.UNICODE)


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



def extract_subgraph(g, nodes, k=2, ignoreDirection=False):
    nodes = [node for node in nodes if node in g.nodes]

    if ignoreDirection:
        g = nx.Graph(g.copy())
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


def extract_shortest_paths(g, query_nodes, ignoreDirection=True):
    if ignoreDirection:
        searchable_g = nx.Graph(g)
    else:
        searchable_g = g

    # print('--->', query_nodes)
    if len(query_nodes) == 1:
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
        # this also cover the case with no paths at all
        paths_nodes = set(paths_nodes).union(query_nodes)

    return g.subgraph(paths_nodes).copy()


# def visualize_graphviz(g, path, output='pdf'):
#     dotfile = path + '.dot'
#     nx.drawing.nx_pydot.write_dot(g, dotfile)
#     subprocess.call(['dot', '-T{}'.format(output), dotfile, '-o', '{}.{}'.format(path, output)])  # , cwd=outdir)

def parseJSON(path):
    nodes = []
    edges = []
    with open(path) as fp:
        for line in fp:
            line = json.loads(line)
            if line['type'] == 'node':
                nodes.append(line)
            elif line['type'] == 'relationship':
                edges.append(line)
            else:
                raise ValueError('Unknown line')
            # print(line)

    g = nx.DiGraph()
    for node in nodes:
        # g.add_node(node['id'], name=node['properties']['name'], labels=node['labels'])
        node['properties']['name'] = decode_htmlentities(node['properties']['name'])
        node['properties']['description'] = decode_htmlentities(node['properties'].get('description', ''))
        node['properties']['additional_information'] = decode_htmlentities(node['properties'].get('additional_information', ''))
        g.add_node(node['id'], labels=node['labels'], **node['properties'])
    for edge in edges:
        # if edge['start']['id'] not in g.nodes:
        #     print('UNKNOWN START NODE: ', edge['start']['id'])
        # if edge['end']['id'] not in g.nodes:
        #     print('UNKNOWN END NODE: ', edge['end']['id'])
        props = edge['properties'] if 'properties' in edge else {}
        g.add_edge(edge['start']['id'], edge['end']['id'], label=edge['label'], **props)

    return nodes, edges, g


def graph2json(nodelist, edgelist, g):
    groups = set()
    for node in nodelist:
        groups.add(node['labels'][0])
    groups_json = {}
    for elt in groups:
        if elt == 'Complex':
            groups_json[elt] = {'shape': 'box',
                                'color': {'background': 'AliceBlue'}}
        elif elt == 'Family':
            groups_json[elt] = {'shape': 'box',
                                'color': {'background': 'Cornsilk'}}
        elif elt == 'Foreign':
            groups_json[elt] = {'shape': 'box',
                                'color': {'background': 'Gainsboro'}}
        elif elt == 'FunctionalCluster':
            groups_json[elt] = {'shape': 'box',
                                'color': {'background': 'Gainsboro'}}
        elif elt == 'Metabolite':
            groups_json[elt] = {'shape': 'box',
                                'color': {'background': 'LavenderBlush'}}
        elif elt == 'Process':
            groups_json[elt] = {'shape': 'box',
                                'color': {'background': 'PapayaWhip'}}
        elif elt == 'Reaction':
            groups_json[elt] = {'shape': 'box',
                                'color': {'background': 'PaleGoldenRod'}}
        else:
            groups_json[elt] = {'shape': 'box',
                                'color': {'background': 'White'}}

    nlist = []
    for nodeid, attrs in g.nodes(data=True):
        label = attrs['name']
        label_parts = [x for x in re.split('(\[.+\])', label) if x.strip()]
        if len(label_parts) == 1:
            label = label_parts[0]
        elif len(label_parts) == 2:
            # label = '<b>{}</b>\n{}'.format(label_parts[0], label_parts[1].replace(',', ', '))
            label = label_parts[0]
        else:
            print('Warning: strangely formatted label: ', label)
        nlist.append({'id': nodeid,
                      'label': label,
                      'group': attrs['labels'][0],
                      'description': attrs.get('description', ''),
                      'synonyms': ', '.join(attrs.get('synonyms', [])),
                      'additional_information': attrs.get('additional_information', '')
                      })
                      # title is displayed on hover in vis.js
                      # 'title': 'Name: {}\nSource: {}\nLink: {}'.format(node, 'NIB', 'http://mylink.com')})
    elist = []
    for fr, to, attrs in g.edges(data=True):
        elist.append({'from': fr,
                      'to': to,
                      'label': attrs['label'].replace('_', ' ')}) #,
                      # 'type': g.edges[edge]['type']})
    return {'network': {'nodes': nlist, 'edges': elist}, 'groups': groups_json}


def get_autocomplete_node_data(g):
    data = []
    for nodeid, attrs in g.nodes(data=True):
        elt = {'id': nodeid}
        for atr in ['name', 'synonyms', 'description', 'additional_information']:
            elt[atr] = attrs.get(atr, '')
        elt['synonyms'] = ', '.join(elt['synonyms'])
        data.append(elt)
    return {'node_data': data}


if __name__ == '__main__':
    ns, es, g = parseJSON('data/PSS-latest.json')
    j = graph2json(ns, es, g)
    nd = get_autocomplete_node_data(g)
