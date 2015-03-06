import pkg_resources
import unittest

import networkx as nx

from pkg_deps import annotators as ann
from pkg_deps import collector as coll


class DummyDist:
    def __init__(self, pkg, version):
        self.project_name = pkg
        self.version = version

    def __str__(self):
        return ' '.join([self.project_name, self.version])


def add_node(graph, pkg, version):
    dummy = DummyDist(pkg, version)
    graph.add_node(pkg, **coll.default_dist_info(dummy))


def add_edge(graph, pkg, req_str):
    dummy = pkg_resources.Requirement.parse(req_str)
    dest = dummy.project_name
    graph.add_edge(pkg, dest, **coll.default_req_info(dummy))


class MissingPinsTestCase(unittest.TestCase):
    def test_unpinned_deps(self):
        graph = nx.DiGraph()
        add_node(graph, 'prj', '1.0')

        # Not pinned but should be
        add_node(graph, 'things', '1.2')
        add_edge(graph, 'prj', 'things>=1')

        # Pinned
        add_node(graph, 'xbox', '360')
        add_edge(graph, 'prj', 'xbox==360')

        ann.flag_unpinned_dependencies(graph, ['prj'])

        self.assertTrue('error_unpinned' in graph['prj']['things'])
        self.assertFalse('error_unpinned' in graph['prj']['xbox'])

    def test_indirect_deps(self):
        graph = nx.DiGraph()
        add_node(graph, 'sit', '1.0')

        add_node(graph, 'chair', '0.9')
        add_edge(graph, 'sit', 'chair==0.9')

        add_node(graph, 'floor', '6.22')
        add_edge(graph, 'chair', 'floor>=6,<7')
        # Missing edge from sit to floor

        add_node(graph, 'joist', '5')
        add_edge(graph, 'floor', 'joist==5')
        # joist is correctly pinned
        add_edge(graph, 'sit', 'joist==5')

        self.assertNotIn('floor', graph['sit'])

        ann.add_indirect_dependencies(graph, ['sit'])

        self.assertIn('floor', graph['sit'].keys())
        self.assertIn('error_indirect', graph['sit']['floor'])
