import pkg_resources
import networkx as nx


def format_specs(specs):
    if not specs:
        return 'any'
    return ','.join(''.join(parts) for parts in specs)


def req_info(req):
    # return dict of info about a requirement
    return {
        'label': format_specs(req.specs),
        'is_pin': any(eq == '==' for eq, version in req.specs),
        'specs': req.specs,
    }


def dist_info(dist):
    return {
        'label': str(dist),
        'version': dist.version,
    }


def collect_dependencies(package, req_info=req_info, dist_info=dist_info):
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
