"""
Collect dependency information about packages.

To work, these functions need to be run within a virtualenv where you've
installed the packages you're insterested in.  In particular, you must
also install the top-level package (Django project, for example).
"""
import pkg_resources

import networkx as nx


__all__ = [
    'collect_dependencies',
]


def collect_dependencies(package, graph=None):
    """
    Consult setuptools for dependencies of a package, returning  a graph.

    Parameters:
        package - the name of the package to use as the root of
            the dependency tree.
        graph - optional networkx.DiGraph to update, otherwise a new
            one is created.

    Returns:
        A networkx.DiGraph with nodes and edges representing the dependencies
        downstream of the given package.  The nodes' keys are "requirement
        strings" like you might find in requirements.txt - for instance
        ``lxml==3.2.4``.  The nodes also have an attribute, ``as_requirement``,
        that holds the same string (so you can rename the nodes without losing
        information).  The edges have an attribute ``requirement`` that is the
        canonical form of the exact requirement one package used to depend on
        another.  "Canonical" means that, for example, version numbers are
        sorted: 'Django<1.7,>=1.6' becomes 'Django>=1.6,<1.7'.

    See also:
        networkx.relabel_nodes
    """
    if not graph:
        graph = nx.DiGraph()

    def find_deps(lib_name):
        dist = pkg_resources.get_distribution(lib_name)
        as_req = str(dist.as_requirement())  # e.g. 'lxml==3.2.4'

        if as_req not in graph.node:
            graph.add_node(
                as_req,
                as_requirement=as_req,
            )

        for dependency in dist.requires():
            dep_name = find_deps(dependency.project_name)

            graph.add_edge(
                as_req,
                dep_name,
                requirement=str(dependency),
            )

        return as_req

    top_node = find_deps(package)
    graph.graph.setdefault('query packages', []).append(top_node)
    return (graph, top_node)
