#!/usr/bin/env python3
import json
import socket
from uuid import getnode as get_mac
import os 
import sys

class Settings:

  def __init__(self, etcf, log):
    self.etcfname = etcf
    self.log = log
    self.mqtt_server = "192.168.1.7"   # From json
    self.mqtt_port = 1883              # From json
    self.mqtt_client_name = "detection_1"   # From json
    self.homie_device = None            # From json
    self.homie_name = None              # From json
    # IP and MacAddr are not important (should not be important).
    if sys.platform.startswith('linux'):
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
      s.connect(('<broadcast>', 0))
      self.our_IP =  s.getsockname()[0]
      # from stackoverflow (of course):
      self.macAddr = ':'.join(("%012x" % get_mac())[i:i+2] for i in range(0, 12, 2))
    elif sys.platform.startswith('darwin'):
      host_name = socket.gethostname() 
      self.our_IP = socket.gethostbyname(host_name) 
      self.macAddr = ':'.join(("%012x" % get_mac())[i:i+2] for i in range(0, 12, 2))
    else:
      self.our_IP = "192.168.1.255"
      self.macAddr = "de:ad:be:ef"
    self.macAddr = self.macAddr.upper()
    # default config  ~/.trumpybear
    self.db_path = os.path.join(os.getenv('HOME'),'.trumpybear')
    self.load_settings(self.etcfname)
    self.status_topic = 'homie/'+self.homie_device+'/control/cmd'
    self.log.info("Settings from %s" % self.etcfname)
    
  def load_settings(self, fn):
    conf = json.load(open(fn))

    self.mqtt_server = conf.get("mqtt_server_ip", "192.168.1.7")
    self.mqtt_port = conf.get("mqtt_port", 1883)
    self.mqtt_client_name = conf.get("mqtt_client_name", "trumpy_67")
    self.homie_device = conf.get('homie_device', "test_bear")
    self.homie_name = conf.get('homie_name', 'Test Bear Bronco')
    self.hscn_sub = conf.get('hscn_sub', "homie/test_bear/screen/control/set")
    self.hcmd_pub = conf.get('hcmd_pub', "homie/test_bear/control/cmd/set")
    self.hscn_pub = conf.get('hscn_pub', "homie/test_bear/screen/control")
    self.hdspm_sub = conf.get('hdspm_sub', 'homie/trumpy_ranger/display/mode/set')
    self.hdspt_sub = conf.get('hdspt_sub', 'homie/trumpy_ranger/display/text/set')
    self.htur1_pub = conf.get('htur1_pub', 'homie/turret_front/turret_1/control/set')
    self.htur2_pub = conf.get('htur2_pub', 'homie/turret_back/turret_1/control/set')
    self.htur1_sub = conf.get('htur1_sub', 'homie/turret_font/turret_1/control')
    self.htur2_sub = conf.get('htur2_sub', 'homie/turret_back/turret_1/control')
    self.htrkv_sub = conf.get('htrkv_sub', 'homie/panel_tracker/track/control/set')
    self.alarm_pub = conf.get('alarm_pub', 'homie/trumpy_bear/control/cmd')


  def print(self):
    self.log.info("==== Settings ====")
    self.log.info(self.settings_serialize())
  
  def settings_serialize(self):
    st = {}
    st['mqtt_server_ip'] = self.mqtt_server
    st['mqtt_port'] = self.mqtt_port
    st['mqtt_client_name'] = self.mqtt_client_name
    st['homie_device'] = self.homie_device 
    st['homie_name'] = self.homie_name
    st['hscn_sub'] = self.hscn_sub
    st['hcmd_pub'] = self.hcmd_pub
    st['hscn_pub'] = self.hscn_pub
    st['hdspm_sub'] = self.hdspm_sub
    st['hdspt_sub'] = self.hdspt_sub
    st['htur1_pub'] = self.htur1_pub
    st['htur2_pub'] = self.htur2_pub
    st['htur1_sub'] = self.htur1_sub
    st['htur2_sub'] = self.htur2_sub
    st['htrkv_sub'] = self.htrkv_sub
    st['alarm_pub'] = self.alarm_pub
    str = json.dumps(st)
    return str

  def settings_deserialize(self, jsonstr):
    st = json.loads(jsonstr)
