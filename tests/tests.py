import json
import os
from pkg_resources import Requirement
import shutil
import subprocess
import tempfile
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


class UnitTestCase(unittest.TestCase):
    def test_precise_pin(self):
        graph = nx.DiGraph()
        prj = add_node(graph, 'prj', '1.0')

        # Not pinned but should be
        things = add_node(graph, 'things', '1.2')
        add_edge(graph, prj, 'things>=1')

        # Pinned
        xbox = add_node(graph, 'xbox', '360')
        add_edge(graph, prj, 'xbox==360')

        self.assertTrue(ann.should_pin_precisely(graph, [prj]))

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

        self.assertTrue(ann.should_pin_all(graph, [sit]))

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

        self.assertTrue(ann.check_dag(graph))

        self.assertIn('cyclic dependency',
                      ann.failed_checks(graph[seeing][believing]))
        self.assertIn('cyclic dependency',
                      ann.failed_checks(graph[believing][seeing]))
        self.assertIn('cyclic dependency',
                      ann.failed_checks(graph[narcissism][narcissism]))

    def test_deps_should_be_met(self):
        graph = nx.DiGraph()

        wakefulness = add_node(graph, 'wakefulness', '1.1')
        coffee = add_node(graph, 'coffee', '0.7')
        add_edge(graph, wakefulness, 'coffee')

        graph[wakefulness][coffee]['requirement'] = 'coffee>1'

        self.assertTrue(ann.dependencies_should_be_met(graph))
        self.assertIn('unmet',
                      ann.failed_checks(graph[wakefulness][coffee]))

    def test_find_matching_node(self):
        graph = nx.DiGraph()
        add_node(graph, 'Things', '1.0')

        self.assertEqual('Things==1.0',
                         ann.find_matching_node(graph, 'things>0.5'))

    def test_find_matching_node_fail(self):
        graph = nx.DiGraph()
        add_node(graph, 'Things', '1.0')

        try:
            ann.find_matching_node(graph, 'STUFF>0.5')
            self.fail("Should have gotten ValueError")
        except ValueError:
            pass


class IntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_area = tempfile.mkdtemp()

        cls.test_env = os.path.join(cls.test_area, 'env')
        cls.test_pip = os.path.join(cls.test_env, 'bin', 'pip')
        cls.test_python = os.path.join(cls.test_env, 'bin', 'python')

        cls.integration_dir = os.path.join(
            os.path.dirname(__file__), 'integration')

        subprocess.check_call(['virtualenv', '-q', cls.test_env])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_area)

    def test_loop(self):
        "Test that a dependency loop is correctly identified"

        loopA_dir = os.path.join(self.integration_dir, 'loopA')
        loopB_dir = os.path.join(self.integration_dir, 'loopB')

        subprocess.check_call(
            [self.test_pip, 'install', '-q', '--no-deps', loopA_dir])

        subprocess.check_call(
            [self.test_pip, 'install', '-q', '--no-deps', loopB_dir])

        with self.assertRaises(subprocess.CalledProcessError) as raised:
            subprocess.check_output(
                ['pkg_deps', '--python', self.test_python, 'loopA'])

        output = raised.exception.output

        self.assertIn(
            'depends on loopB (loopB==1.0 is installed) - cycl',
            output.decode('utf-8'))

    def test_normalization(self):
        "Test that _ vs - and CAPS vs lower are dealt with by the graph maker"
        for pkg in ['normalization-top',
                    'Normalization_Foo',
                    'normalization-bar']:
            subprocess.check_call(
                [self.test_pip, 'install', '-q', '--no-deps',
                 os.path.join(self.integration_dir, pkg)])

        result = subprocess.check_output(
            ['pkg_deps', '--python', self.test_python,
             'normalization-top'])

        lines = result.decode('utf-8').splitlines()

        # top depends on both foo and bar, those are the only deps.
        self.assertEqual(2, len([line
                                 for line in lines
                                 if 'depends on' in line]))

    def test_combining_json(self):
        "Test that we can combine JSON output from multiple runs"

        # Install two packages in a test virtualenv,
        # and separately run pkg_deps --json on each of them.
        json_files = []
        for num, pkg in enumerate(['Normalization_Foo',
                                   'normalization-bar']):
            subprocess.check_call(
                [self.test_pip, 'install', '-q', '--no-deps',
                 os.path.join(self.integration_dir, pkg)])

            json_file = os.path.join(self.test_area, '%d.json' % num)
            with open(json_file, 'wb') as json_out:
                subprocess.check_call(
                    ['pkg_deps',
                     '--python', self.test_python,
                     '--json', pkg],
                    stdout=json_out)
            json_files.append(json_file)

        # Combine the results from the two runs, and make sure
        # it looks like we want it to.
        result = subprocess.check_output(
            ['pkg_deps', '--json', '--load-json'] + json_files)

        combined = json.loads(result.decode())
        graph_data = dict(combined['graph'])
        self.assertEqual(set(graph_data['query packages']),
                         set(['Normalization-Foo==1.0',
                              'normalization-bar==1.0']))

        self.assertEqual(len(combined['links']), 0)
