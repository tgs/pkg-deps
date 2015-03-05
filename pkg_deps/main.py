#!/usr/bin/env python
from . import collector


usage = """
pkg_deps: print dependencies and latest versions available.

Usage:
    pkg_deps <package> [<package ...>]

"""


def main():
    import sys

    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(usage)
        sys.exit(1)

    g, t = collector.collect_dependencies(sys.argv[1])

    if len(sys.argv) > 2:
        for pkg in sys.argv[2:]:
            collector.collect_dependencies(pkg, graph=g)

    collector.add_available_updates(g)

    simple_print(g)


def simple_print(graph):
    for pkg in graph:
        node = graph.node[pkg]

        if 'latest' in node:
            latest = '(Latest: {latest})'.format(**node)
        else:
            latest = ''

        print(node['label'], latest)

        for _, req, edge in graph.out_edges([pkg], data=True):
            req_node = graph.node[req]

            print('  depends on %s (%s is installed)' % (
                req + ' ' + edge['label'], req_node['version']))


if __name__ == '__main__':
    main()
