#!/bin/bash
cp -a /home/pi/Projects/iot/login/* /home/pi/login
systemctl --user restart tblogin
