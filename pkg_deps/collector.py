"""
Collect dependency information about packages.

To work, these functions need to be run within a virtualenv where you've
installed the packages you're insterested in.  In particular, you must
also install the top-level package (Django project, for example).
"""
import pkg_resources
import pickle
import subprocess

import networkx as nx

from pkg_deps import probe


def collect_dependencies_here(packages, graph=None):
    """
    Consult setuptools for dependencies of a package, returning  a graph.

    Parameters:
        packages - the names of the packages to use as the root of
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
    return dependencies_to_graph(
        *probe.find_dependencies(packages),
        graph=graph)


def collect_dependencies_elsewhere(python, packages, graph=None):
    deps = run_probe(python, packages)
    return dependencies_to_graph(*deps, graph=graph)


def run_probe(python, packages):
    # Send probe.py to the target python as a stream,
    # and read back the pickled package information!
    probe_stream = pkg_resources.resource_stream('pkg_deps', 'probe.py')

    proc = subprocess.Popen(
        [python, '-', '--pickle'] + list(packages),
        stdin=probe_stream,
        stdout=subprocess.PIPE,
    )

    output = proc.communicate()[0]

    if proc.wait() != 0:
        raise RuntimeError("Problem executing probe with %s" % python)

    return pickle.loads(output)


def dependencies_to_graph(top_nodes, nodes, edges, graph=None):
    if not graph:
        graph = nx.DiGraph()

    for node in nodes:
        if node not in graph:
            graph.add_node(node, as_requirement=node)

    for source, requirement, target in edges:
        graph.add_edge(
            source,
            target,
            requirement=requirement)

    graph.graph.setdefault('query packages', []).extend(top_nodes)
    return (graph, top_nodes)
