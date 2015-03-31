# Print dependency info in graph form

`pkg_deps` is a tool to examine dependency information about installed Python
packages, and render it in a variety of ways.  Various checks can also be run.
As of version 0.4, the output formats include:

* dot, for rendering with GraphViz,
* human-readable text output, and
* JSON, for further processing with automated tools (including re-loading
  and combining dependency graphs by this tool, soon!)

The checks it can run include (again, as of 0.4):

* finding dependency loops,
* finding outdated packages,
* ensuring that certain packages specify exact ('==') version dependencies,
  and
* ensuring that certain packages do not have any indirect dependencies - e.g.
  making sure a web app pins *all* of its dependencies, including otherwise
  indirect ones.

The tool has several dependencies itself, so to avoid having to install it in
each virtualenv you want to examine, it also supports running a probe with a
different Python binary.  For example, you could install it once, and then
run it on each mini-environment that Tox creates.

For details on how to accomplish these things, run `pkg_deps --help`.
