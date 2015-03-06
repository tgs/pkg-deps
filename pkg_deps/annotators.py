import logging
import re
import subprocess


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
        if name not in graph.node:
            logger.debug("Skipping", name, "not already in dep graph")
            continue

        graph.node[name]['latest'] = latest

    return graph


def add_missing_pins(graph, top_packages):
    """Find missing pins - missing if top package depends
    only indirectly, or does not pin the version."""

    flag_unpinned_dependencies(graph, top_packages)

    add_indirect_dependencies(graph, top_packages)


def flag_unpinned_dependencies(graph, top_packages):
    for src, dest, data in graph.out_edges(top_packages, data=True):
        if not data['is_pin']:
            data['error_unpinned'] = True
            data['label'] = data['label'] + ' UNPINNED'


def add_indirect_dependencies(graph, top_packages):
    direct = set(dest for src, dest in graph.out_edges(top_packages))

    for package in top_packages:
        for dest in graph.successors_iter(package):
            print('Considering', dest)
            if dest not in direct:
                print('Adding', dest)
                node_data = graph.node[dest]
                graph.add_edge(
                    package,
                    dest,
                    error_indirect=True,
                    label='MISSING PIN ==' + node_data['version'])
