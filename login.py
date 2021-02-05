from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import paho.mqtt.client as mqtt
import sys
import json
import time
from lib.Settings import Settings
from lib.Homie_MQTT import Homie_MQTT
import argparse
import logging
import logging.handlers
from threading import Lock, Thread
import os

# some globals
settings = None
hmqtt = None
mq_thr = None         # Thread for mqtt loops 
env_home = None       # env['HOME']
root = None           # Tk root
menu_fr = None
alarm_btn = None
voice_btn = None
laser_btn = None
login_btn = None
logoff_btn = None
panel_fr = None
title = None
subtitle = None
pnl_middle = None
message = None
vid_widget = None
turrets = None

laser_cmds = {'Square': 'square', 'Circle': 'circle', 'Diamond': 'diamond', 
  'Crosshairs':'crosshairs', 'Horizontal Sweep': 'hzig', 'Vertical Sweep': 'vzig',
   'Random': 'random', 'TB Tame': 'tame', 'TB Mean': 'mean'}

def main():
  global settings, hmqtt, log,  env_home, mq_thr
  global root,menu_fr,alarm_btn,voice_btn,laser_btn,login_btn,logoff_btn
  global menu_fr, panel_fr, title, subtitle, center_img, pnl_middle, message

  env_home = os.getenv('HOME')
  ap = argparse.ArgumentParser()
  ap.add_argument("-c", "--conf", required=True, type=str,
    help="path and name of the json configuration file")
  ap.add_argument("-s", "--syslog", action = 'store_true',
    default=False, help="use syslog")

  args = vars(ap.parse_args())
  
  # logging setup
  log = logging.getLogger('testbear')
  #applog.setLevel(args['log'])
  if args['syslog']:
    applog.setLevel(logging.DEBUG)
    handler = logging.handlers.SysLogHandler(address = '/dev/log')
    # formatter for syslog (no date/time or appname. Just  msg, lux, luxavg
    formatter = logging.Formatter('%(name)s-%(levelname)-5s: %(message)-30s')
    handler.setFormatter(formatter)
    applog.addHandler(handler)
  else:
    logging.basicConfig(level=logging.DEBUG,datefmt="%H:%M:%S",format='%(asctime)s %(levelname)-5s %(message)-40s')

  settings = Settings(args["conf"], 
                      log)
  settings.print()

  try:
    hmqtt = Homie_MQTT(settings, on_mqtt_msg)
  except:
    log.fail('failed mqtt setup')
    exit()
    
  root = Tk()
  menu_fr = ttk.Frame(root, width=200, height=580)
  menu_fr.pack(side=LEFT)
  alarm_btn = Button(menu_fr, text = "Alarm", font = "Menlo 14 bold",)
  voice_btn = Button(menu_fr, text = "Voice", font = "Menlo 14 bold")
  laser_btn = Button(menu_fr, text = "Lasers", font = "Menlo 14 bold")
  login_btn = Button(menu_fr, text = "Login", font = "Menlo 14 bold", 
      command = on_login)
  logoff_btn = Button(menu_fr, text = "Logoff", font = "Menlo 14 bold",
      command = on_logoff)
  
  panel_fr = ttk.Frame(root, width=700, height=580)
  panel_fr.pack(side=TOP)
  title = ttk.Label(panel_fr, text="Trumpy Bear", font="Menlo 34").pack()
  subtitle = ttk.Label(panel_fr, text="Please Login",font="Menlo 26").pack()
  print('type of subtitle:', type(subtitle))
  '''
  img1 = Image.open("images/IF-Garden.jpg")
  img1 = img1.resize((400, 300))
  center_img = ImageTk.PhotoImage(image=img1)
  pnl_middle = ttk.Label(panel_fr, image=center_img)
  pnl_middle.pack(side=TOP)
  print('type of pnl_middle:', type(pnl_middle))
  '''
  pnl_middle = home_panel()
  pnl_middle.pack(side=TOP)
  
  # bottom is a horizontal flow
  f1 = ttk.Frame(panel_fr).pack(side=BOTTOM)
  l1 = ttk.Label(f1, text="Messages: ", font="18").pack(side=LEFT)
  message = ttk.Label(f1,text=" ", font="18").pack(side=LEFT)
  login_btn.pack()
  
  # and now, the event loops and threads
  try:
    #root.after(1, mqtt_loop)
    #mq_thr = Thread(target=mqtt_loop,args=(None,))
    log.info('Started thread for mqtt loop')
  except:
    log.fail('mqtt thread fail')
    
  root.mainloop()
  while True:
    time.sleep(10)
  
def mqtt_loop():
  global hmqtt, log
  log.info('mqtt_loop-ing')
  hmqtt.loop_start()

def pict_for(name):
  global env_home
  fps = os.listdir(f"{env_home}/.trumpybear/{name}/face/")
  fps.sort()
  print('found:', fps[-1])
  return f'{env_home}/.trumpybear/{name}/face/{fps[-1]}'
  
