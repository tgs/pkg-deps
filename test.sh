#!/bin/bash

set -e

echo "Enabling Python 2.7, 3.3, 3.4"

export PATH="$PATH:/opt/python-2.7/bin"
source /opt/rh/python33/enable
source /opt/python-3.4/activate.sh

if [ ! -f toxenv/bin/tox ]; then
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
