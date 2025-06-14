#!/bin/bash
nm-online
source PYENV/bin/activate
NODE=`hostname`
cd /usr/local/lib/tblogin
python3 main.py -s -c ${NODE}.json
