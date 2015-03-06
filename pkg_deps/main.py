#!/usr/bin/env python
import click

from . import collector
from . import annotators
from . import writers


@click.command()
@click.argument('packages', nargs=-1, required=True)
@click.option('--outdated', is_flag=True, help="Look for outdated packages.")
@click.option('--human', 'format', flag_value='human', default=True,
              help="Print results in simple human-readable form.")
@click.option('--dot', 'format', flag_value='dot',
              help="Write in the GraphViz 'dot' format.")
@click.option('--graphml', 'format', flag_value='graphml',
              help="Write in the XML-based GraphML format.")
@click.option('--json', 'format', flag_value='json',
              help="Write in a d3.js-compatible 'node-link' JSON format.")
@click.option('--should-pin', is_flag=True,
              help="""Annotate packages that the top-level package
              depends on only indirectly or does not pin the version.""")
def main(packages, outdated, format, should_pin):
    """Print dependencies and latest versions available."""

    graph = None

    good_package_names = []
    for package in packages:
        graph, top = collector.collect_dependencies(package, graph=graph)
        good_package_names.append(top)

    if outdated:
        annotators.add_available_updates(graph)

    if should_pin:
        annotators.add_missing_pins(graph, good_package_names)

    getattr(writers, format)(graph)


if __name__ == '__main__':
    main()
