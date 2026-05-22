#!/bin/bash
nm-online
source PYENV/bin/activate
NODE=`hostname`
cd /usr/local/lib/tblogin
python3 login.py -s -c ${NODE}.json
