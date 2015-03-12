from pkg_resources import Requirement
import unittest

import networkx as nx

from pkg_deps import annotators as ann


class DummyDist:
    def __init__(self, pkg, version):
        self.project_name = pkg
        self.version = version

    def __str__(self):
        return ' '.join([self.project_name, self.version])


def add_node(graph, pkg, version):
    as_req = str(Requirement.parse('%s==%s' % (pkg, version)))
    graph.add_node(as_req, as_requirement=as_req)
    return as_req


def add_edge(graph, pkg, req_str):
    dest = ann.find_matching_node(graph, req_str)
    graph.add_edge(pkg, dest, requirement=req_str)


class MissingPinsTestCase(unittest.TestCase):
    def test_precise_pin(self):
        graph = nx.DiGraph()
        prj = add_node(graph, 'prj', '1.0')

        # Not pinned but should be
        things = add_node(graph, 'things', '1.2')
        add_edge(graph, prj, 'things>=1')

        # Pinned
        xbox = add_node(graph, 'xbox', '360')
        add_edge(graph, prj, 'xbox==360')

        ann.should_pin_precisely(graph, [prj])

        self.assertTrue('not precise' in ann.failed_checks(graph[prj][things]))
        self.assertFalse('not precise' in ann.failed_checks(graph[prj][xbox]))

    def test_should_pin_all(self):
        # Test that we can detect when a top-level package indirectly depends
        # on something but doesn't have it pinned.

        graph = nx.DiGraph()

        # We set up a dependency relationship:
        # sit -> chair -> floor -> joist
        # Sit has pinned chair and joist, but not floor.
        # Lower-level packages don't have to pin, only the top-level one.
        sit = add_node(graph, 'sit', '1.0')
        chair = add_node(graph, 'chair', '0.9')
        floor = add_node(graph, 'floor', '6.22')
        joist = add_node(graph, 'joist', '5')

        add_edge(graph, sit, 'chair==0.9')

        add_edge(graph, chair, 'floor>=6,<7')
        # Missing        sit -> floor

        add_edge(graph, sit, 'joist==5')
        add_edge(graph, floor, 'joist==5')

        self.assertNotIn(floor, graph[sit])

        ann.should_pin_all(graph, [sit])

        # We should have found the missing pin
        self.assertIn(floor, graph[sit].keys())
        self.assertIn('missing pin', ann.failed_checks(graph[sit][floor]))
        self.assertIn('requirement', graph[sit][floor])

        # Don't fail the pin that is correct
        self.assertIn(joist, graph[sit].keys())
        self.assertNotIn('missing pin', ann.failed_checks(graph[sit][joist]))

    def test_check_dag(self):
        graph = nx.DiGraph()

        believing = add_node(graph, "believing", "3.7")
        seeing = add_node(graph, "seeing", "4.22")
        narcissism = add_node(graph, "narcissism", "100")

        add_edge(graph, believing, "seeing>3")
        add_edge(graph, seeing, "believing")
        add_edge(graph, narcissism, "narcissism")

        ann.check_dag(graph)

        self.assertIn('cycle', ann.failed_checks(graph[seeing][believing]))
        self.assertIn('cycle', ann.failed_checks(graph[believing][seeing]))
        self.assertIn('cycle', ann.failed_checks(graph[narcissism][narcissism]))

    def test_find_matching_node(self):
        graph = nx.DiGraph()
        Things = add_node(graph, 'Things', '1.0')

        self.assertEqual('Things==1.0',
                         ann.find_matching_node(graph, 'things>0.5'))

    def test_find_matching_node_fail(self):
        graph = nx.DiGraph()
        Things = add_node(graph, 'Things', '1.0')

        try:
            ann.find_matching_node(graph, 'STUFF>0.5')
            self.fail("Should have gotten ValueError")
        except ValueError:
            pass
