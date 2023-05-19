#! /bin/bash
# 
# startup test Trumpy Bear
#   Don't use /etc/xdg/lxsession/LXDE-pi/autostart 
#	this replaces that for Testing.
systemctl --user restart mqttmycroft
systemctl --user restart mycroft
systemctl --user restart tblogin
systemctl --user restart trumpy

