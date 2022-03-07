#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import sys, traceback
import json
from datetime import datetime
import time
from threading import Thread

import time

class Homie_MQTT:

  def __init__(self, settings, callback):
    self.settings = settings
    self.log = settings.log
    self.callback = callback
    
    # init server connection
    self.client = mqtt.Client(settings.mqtt_client_name, False)
    #self.client.max_queued_messages_set(3)
    hdevice = self.hdevice = self.settings.homie_device  # "device_name"
    hlname = self.hlname = self.settings.homie_name     # "Display Name"
    # beware async timing with on_connect

    self.client.on_message = self.on_message
    self.client.on_disconnect = self.on_disconnect
    rc = self.client.connect(settings.mqtt_server, settings.mqtt_port)
    if rc != mqtt.MQTT_ERR_SUCCESS:
        self.log.warn("network missing?")
        exit()
    self.client.loop_start()
      

    # Shoes app listens for login/registation info at:
    #self.hscn_pub = f'homie/{hdevice}/screen/control/set'
    sublist = [self.settings.hscn_sub,
              self.settings.hdspm_sub, 
              self.settings.hdspt_sub,
              self.settings.htur1_sub,
              self.settings.htur2_sub,
              self.settings.htrkv_sub,
              self.settings.notecmd_sub,
              self.settings.notetext_sub]
    self.log.debug("Homie_MQTT __init__")
    for sub in sublist:
      rc,_ = self.client.subscribe(sub)
      if rc != mqtt.MQTT_ERR_SUCCESS:
        self.log.warn(f"Subscribe to {sub} failed: {rc}")
      else:
        self.log.debug(f"Init() Subscribed to {sub}") 
    
  def on_subscribe(self, client, userdata, mid, granted_qos):
    self.log.debug("Subscribed to %s" % self.hurl_sub)

  def on_message(self, client, userdata, message):
    global settings
    topic = message.topic
    payload = str(message.payload.decode("utf-8"))
    self.log.debug("on_message %s %s" % (topic, payload))
    cb_thr = Thread(target=self.callback, args=(topic,payload))
    cb_thr.start()
    
  def isConnected(self):
    return self.mqtt_connected

  def on_connect(self, client, userdata, flags, rc):
    self.log.debug("Subscribing: %s %d" (type(rc), rc))
    if rc == 0:
      self.log.debug("Connecting to %s" % self.mqtt_server_ip)
      rc,_ = self.client.subscribe(self.hurl_sub)
      if rc != mqtt.MQTT_ERR_SUCCESS:
        self.log.debug("Subscribe failed: ", rc)
      else:
        self.log.debug("Subscribed to %s" % self.hurl_sub)
        self.mqtt_connected = True
    else:
      self.log.debug("Failed to connect: %d" %rc)
    self.log.debug("leaving on_connect")
       
  def on_disconnect(self, client, userdata, rc):
    self.mqtt_connected = False
    self.log.debug("mqtt reconnecting")
    self.client.reconnect()
      

