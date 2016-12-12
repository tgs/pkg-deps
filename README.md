# Print dependency info in graph form

`pkg-deps` is a tool to examine dependency information about installed Python
packages, and render it in a variety of ways.  Various checks can also be run.
As of version 1.0, the output formats include:

* human-readable text output with highlighting of problems,
* teamcity, for specially-formatted messages that the TeamCity CI tool can
  understand (to use this, use `pip install pkg-deps[teamcity]`),
* dot, for rendering with GraphViz, and
* JSON, for further processing with automated tools (including re-loading
  and combining dependency graphs by this tool!)

The checks it can run include (again, as of 1.0):

* finding dependency loops,
* finding unmet dependencies, including unmet version requirements,
* finding outdated packages,
* ensuring that certain packages specify exact ('==') version dependencies,
  and
* ensuring that certain packages do not have any indirect dependencies - e.g.
  making sure a web app pins *all* of its dependencies, including otherwise
  indirect ones.

The tool has several dependencies itself, so to avoid having to install it in
each virtualenv you want to examine, it also supports running a probe with
a different Python binary.  For example, you could install it once using
`pipsi` and then run it in your current virtualenv with `pkg-deps -p \`which
python\``.

For details on how to accomplish these things, run `pkg-deps --help`.
