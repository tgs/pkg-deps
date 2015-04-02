#!/bin/bash

set -e

which python2.7
which python3.3
which python3.4

TOX=`which tox || true`

if [ ! -z "$TOX" ]; then
	echo "Already have tox: $TOX"
elif [ ! -f toxenv/bin/tox ]; then
	echo "Making virtualenv to run tox"
	rm -rf toxenv
	virtualenv toxenv
	source toxenv/bin/activate
	pip install tox
else
	echo "Re-using tox virtualenv"
	source toxenv/bin/activate
fi

tox "$@"
