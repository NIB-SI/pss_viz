import csv
import subprocess
import networkx as nx
import itertools

from fuzzywuzzy import fuzz, process


def parse_ckn_csv(fname):
    g = nx.DiGraph()
    fields = ['from', 'to', 'type']
    with open(fname, newline='') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(2048))
        csvfile.seek(0)
        reader = csv.DictReader(csvfile, fieldnames=fields, dialect=dialect, restkey='rest', )
        for row in reader:
            g.add_edge(row['from'], row['to'], type=row['type'])
            if row['type'] == 'binding':
                g.add_edge(row['to'], row['from'], type=row['type'])
    return g


def best_matching_nodes(g, node, k=5):
    return [n for n, s in process.extract(node, list(g.nodes), limit=k, scorer=fuzz.QRatio)]


def extract_subgraph(g, nodes, k=2, ignoreDirection=False, fuzzySearch=True):
    if fuzzySearch:
        matched_nodes = [node for node in nodes if node in g.nodes]
        unmatched_nodes = [node for node in nodes if node not in g.nodes]
        all_nodes = list(g.nodes)
        for node in unmatched_nodes:
            best_match, score = process.extract(node, all_nodes, limit=1, scorer=fuzz.QRatio)[0]
            matched_nodes.append(best_match)
        nodes = matched_nodes
    else:
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
    for i, node in enumerate(result.nodes):
        result.nodes[node]['id'] = i+1
    return result


def graph2json(g):
    nlist = []
    for node in g.nodes:
        nlist.append({'id': g.nodes[node]['id'],
                      'label': node})
                      # title is displayed on hover in vis.js
                      # 'title': 'Name: {}\nSource: {}\nLink: {}'.format(node, 'NIB', 'http://mylink.com')})
    elist = []
    for edge in g.edges:
        fr = edge[0]
        to = edge[1]
        elist.append({'from': g.nodes[fr]['id'],
                      'to': g.nodes[to]['id'],
                      # 'label': g.edges[edge]['type'],
                      'type': g.edges[edge]['type']})
    return {'nodes': nlist, 'edges': elist}


def visualize_graphviz(g, path, output='pdf'):
    dotfile = path + '.dot'
    nx.drawing.nx_pydot.write_dot(g, dotfile)
    subprocess.call(['dot', '-T{}'.format(output), dotfile, '-o', '{}.{}'.format(path, output)])  # , cwd=outdir)
