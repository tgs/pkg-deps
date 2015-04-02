"""
Probe script to find dependencies.

This file is meant to be run in a virtualenv that we're interested in,
and it should only depend on the presence of setuptools.

To avoid duplication, it is also used directly as a library.  But it
must not import anything else from pkg_deps, because it's used as
a top-level Python script.
"""

import pkg_resources


def find_dependencies(packages):
    nodes = set()  # Set of strings, the packages 'as requirements'
    edges = set()  # Set of tuples, (src, req, dest)

    def find_deps(lib_name):
        dist = pkg_resources.get_distribution(lib_name)
        as_req = str(dist.as_requirement())  # e.g. 'lxml==3.2.4'

        if as_req not in nodes:
            nodes.add(as_req)

            for dependency in dist.requires():
                dep_name = find_deps(dependency.project_name)

                edges.add((
                    as_req,
                    str(dependency),
                    dep_name,
                ))

        return as_req

    top_nodes = [find_deps(pkg) for pkg in packages]

    return (top_nodes, list(nodes), list(edges))


if __name__ == '__main__':
    import sys
    import pprint
    args = list(sys.argv[1:])
    deps = find_dependencies(args)
    # TODO: handle package names with non-ascii chars
    pprint.pprint(deps)
