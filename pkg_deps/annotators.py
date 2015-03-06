import logging
import re
import subprocess

import networkx as nx


logger = logging.getLogger(__name__)


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
            logger.debug("Skipping line ", line)
            continue

        package, current, latest = match.groups()

        name = package.lower()
        data = graph.node.get(name)

        if not data:
            logger.debug("Skipping", name, "not already in dep graph")
            continue

        data['latest'] = latest
        data['label'] = '%s (latest: %s)' % (latest, data['label'])

    return graph


def should_pin_precisely(graph, top_packages):
    """
    Annotate requirements from top packages that aren't pinned (==).

    This sets ``error_not_precise=True`` in the edge data, and
    modifies the edge label.
    """
    for src, dest, data in graph.out_edges(top_packages, data=True):
        if not data['is_pin']:
            data['error_not_precise'] = True
            data['label'] = 'PIN NOT PRECISE (%s)' % data['label']


def should_pin_all(graph, top_packages):
    """
    Add missing requirements from top packages to "grandchild" dependencies.

    If prj_A depends on B, which depends on C, but prj_A hasn't declared
    a dependency on C, this adds that edge to the graph, with the edge
    attribute ``error_indirect=True`` and an alarming label.
    """

    for package in top_packages:
        direct = set(dest for src, dest in graph.out_edges([package]))
        for dest in nx.descendants(graph, package):
            if dest not in direct:
                node_data = graph.node[dest]
                graph.add_edge(
                    package,
                    dest,
                    error_indirect=True,
                    is_pin=True,
                    label='MISSING PIN (==%s)' % node_data['version'])
