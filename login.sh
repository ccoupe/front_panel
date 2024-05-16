#!/bin/bash
#/home/pi/.shoes/walkabout/shoes /home/pi/login/login.rb
#cd /home/ccoupe/login
source ~/tb-env/bin/activate
cd /usr/local/lib/tblogin
node=`hostname`
python3 login.py -s -c ${node}.json
