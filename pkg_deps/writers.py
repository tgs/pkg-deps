import json as _json
import networkx as nx
from networkx.readwrite.json_graph import node_link
import sys


def human(graph):
    for pkg in graph:
        node = graph.node[pkg]

        if 'latest' in node:
            latest = '(Latest: {latest})'.format(**node)
        else:
            latest = ''

        print(node['label'], latest)

        for _, req, edge in graph.out_edges([pkg], data=True):
            req_node = graph.node[req]

            print('  depends on %s (%s is installed)' % (
                req + ' ' + edge['label'], req_node['version']))


def dot(graph):
    dot = nx.to_pydot(graph)
    print(dot.to_string())


def graphml(graph):
    # GraphML doesn't know how to serialize lists, so we
    # convert them to strings.
    copy = nx.DiGraph(graph)
    for source, dest, data in copy.edges_iter(data=True):
        print(repr(data))
        data['specs'] = str(data['specs'])
    for line in nx.generate_graphml(copy):
        print(line)


def json(graph):
    rep = node_link.node_link_data(graph)
    _json.dump(rep, sys.stdout, indent=2)
