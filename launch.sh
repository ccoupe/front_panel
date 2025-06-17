#!/bin/bash
nm-online
source PYENV/bin/activate
NODE=`hostname`
cd /usr/local/lib/tblogin
uv run main.py -s -c ${NODE}.json
