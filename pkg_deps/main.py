#!/usr/bin/env python
import logging
import sys

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
@click.option('--python', '-p', type=click.Path(), default=None,
              help="Look in this Python installation (i.e. virtualenv) to find"
              " dependency information.  PATH is the path to the python"
              " executable itself.  Incompatible with --outdated for now.""")
@click.option('--human', 'format', flag_value='human', default=True,
              help="Print results in simple human-readable form. (DEFAULT)")
@click.option('--dot', 'format', flag_value='dot',
              help="Write in the GraphViz 'dot' format, for direct"
              " visualization.")
@click.option('--json', 'format', flag_value='json',
              help="Write in a 'node-link' JSON format, for use with other"
              " Python tools or d3.js.")
@click.option('--teamcity', 'format', flag_value='teamcity',
              help="Write any problems as TeamCity buildProblem messages.")
@click.option('--load-json', 'argument_type', flag_value='json',
              help="Treat arguments as JSON files instead of package names;"
              " combine them, DON'T RUN any checks, and print the"
              " resulting graph.")
@click.option('--packages', 'argument_type', flag_value='packages',
              default=True,
              help="Treat arguments as package names; find their"
              " dependencies, run any checks, and print the resulting graph."
              " (DEFAULT)")
@click.option('--precise-pin', is_flag=True,
              help="Annotate packages that the top-level package depends on"
              " directly without exactly pinning the version (xyz==N.N).")
@click.option('--should-pin-all', is_flag=True,
              help="Annotate packages that the top-level package depends on"
              " indirectly but not directly.")
@click.option('--verbose', '-v', count=True,
              help="Control the logging level.")
@click.option('--quiet', '-q', count=True,
              help="Control the logging level.")
def main(packages, outdated, python, format, argument_type, precise_pin,
         should_pin_all, verbose, quiet):
    """
    Search the package dependencies in a virtualenv for various problems.

    By default, dependency cycles and unmet dependencies (including unmet
    version requirements) cause an error return code and get annotated
    in the output.
    """

    log_level_requested = verbose - quiet + 2  # default is WARNING

    logging.basicConfig(
        format='%(levelname)s: %(message)s',
        level=_log_levels[min(log_level_requested, len(_log_levels) - 1)])

    any_problems = False

    if argument_type == 'packages':
        if python:
            if outdated:
                click.secho("--outdated is incompatible with --target-python"
                            " for now - sorry!", fg='red')
                # We could use the target python to run
                # "python -m pip list --outdated"
                # TODO!
                sys.exit(1)
            graph, good_package_names = collector.collect_dependencies_elsewhere(
                python, packages)
        else:
            graph, good_package_names = collector.collect_dependencies_here(
                packages)

        any_problems |= annotators.check_dag(graph)

        any_problems |= annotators.dependencies_should_be_met(graph)

        if outdated:
            any_problems |= annotators.add_available_updates(graph)

        if precise_pin:
            any_problems |= annotators.should_pin_precisely(graph,
                                                            good_package_names)

        if should_pin_all:
            any_problems |= annotators.should_pin_all(graph,
                                                      good_package_names)

    else:
        assert argument_type == 'json'
        graph = collector.combine_json_graphs(packages)

    getattr(writers, format)(graph)
    sys.exit(any_problems)


if __name__ == '__main__':
    main()
