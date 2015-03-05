"""
Collect dependency information about packages.

To work, these functions need to be run within a virtualenv where you've
installed the packages you're insterested in.  In particular, you must
also install the top-level package (Django project, for example).
"""
import logging
import pkg_resources
import re
import subprocess

import networkx as nx


logger = logging.getLogger(__name__)


__all__ = [
    'collect_dependencies',
    'add_available_updates',
]


def format_specs(specs):
    if not specs:
        return 'any'
    return ','.join(''.join(parts) for parts in specs)


def default_req_info(req):
    # return dict of info about a requirement
    return {
        'label': format_specs(req.specs),
        'is_pin': any(eq == '==' for eq, version in req.specs),
        'specs': req.specs,
    }


def default_dist_info(dist):
    return {
        'label': str(dist),
        'version': dist.version,
    }


def collect_dependencies(package,
                         req_info=default_req_info,
                         dist_info=default_dist_info,
                         graph=None):
    """
    Consult setuptools for dependencies of a package, returning  a graph.

    Parameters:
        package - the name of the package to use as the root of
            the dependency tree.
        req_info - optional single-argument function,
            pkg_resources.Requirement -> dict, that sets the attributes
            of the edges linking package nodes.  Default is
            ``default_req_info``.
        dist_info - optional single-argument function,
            pkg_resources.DistInfoDistribution -> dict, that
            sets the node attributes in the graph.  Default is
            ``default_dist_info``.
        graph - optional networkx.DiGraph to update, otherwise a new
            one is created.
    """
    if not graph:
        graph = nx.DiGraph()

    def find_reqs(lib_name):
        dist = pkg_resources.get_distribution(lib_name)
        name = dist.project_name.lower()

        if name not in graph.node:
            graph.add_node(
                name,
                **dist_info(dist))

        for req in dist.requires():
            req_name = find_reqs(req.project_name)

            graph.add_edge(
                name,
                req_name,
                **req_info(req))

        return name

    top_node = find_reqs(package)
    return (graph, top_node)


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
