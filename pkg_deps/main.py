#!/usr/bin/env python
import logging

import click

from . import collector
from . import annotators
from . import writers


_log_levels = [
    logging.CRITICAL,
    logging.ERROR,
    logging.WARNING,
    logging.INFO,
    logging.DEBUG,
]


@click.command()
@click.argument('packages', nargs=-1, required=True)
@click.option('--outdated', is_flag=True, help="Look for outdated packages.")
@click.option('--target-python', type=click.Path(), default=None,
              help="""Look in this Python installation (i.e. virtualenv)
              to find dependency information.  PATH is the path to the python
              executable itself.  Incompatible with --outdated for now.""")
@click.option('--human', 'format', flag_value='human', default=True,
              help="Print results in simple human-readable form.")
@click.option('--dot', 'format', flag_value='dot',
              help="""Write in the GraphViz 'dot' format, for direct
              visualization.""")
@click.option('--json', 'format', flag_value='json',
              help="""Write in a 'node-link' JSON format, for use with other
              Python tools or d3.js.""")
@click.option('--precise-pin', is_flag=True,
              help="""Annotate packages that the top-level package depends on
              directly without exactly pinning the version (xyz==N.N).""")
@click.option('--should-pin-all', is_flag=True,
              help="""Annotate packages that the top-level package depends on
              indirectly but not directly.""")
@click.option('--verbose', '-v', count=True,
              help="Control the logging level.")
@click.option('--quiet', '-q', count=True,
              help="Control the logging level.")
def main(packages, outdated, target_python, format, precise_pin,
         should_pin_all, verbose, quiet):
    """Print dependencies and latest versions available."""

    log_level_requested = verbose - quiet + 2  # default is WARNING

    logging.basicConfig(
        format='%(levelname)s: %(message)s',
        level=_log_levels[min(log_level_requested, len(_log_levels) - 1)])

    if target_python:
        graph, good_package_names = collector.collect_dependencies_elsewhere(
            target_python, packages)
    else:
        graph, good_package_names = collector.collect_dependencies_here(
            packages)

    annotators.check_dag(graph)

    if outdated:
        annotators.add_available_updates(graph)

    if precise_pin:
        annotators.should_pin_precisely(graph, good_package_names)

    if should_pin_all:
        annotators.should_pin_all(graph, good_package_names)

    getattr(writers, format)(graph)


if __name__ == '__main__':
    main()
