import json as _json
import networkx as nx
from networkx.readwrite.json_graph import node_link
import sys


def human(graph):
    for pkg in graph:
        node = graph.node[pkg]

        print(node['label'])

        for _, req, edge in graph.out_edges([pkg], data=True):
            req_node = graph.node[req]

            print('  depends on %s (%s is installed)' % (
                req + ' ' + edge['label'], req_node['version']))


_dot_colors = {
    'error_not_precise': '#bb0000',
    'error_indirect': '#bb6600',
    'error_cycle': '#bb0066',
}


def dot(graph):
    # Copy so we can add display information
    graph = nx.DiGraph(graph)

    for source, dest, data in graph.edges_iter(data=True):
        for key in data:
            if key in _dot_colors:
                data['color'] = _dot_colors[key]
                break

        if data['is_pin']:
            data['style'] = 'dashed'

    for package in graph.node:
        data = graph.node[package]
        if 'latest' in data:
            data['color'] = '#0000bb'

    dot = nx.to_pydot(graph)
    dot.set_rankdir('LR')
    print(dot.to_string())


def graphml(graph):
    # GraphML doesn't know how to serialize lists, so we
    # convert them to strings.
    copy = nx.DiGraph(graph)
    for source, dest, data in copy.edges_iter(data=True):
        data['specs'] = str(data['specs'])
    for line in nx.generate_graphml(copy):
        print(line)


def json(graph):
    rep = node_link.node_link_data(graph)
    _json.dump(rep, sys.stdout, indent=2)
