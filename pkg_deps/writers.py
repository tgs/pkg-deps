from __future__ import print_function
import json as _json
import click
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

    packages = sorted(graph)
    try:
        packages = nx.topological_sort(graph, packages)
    except nx.exception.NetworkXUnfeasible:
        # Can happen if graph is cyclic; we've already warned by now.
        pass

    for pkg in packages:
        node_data = graph.node[pkg]

        problems = click.style(human_format_problems(node_data))
        if problems:
            problems = click.style(problems, bold=True)
        click.echo(" ".join([pkg, problems]))

        for src, dest, data in sorted(graph.out_edges([pkg], data=True)):
            problems = human_format_problems(data)
            if problems:
                problems = click.style(problems, bold=True)

            click.echo('  depends on %s (%s is installed) %s' % (
                data['requirement'], dest, problems))


_dot_colors = {
    'not precise': '#bb0000',
    'missing pin': '#bb6600',
    'cyclic dependency': '#bb0066',
    'outdated': '#0000bb',
    'unmet': '#6633bb',
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

    dot = nx.nx_pydot.to_pydot(graph)

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


def teamcity(graph):
    import teamcity.messages
    tc = teamcity.messages.TeamcityServiceMessages()

    print("Dependency tree starting with these packages:")
    print("   ".join(graph.graph['query packages']))
    print("Checked for:", ", ".join(ann.graph_checks(graph)))

    packages = sorted(graph)
    try:
        packages = nx.topological_sort(graph, packages)
    except nx.exception.NetworkXUnfeasible:
        # Can happen if graph is cyclic; we've already warned by now.
        pass

    for pkg in packages:
        node_data = graph.node[pkg]

        problems = human_format_problems(node_data)
        if problems:
            tc.buildProblem(
                "Package %s: %s" % (pkg, problems), 'pkg_deps.package_problem')

        for src, dest, data in sorted(graph.out_edges([pkg], data=True)):
            problems = human_format_problems(data)
            if problems:
                tc.buildProblem(
                    '%s depends on %s (%s is installed): %s' % (
                        pkg, data['requirement'], dest, problems),
                'pkg_deps.dependency_problem')
