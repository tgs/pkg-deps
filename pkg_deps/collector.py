"""
Collect dependency information about packages.

To work, these functions need to be run within a virtualenv where you've
installed the packages you're insterested in.  In particular, you must
also install the top-level package (Django project, for example).
"""
import ast
import json
import logging
import subprocess

import networkx as nx
from networkx.readwrite.json_graph import node_link

from pkg_deps import probe


logger = logging.getLogger(__name__)


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


def _not_pyc(path):
    "So we can use probe.__file__: strip c off of .pyc"
    return path.rstrip('c')


def run_probe(python, packages):
    # Could do this, would maybe be zip-safe, but it's annoying for debugging.
    #probe_stream = pkg_resources.resource_stream('pkg_deps', 'probe.py')
    # And then stdin=probe_stream.

    proc = subprocess.Popen(
        [python, _not_pyc(probe.__file__)] + list(packages),
        stdout=subprocess.PIPE,
    )

    output = proc.communicate()[0]

    if proc.wait() != 0:
        raise RuntimeError("Problem executing probe with %s" % python)

    return ast.literal_eval(output.decode())  # default encoding...


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


def combine_json_graphs(filenames):
    if not filenames:
        return nx.DiGraph()

    graphs = []
    for fn in filenames:
        with open(fn, 'r') as json_file:
            graph_data = json.load(json_file)
            graphs.append(node_link.node_link_graph(graph_data))
    composed = nx.compose_all(graphs)

    # TODO: try to merge edge annotations that may differ between graphs
    query_packages = sum([G.graph['query packages'] for G in graphs], [])
    composed.graph['query packages'] = query_packages

    check_lists = [G.graph['checks'] for G in graphs]
    last = None
    for check_list in check_lists:
        # TODO test this
        if last is not None and set(check_list) != last:
            logger.warning("Loading several dependency graphs, but they were"
                           " run with different consistency checks - edge"
                           " annotations may be incorrect!")

        last = set(check_list)

    return composed
