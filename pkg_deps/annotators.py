import logging
from pkg_resources import Requirement
import re
import subprocess

import networkx as nx


logger = logging.getLogger(__name__)


str_types = (type(u''), type(b''))


def find_matching_node(graph, requirement):
    # Could certainly make this faster, but maybe that's not important?
    # First off, cache parsed versions of all the nodes in the graph...

    orig = requirement

    if type(requirement) in str_types:
        requirement = Requirement.parse(requirement)

    for n in graph:
        (name, ver) = n.split('==')
        if requirement.key == name.lower() and ver in requirement:
            return n

    raise ValueError("Couldn't find any packages matching %s" % orig)


def mark_check_failed(obj, check_name, message=''):
    fails = obj.setdefault('failed_checks', {})
    fails[check_name] = message


def failed_checks(obj):
    return obj.get('failed_checks', {})


def mark_graph_checked(graph, check_name):
    graph.graph.setdefault('checks', []).append(check_name)


def graph_checks(graph):
    return graph.graph.get('checks', [])


def dependencies_should_be_met(graph):
    bad = False

    for source, dest, data in graph.edges_iter(data=True):
        requirement = data['requirement']
        if type(requirement) in str_types:
            requirement = Requirement.parse(requirement)

        name, ver = dest.split('==')
        if ver not in requirement:
            mark_check_failed(data, 'unmet',
                              '%s is not installed' % data['requirement'])
            bad = True

    mark_graph_checked(graph, 'unmet')
    return bad


def add_available_updates(graph):
    """
    Add outdated package info to a dependency graph.

    Parameters:
        graph - a networkx.DiGraph to which info is added.

    This function runs and parses ``pip list --outdated``.  For
    each package that pip thinks is outdated, a 'latest' attribute
    is added to its node in the graph, with the latest available
    version as the value.
    """
    # It might be possible to do this with
    # pip.commands.list.ListCommand.find_packages_latest_versions,
    # but that seems like a lot of trouble, especially dealing with the
    # user's configuration of indexes and stuff.
    outdated_b = subprocess.check_output(['pip', 'list', '--outdated'])

    # default encoding.. hopefully what pip also used?
    outdated = outdated_b.decode()

    # Example: six (Current: 1.6.1 Latest: 1.9.0)
    line_re = re.compile(r'^([^ ]+) \(Current: ([^ ]+) Latest: ([^)]+)\)$')

    for line in outdated.splitlines():
        match = line_re.match(line)
        if not match:
            logger.debug("Skipping line: %s", line)
            continue

        package, current, latest = match.groups()

        name = package.lower()
        try:
            node = find_matching_node(graph, name)
        except ValueError:
            logger.info("Skipping outdated package %s,"
                        " not already in dep graph",
                        name)
            continue

        mark_check_failed(graph.node[node], 'outdated',
                          message='latest is %s' % latest)

    mark_graph_checked(graph, 'outdated')

    return graph


def check_dag(graph):
    "Make sure the dependency graph is acyclic."

    cycles = list(nx.simple_cycles(graph))

    if cycles:
        logger.warning("There are circular dependencies!")

    for nodelist in cycles:
        for i in range(len(nodelist)):
            # -1 = index of last element in nodelist
            mark_check_failed(graph[nodelist[i - 1]][nodelist[i]],
                              'cyclic dependency')

    mark_graph_checked(graph, 'cyclic dependency')
    return bool(cycles)


def should_pin_precisely(graph, top_packages):
    """
    Annotate requirements from top packages that aren't pinned (==).

    This sets the check "not precise".
    """
    bad = False
    for src, dest, data in graph.out_edges(top_packages, data=True):
        if '==' not in data['requirement']:
            mark_check_failed(data, 'not precise', data['requirement'])
            bad = True

    mark_graph_checked(graph, 'not precise')
    return bad


def should_pin_all(graph, top_packages):
    """
    Add missing requirements from top packages to "grandchild" dependencies.

    If prj_A depends on B, which depends on C, but prj_A hasn't declared
    a dependency on C, this adds that edge to the graph, and sets the
    check "missing pin" failed on it.

    This actually looks at *all* descendants, including ones more than two
    "generations" away.
    """
    bad = False

    for package in top_packages:
        direct = set(dest for src, dest in graph.out_edges([package]))
        for dest in nx.descendants(graph, package):
            if dest not in direct:
                bad = True
                node_data = graph.node[dest]
                graph.add_edge(
                    package,
                    dest,
                    requirement=dest)
                mark_check_failed(
                    graph[package][dest],
                    'missing pin',
                    node_data['as_requirement'])

    mark_graph_checked(graph, 'missing pin')
    return bad