def on_mqtt_msg(topic, payload):
  global log, settings, vid_widget, alarm_btn, voice_btn, laser_btn
  global login_btn, logoff_btn, turrets
  log.info(f'on_mqtt: {topic} {payload}')
  if topic == settings.hscn_sub:
    if payload == 'wake':
      wake_up()
    elif payload.startswith('{'):
      hsh = json.loads(payload)
      print(f"json parse: {hsh}")
      cmd =  hsh['cmd']
      if cmd == 'wake':
        wake_up()
      elif cmd == 'register':
        do_register()
      elif cmd == 'user':
        user = hsh['user']
        role = hsh['role']
        img_path = pict_for(user)
        log.info(f"{user} logged in")
        # change the front picture
        set_picture(img_path)
        # hide or show the correct buttons
        alarm_btn.pack()
        voice_btn.pack()
        laser_btn.pack()
        login_btn.pack_forget()
        logoff_btn.pack()
        dt = {'cmd': 'get_turrets'}
        hmqtt.client.publish(settings.hcmd_pub, json.dumps(dt))
      elif cmd == 'set_turrets':
        # TODO (re) build $turrets ary of hash
        turrets = hsh['turrets']
        log.info(turrets)
      elif cmd == 'logout':
        on_logout()
      elif cmd == 'tracking':
        #@tgt_msg.text = hsh['msg']
        #@tgt_img.path = '/home/pi/Projects/tmp/tracking.jpg'
        pass
      
  elif topic == settings.htrkv_sub:
    log.info(f"got #{topic} #{payload}")
    hsh = json.loads(payload)
    if hsh['uri'] != None:
      uri = hsh['uri']
      vid_widget.set_path(uri)
      vid_widget.play()
    elif hsh['uri'] == None:
      if vid_widget:
        vid_widget.stop()
        pass
      end        
    else:
      log.debug(f"ignore #{payload}")

  elif topic == settings.hdspm_sub:
    # display_mode command. 
    if payload == 'off':
      # trigger screen saver - hide our stuff
      monitor_sleep()
    elif payload == 'on':
      # turn screen saver off - show our goods.
      monitor_wake()

  elif topic == settings.hdspt_sub:
    # text command
    #@msg.text = msg.payload
    pass
  elif topic == settings.htur1_sub or topic == settings.htur2_sub:
    # 'OK' is a possible payload
    if msg.payload.startswith('{'):
      dt = JSON.parse(msg.payload)
      #debug "#{dt['bounds']}"
      log.info(f"{dt['bounds']}")
      #manual_panel dt['bounds']
      
def on_login():
  global hmqtt, settings
  global root,menu_fr,alarm_btn,voice_btn,laser_btn,login_btn,logoff_btn
  global panel_fr,title,subtitle,pnl_middle,message
  print("logging in")
  # turn on the lamp
  hmqtt.client.publish(settings.hscn_pub, "awake", False, 1)
  time.sleep(1)   # enough time to turn on the lamp?
  dt = {'cmd': 'login'}
  hmqtt.client.publish(settings.hcmd_pub, json.dumps(dt), False, 1)
  
# async response from trumpy.py will arrive and
# replace pnl_middle
def on_logoff():
  global root,menu_fr,alarm_btn,voice_btn,laser_btn,login_btn,logoff_btn
  global panel_fr, title ,subtitle, message
  print("logging off")
  # replace pnl_middle
  pnl_middle = home_panel()
  pnl_middle.pack(side=TOP)
  # hide or show the correct buttons
  alarm_btn.pack_forget()
  voice_btn.pack_forget()
  laser_btn.pack_forget()
  login_btn.pack()
  logoff_btn.pack_forget()


def set_picture(img_path):
  global panel_fr, center_img, pnl_middle
  img1 = Image.open(img_path)
  img1 = img1.resize((400, 300))
  center_img = ImageTk.PhotoImage(image=img1)
  pnl_middle['image'] = center_img

  
def home_panel():
  global panel_fr,center_img, pnl_middle, env_home
  img1 = Image.open(f"{env_home}/login/images/IF-Garden.jpg")
  img1 = img1.resize((400, 300))
  center_img = ImageTk.PhotoImage(image=img1)
  pnl_middle = Label(panel_fr, image=center_img)
  pnl_middle.pack(side=TOP)
  print(type(pnl_middle))
  return pnl_middle

def wake_up():
  # run Hubitat lighting/Muting automations 
  global log, settings, hmqtt
  log.info("Wake up runs")
  hmqtt.client.publish(settings.hscn_pub, "awake", false, 1)
  
def monitor_wake():
  global log, settings, hmqtt
  log.info("waking monitor")
  os.system('DISPLAY=:0; xset s reset')


def monitor_sleep():
  global log, settings, hmqtt
  log.info("sleeping monitor")
  os.system('DISPLAY=:0; xset s activate')


def keepalive():
  global log, settings, hmqtt
  dt = {'cmd': 'keepalive', 'minutes': 2}
  hmqtt.client.publish(settings.hcmd_pub, json.dumps(dt))

def do_register():
  global log, settings, hmqtt, subtitle
  # unsleep screen saver
  monitor_wake()
  # tell hubitat we are working.
  wake_up()
  # put Trumpybear in Register Mode
  dt = {'cmd': 'register'}
  hmqtt.client.publish(settings.hcmd_pub, json.dumps(dt))
  subtitle['text'] = "Registering"


if __name__ == '__main__':
  sys.exit(main())
