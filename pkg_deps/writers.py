from __future__ import print_function
import json as _json
import networkx as nx
from networkx.readwrite.json_graph import node_link
import sys

from . import annotators as ann


def human_format_problems(obj, prefix_if_any='- '):
    problems = ann.failed_checks(obj)
    if not problems:
        return ''

    return prefix_if_any + '; '.join(
        (': '.join((check, message)) if message else check)
        for check, message in problems.items())


def human(graph):
    print("# Dependency tree starting with these packages:")
    print("# ", "   ".join(graph.graph['query packages']))
    print("# Checked for:", ", ".join(ann.graph_checks(graph)))

    for pkg in nx.topological_sort(graph, sorted(graph)):
        node_data = graph.node[pkg]

        print(pkg, human_format_problems(node_data))

        for src, dest, data in sorted(graph.out_edges([pkg], data=True)):
            problems = human_format_problems(data)

            print('  depends on %s (%s is installed) %s' % (
                data['requirement'], dest, problems))


_dot_colors = {
    'not precise': '#bb0000',
    'missing pin': '#bb6600',
    'cycle': '#bb0066',
    'outdated': '#0000bb',
}


def dot(graph):
    # Set colors and labels for edges
    for source, dest, data in graph.edges_iter(data=True):
        for check in ann.failed_checks(data):
            if check in _dot_colors:
                data['color'] = _dot_colors[check]
                break

        if '==' in data['requirement']:
            data['style'] = 'dashed'

        data['label'] = data['requirement']

        problems = ", ".join(ann.failed_checks(data).keys())
        if problems:
            data['label'] += ' (%s)' % problems

    # Set colors and labels for nodes
    for package in graph.node:
        data = graph.node[package]
        for check in ann.failed_checks(data):
            if check in _dot_colors:
                data['color'] = _dot_colors[check]

        data['label'] = data['as_requirement']

        problems = ", ".join(ann.failed_checks(data).keys())
        if problems:
            data['label'] += ' (%s)' % problems

        if package in graph.graph['query packages']:
            data['shape'] = 'box'

    dot = nx.to_pydot(graph)

    # Set graph title (only works after conversion)
    dot.set_label(" ".join((
        "Dependency tree rooted at square node(s)"
        "\nChecked for:",
        ', '.join(ann.graph_checks(graph)),
    )))
    dot.set_rankdir('LR')
    print(dot.to_string())


def json(graph):
    rep = node_link.node_link_data(graph)
    _json.dump(rep, sys.stdout, indent=2)
