# from tkinter import *
from tkinter import ttk
from lib.Homie_MQTT import Homie_MQTT
# import sys
import json


class TurretSlider:

  def publish(self, val):
      rval = round(float(val), 1)
      if self.typefld == 'pan':
        pdt = {'pan': rval}
      else:
        pdt = {'tilt': rval}
      self.hmqtt.client.publish(self.topic, json.dumps(pdt), False, 1)
      print(rval, pdt)
      self.pv['text'] = str(rval)
      
  def __init__(self, parent, name, scalewidth, turret, hmqtt: Homie_MQTT):
    self.topic = f"{turret['topic']}/set"
    self.hmqtt = hmqtt
    if name == 'Pan':
      self.minv = turret['pan_min']
      self.maxv = turret['pan_max']
      self.typefld = 'pan'
    elif name == 'Tilt':
      self.minv = turret['tilt_min']
      self.maxv = turret['tilt_max']
      self.typefld = 'tilt'
    self.frame = ttk.Frame(parent)
    self.pl = ttk.Label(self.frame, text=name, style="MenloMd.TLabel")
    self.pmin = ttk.Label(self.frame, text=str(self.minv), style="MenloSm.TLabel")
    self.pmax = ttk.Label(self.frame, text=str(self.maxv), style="MenloSm.TLabel")
    self.pctr = (self.maxv - self.minv) / 2 + self.minv
    self.pv = ttk.Label(self.frame, text=str(self.pctr), style="MenloMd.TLabel")
    self.curvalue = ttk.DoubleVar(value=self.pctr)
    self.pscl = ttk.Scale(self.frame, orient='horizontal', from_=self.minv,
                          to=self.maxv, variable=self.curvalue,
                          length=scalewidth, command=self.publish)
        
    self.pl.grid(row=1, column=2)
    self.pmin.grid(row=2, column=1, sticky='e')
    self.pscl.grid(row=2, column=2)
    self.pmax.grid(row=2, column=3, sticky='w')
    self.pv.grid(row=3, column=2)

  def grid(self, **kwargs):
    self.frame.grid(**kwargs)
