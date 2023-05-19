from tkinter import *
from tkinter import ttk
from tkinter import font
from PIL import Image, ImageTk
import paho.mqtt.client as mqtt
import sys
import json
import time
from lib.Settings import Settings
from lib.Homie_MQTT import Homie_MQTT
from lib.TurretSlider import TurretSlider
import argparse
import logging
import logging.handlers
import threading
from threading import Lock, Thread
import os
import sys
import vlc
#import pulsectl

# some globals
isOSX = False
settings = None
hmqtt = None
mq_thr = None         # Thread for mqtt 
env_home = None       # env['HOME']
mainwin = None        # First Toplevel of root.
content = None        # First frame, contains menu_fr and panel_fr (frames)
menu_fr = None
panel_fr = None
alarm_btn = None
voice_btn = None
laser_btn = None
login_btn = None
logoff_btn = None

mic_btn = None
mic_image = None
mic_muted = True
# Login/Logout Frame contains:
pnl_hdr = ""
status_hdr = ""
pnl_middle = None
msg_hdr = ""
center_img = None
vid_widget = None
vlc_instance = None   
turrets = None
# merging in Screen saver - HE Notify stuff
device = None
saver_running = False
devFnt = None
font1 = None
font2 = None
font3 = None
stroke_fill = 'white'
screen_width = None
screen_height = None
saver_cvs = None
lnY = []
screen_thread = None
saver_blank_thread = None
scroll_thread = None
textLines =[]
devLns = 2
firstLine = 0

laser_cmds = {'Square': 'square', 'Circle': 'circle', 'Diamond': 'diamond', 
  'Crosshairs':'crosshairs', 'Horizontal Sweep': 'hzig', 'Vertical Sweep': 'vzig',
   'Random': 'random', 'TB Tame': 'tame', 'TB Mean': 'mean'}
   
def do_quit():
  global mainwin
  mainwin.destroy()
  exit()

def main():
  global settings, hmqtt, log,  env_home, mq_thr
  global mainwin,menu_fr,alarm_btn,voice_btn,laser_btn,login_btn,logoff_btn
  global mic_btn, mic_image, mic_muted,ranger_btn
  global menu_fr, panel_fr, center_img, pnl_middle, message
  global pnl_hdr, status_hdr, msg_hdr, content
  global device,saver_cvs,stroke_fill, screen_height, screen_width
  global font1,font2,font3,devFnt, mic_imgs
  env_home = os.getenv('HOME')
  if sys.platform == 'darwin':
    isOSX = True
    print('Darwin not really supported')
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
    log.setLevel(logging.DEBUG)
    handler = logging.handlers.SysLogHandler(address = '/dev/log')
    # formatter for syslog (no date/time or appname. Just  msg, lux, luxavg
    formatter = logging.Formatter('%(name)s-%(levelname)-5s: %(message)-30s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
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
    
  #pulse = pulsectl.Pulse('tblogin')
    
  tkroot = Tk()
  mainwin = Toplevel(tkroot)
  # new:
  #root.wait_visibility(saver_cvs)
  mainwin.wm_attributes("-topmost", True)
  #mainwin.attributes('-fullscreen', True)    # required, else ghost window on top
  # 
  #mainwin.geometry('900x580')
  mainwin.bind("<Escape>", lambda event:tkroot.destroy())

  mainwin.protocol("WM_DELETE_WINDOW", do_quit)
  st = ttk.Style()
  st.theme_use('alt') # better than 'default', IMO
  st.configure("Menlo.TButton", font = ('Menlo', 16, 'bold'), 
    height=20, width=10)
  
  st = ttk.Style()
  st.configure("Menlo.TRadiobutton", font = ('Menlo', 12))
  
  st = ttk.Style()
  st.configure("MenloSm.TLabel", font = ('Menlo', 14))
  st = ttk.Style()
  st.configure("MenloMd.TLabel", font = ('Menlo', 16))
  st = ttk.Style()
  st.configure("MenloMd.TLabel", font = ('Menlo', 18))
  
  st = ttk.Style()
  st.configure("Menlo.TCheckbutton", font = ('Menlo', 16), 
    height=10, width=10)
    
  st = ttk.Style()
  st.configure("Menlo.TCombobox", font = ('Menlo', 16), 
    height=16, width=10)
  
  content = ttk.Frame(mainwin)
  menu_fr = ttk.Frame(content, width=100, height=580, borderwidth=5)
  menu_fr.pack(side=LEFT, expand=True)
  
  st_p = 4
  alarm_btn = ttk.Button(menu_fr, text ="Alarm", style='Menlo.TButton', 
      command=alarm_panel)
  alarm_btn['state'] = 'disabled'
  alarm_btn.grid(row=st_p + 2)
  voice_btn = ttk.Button(menu_fr, text = "GLaDOS", style='Menlo.TButton',
      command=mycroft_panel)
  voice_btn.grid(row=st_p + 3)
  voice_btn['state'] = 'disabled'
  laser_btn = ttk.Button(menu_fr, text = "Lasers", style='Menlo.TButton',
      command=laser_panel)
  laser_btn.grid(row=st_p + 4)
  laser_btn['state'] = 'disabled'
  ranger_btn = ttk.Button(menu_fr, text = "Ranger", style='Menlo.TButton',
      command=ranger_panel)
  ranger_btn.grid(row=st_p + 5)
  ranger_btn['state'] = 'disabled'
  #ranger_btn['state'] = '!disabled'
  login_btn = ttk.Button(menu_fr, text = "Login", style='Menlo.TButton', 
      command = on_login)
  login_btn.grid(row=st_p + 6)
  logoff_btn = ttk.Button(menu_fr, text = "Logoff", style='Menlo.TButton',
      command = on_logoff)
  logoff_btn.grid(row=st_p + 7)

  # Sigh. Images and Tk 
  mic_imgs = []
  imgT = Image.open(f"{env_home}/login/images/microphone-red.png")
  imgT = imgT.resize((40, 70))
  imgPi = ImageTk.PhotoImage(image=imgT)
  mic_imgs.append(imgPi)

  imgT = Image.open(f"{env_home}/login/images/microphone-green.png")
  imgT = imgT.resize((40, 70))
  imgPi = ImageTk.PhotoImage(image=imgT)
  mic_imgs.append(imgPi)
  if mic_muted:
    # red icon
    micst = 0
  else:
    # green icon
    micst = 1
  #mic_btn = ttk.Label(menu_fr, image = mic_imgs[micst], )
  mic_btn = ttk.Button(menu_fr, image = mic_imgs[micst], command = on_mute)
  mic_btn.grid(row=st_p + 8, rowspan = 2)
  
  start_panel(True)

  # fill in the right side panel. 
  content.pack()
  
  # ----- Now the screen saver panel ---
  device= Toplevel(tkroot)
  
  # Tkinter Window Configurations
  #device.wait_visibility(saver_cvs)
  device.wm_attributes('-alpha',1)
  device.wm_attributes("-topmost", False)
  #device.overrideredirect(1)
  device.attributes('-fullscreen', True)
  device.attributes("-zoomed", True)
  #device.attributes("-toolwindow", 1)
  screen_width = device.winfo_screenwidth()
  screen_height = device.winfo_screenheight()
  # create canvas 
  saver_cvs = Canvas(device, background='black', borderwidth = 0)
  saver_cvs.create_rectangle(0, 0, screen_width, screen_height, fill = 'black')
  saver_cvs.pack(expand="yes",fill="both")
 
  
  font1 = font.Font(family=settings.font1, size=settings.font1sz[0])
  font2 = font.Font(family=settings.font2, size=settings.font2sz[0])
  font3 = font.Font(family=settings.font3, size=settings.font3sz[0])
  fnt = settings.deflt_font
  set_font(fnt)
  stroke_fill = settings.stroke_fill
  for seq in ['<Any-KeyPress>', '<Any-Button> ', '<Any-Motion>']:
    device.bind_all(seq, saver_closing)

  # arrange toplevel windows
  saver_running = False
  device.withdraw()
  mainwin.state('normal')
  log.info(f'starting mainloop fg: {mainwin.state()}, bg: {device.state()}')
  
  # set screensaver timer
  screen_timer_reset()
  
  # NOTE: mqtt messages seem to arrive just fine. Even though we
  # don't seem to accomodate them
  log.info('starting mqtt loop')
  mqtt_loop()
  delay_thread = threading.Timer(1, delayed_setup)
  delay_thread.start()
  mainwin.mainloop()
  
  while True:
    time.sleep(10)
  
def mqtt_loop():
  global hmqtt, log
  log.info('mqtt_loop-ing')
  hmqtt.client.loop_start()

def delayed_setup():
  global hmqtt, log
  # cmd the bridge to mute the microphone (and speaker?)
  # TODO WHY IS hspc_pub A TUPLE?
  log.info('force microphone and speaker off')
  hmqtt.client.publish(settings.hspc_pub[0], "off")
  
def screen_timer_fired():
  # when this happens we need to bring the
  # screen saver window to the top and
  # hide the main window/menus
  global saver_running,device,mainwin,log,screen_width,screen_height
  log.info(f'screen_timer_fired()')
  mainwin.withdraw()
  device.state('normal')
  device.lift(mainwin)
  mainwin.lower()
  saver_running = True
  log.info(f'device: {device.state()} mainwin: {mainwin.state()}')
 
# user touched/moused/keyed screen saver. Send to back
# bring main window to top. Also set a new screen timer
def saver_closing(event):
  global saver_cvs, device, saver_running, mainwin
  if saver_running and device.state() == 'normal':
    saver_running = False
    log.info(f'saver_closing()')
    mainwin.lift()
    device.lower()
    device.withdraw()
    mainwin.state('normal')
    screen_timer_reset()
    
  
def screen_timer_reset():
  global screen_thread
  if screen_thread:
    screen_thread.cancel()
  screen_thread = threading.Timer(120, screen_timer_fired)
  screen_thread.start()
  
def saver_timer_fired():
  global saver_cvs, saver_blank_thread, scroll_thread
  saver_blank_thread = None
  log.info('saver TMO fired')
  saver_cvs.delete('all')
  if scroll_thread:
    scroll_thread.cancel()
    scroll_thread = None

  
def saver_blank(secs):
  global saver_blank_thread
  if saver_blank_thread:
    # reset unfired timer by canceling.
    saver_blank_thread.cancel()

  saver_blank_thread = threading.Timer(secs, saver_timer_fired)
  saver_blank_thread.start()


def pict_for(name):
  global env_home
  fps = os.listdir(f"{env_home}/.trumpybear/{name}/face/")
  fps.sort()
  print('found:', fps[-1])
  return f'{env_home}/.trumpybear/{name}/face/{fps[-1]}'
  
def on_mqtt_msg(topic, payload):
  global log, settings, vid_widget, alarm_btn, voice_btn, laser_btn
  global login_btn, logoff_btn, turrets, mic_btn, mic_imgs, ranger_btn
  global pnl_hdr, status_hdr, msg_hdr, vlc_instance
  global saver_running, textLines, devLn, scroll_thread, devLns
  
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
        status_hdr['text'] = f'{user} has logged in'
        # change the front picture
        set_picture(img_path)
        # hide or show the correct buttons
        alarm_btn['state'] = '!disabled'
        voice_btn['state'] = '!disabled'
        laser_btn['state'] = '!disabled'
        ranger_btn['state'] = '!disabled'
        login_btn['state'] = 'disabled'
        logoff_btn['state'] = '!disabled'
        mic_btn['state'] = '!disabled'
        dt = {'cmd': 'get_turrets'}
        hmqtt.client.publish(settings.hcmd_pub, json.dumps(dt))
      elif cmd == 'mic_on':
        mic_btn.config(image=mic_imgs[1])
        #mic_btn.image = mic_imgs[1]
      elif cmd == 'mic_off':
        mic_btn.config(image=mic_imgs[0])
        #mic_btn.image = mic_imgs[0]
      elif cmd == 'set_turrets':
        turrets = hsh['turrets']
        log.info(turrets)
      elif cmd == 'logout':
        on_logoff()
      elif cmd == 'tracking':
        #@tgt_msg.text = hsh['msg']
        msg_hdr[text]=hsh['msg']
        pass
      
  elif topic == settings.htrkv_sub:
    log.info(f"got {topic} => {payload}")
    hsh = json.loads(payload)
    if hsh['uri'] != None:
      uri = hsh['uri']
      media = vlc_instance.media_new(uri)
      vid_widget.set_media(media)
      vid_widget.play()
    elif hsh['uri'] == None:
      if vid_widget:
        vid_widget.stop()
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
    msg_hdr['text'] = payload
    # msg_hdr.config(text=payload)

  elif topic == settings.htur1_sub or topic == settings.htur2_sub:
    # 'OK' is a possible payload, we ignore it.
    if payload.startswith('{'):
      dt = JSON.parse(msg.payload)
      #debug "#{dt['bounds']}"
      log.info(f"{dt['bounds']}")
      #manual_panel dt['bounds']
  #
  # Screen Saver text and commands
  #
  elif topic == settings.notecmd_sub:
    args = json.loads(payload)
    cmd = args.get('cmd', None)
    setargs = args.get('settings', None);
    textargs = args.get('text')
    if cmd: 
      if cmd == 'on':
        screenCmdOn(args)
      elif cmd == 'off':
        screenCmdOff(args)
      elif cmd == 'update':
        log.info('ignoring update command')
      else:
        log.info("invalid command")
    elif setargs:
      screenParseSettings(setargs)
  elif topic == settings.notetext_sub:
    if (saver_running == True):
      saver_cvs.delete('all')
      words = payload.split()
      nln = len(lnY)       # number of display lines 
      #log.info(f'nln: {nln} nwd: {words}')
      # setup blanking timer for screensaver
      saver_blank(5*60)
      textLines = []
      if scroll_thread:
        scroll_thread.cancel()
      needscroll = layoutLines(textLines, devLns, len(words), words)
      if needscroll:
        # set 1 sec timer
        scroll_thread =  threading.Timer(1, scroll_timer_fired)
        scroll_thread.start()
        #log.info(f'setup scroll for {len(textLines)} lines')
        displayLines(0, devLns, textLines)
      else:
        displayLines(0, devLns, textLines)
    # Display msg in bottom panel ?
          
def on_login():
  global hmqtt, settings
  global menu_fr,alarm_btn,voice_btn,laser_btn,login_btn,logoff_btn
  global panel_fr,title,subtitle,pnl_middle,message
  print("logging in")
  # turn on the lamp
  hmqtt.client.publish(settings.hscn_pub, "awake", False, 1)
  time.sleep(1)   # enough time to turn on the lamp?
  dt = {'cmd': 'login'}
  hmqtt.client.publish(settings.hcmd_pub, json.dumps(dt), False, 1)
  screen_timer_reset()
  
# async response from trumpy.py will arrive and
# replace pnl_middle
def on_logoff():
  global menu_fr,alarm_btn,voice_btn,laser_btn,login_btn,logoff_btn,ranger_btn
  global panel_fr, status_hdr, mic_muted, mic_btn,settings,hmqtt
  print("logging off")
  lamp_off()
  start_panel()
  status_hdr['text'] = 'Please Login'
  # hide or show the correct buttons
  alarm_btn['state'] = 'disabled'
  voice_btn['state'] = 'disabled'
  laser_btn['state'] = 'disabled'
  ranger_btn['state'] = 'disabled'
  login_btn['state'] = '!disabled'
  logoff_btn['state'] = 'disabled'
  mic_btn['state'] = 'disabled'
  # disable da mic icon - turn off - via the bridge
  topic = settings.hspc_pub[0]
  hmqtt.client.publish(topic, "off")
  mic_muted = True
  

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
  return pnl_middle

def wake_up():
  # run Hubitat lighting/Muting automations 
  global log, settings, hmqtt
  log.info("Wake up runs")
  hmqtt.client.publish(settings.hscn_pub, "awake", false, 1)
  
# Trumpy Bear needs to show, Screen saver hides.
def monitor_wake():
  global log, settings, hmqtt, saver_running
  
  log.info("waking monitor")
  saver_closing();
  #saver_running = False
  #os.system('DISPLAY=:0; xset s reset')
  
# Trumpy Bear sleeps, Screen Saver awakens
def monitor_sleep():
  global log, settings, hmqtt, saver_running
  log.info("sleeping monitor")
  screen_timer_fired()
  #saver_running = True
  #os.system('DISPLAY=:0; xset s activate')


def keepalive():
  global log, settings, hmqtt
  dt = {'cmd': 'keepalive', 'minutes': 2}
  hmqtt.client.publish(settings.hcmd_pub, json.dumps(dt))

def do_register():
  global log, settings, hmqtt, status_hdr
  # unsleep screen saver
  monitor_wake()
  # tell hubitat we are working.
  wake_up()
  # put Trumpybear in Register Mode
  dt = {'cmd': 'register'}
  hmqtt.client.publish(settings.hcmd_pub, json.dumps(dt))
  status_hdr['text'] = "Registering"
  
def start_panel(first=False):
  global panel_fr,center_img, pnl_middle,  content
  global pnl_hdr, status_hdr, msg_hdr
  if not first:
    panel_fr.grid_forget()
    panel_fr.destroy()
    screen_timer_reset()

  panel_fr = ttk.Frame(content, width=700, height=580, borderwidth=5)
  panel_fr.pack(side=RIGHT, expand=True)
  
  pnl_hdr = ttk.Label(panel_fr, text="Trumpy Bear", font="Menlo 34")
  pnl_hdr.grid(column=2, columnspan=15, row=1)
  status_hdr = ttk.Label(panel_fr, text="Please Login",font="Menlo 26")
  status_hdr.grid(column=4, columnspan=15, row=2)

  pnl_middle = home_panel()
  pnl_middle.grid(row=3, column=1, padx=20, pady=20, rowspan=14, columnspan=16)
  
  # bottom is a horizontal flow
  f1 = ttk.Frame(panel_fr)
  f1.grid(rows=5, columns=8,sticky=S)
  l1 = ttk.Label(f1, text="Messages: ", style="MenloMd.TLabel")
  l1.grid(column=0, row=0, sticky=S)
  msg_hdr = ttk.Label(f1,text=" ", style="MenloMd.TLabel")
  msg_hdr.grid(row=0, column=1, columnspan=7, sticky=S)

def alarm_panel():
  # build and grid new frame
  global panel_fr, content
  screen_timer_reset()
  panel_fr.grid_forget()
  panel_fr.destroy()
  panel_fr = ttk.Frame(content, width=700, height=580, borderwidth=5)
  panel_fr.pack(side=RIGHT, expand=True)
  lbl = ttk.Label(panel_fr, style="MenloMd.TLabel",
      text="You can try turning off the Alarm. Sometimes it will stop.")
  lbl.grid(row =1, column=0, columnspan=12)
  btn = ttk.Button(panel_fr, text="Turn Off", style='Menlo.TButton')
  btn.grid(row=2, column=2)
  
def start_mycroft():
  global hmqtt, settings
  dt = {'cmd': 'mycroft'}
  hmqtt.client.publish(settings.hcmd_pub,json.dumps(dt))

# glados control runs on the bridge.py process: homie.../speech/control/set
# TODO why is their a tuple?
def start_glados():
  global hmqtt, settings
  hmqtt.client.publish(settings.hspc_pub[0],'chat')
  
def stop_glados():
  # good luck stopping her
  # talk to the bridge, not trumpy bear
# TODO why is that a tuple?
  global hmqtt, settings
  hmqtt.client.publish(settings.hspc_pub[0],'stop')

def quit_glados():
  # I can't quit her
  # talk to the bridge, not trumpy bear
# TODO why is that a tuple?
  global hmqtt, settings
  hmqtt.client.publish(settings.hspc_pub[0],'quit')

def mycroft_panel():
  global panel_fr, content
  screen_timer_reset()
  panel_fr.grid_forget()
  panel_fr.destroy()
  panel_fr = ttk.Frame(content, width=700, height=580, borderwidth=5)
  panel_fr.pack(side=RIGHT, expand=True)
  lbl = ttk.Label(panel_fr, style="MenloMd.TLabel",
      text="You can try talking to GLaDos after she acknowledges you.")
  lbl.grid(row =1, column=1, columnspan=12)
  lbl2 = ttk.Label(panel_fr, style="MenloMd.TLabel",
      text="Talk when the microphone icon is Green")
  lbl2.grid(row =2, column=1, columnspan=12)
  btn = ttk.Button(panel_fr, text="GLaDos", style='Menlo.TButton', 
      command=start_glados)
  btn.grid(row=3, column=1)
  stop_btn = ttk.Button(panel_fr, text="Stop", style='Menlo.TButton', 
      command=stop_glados)
  stop_btn.grid(row=3, column=2)
  quit_btn = ttk.Button(panel_fr, text="Quit", style='Menlo.TButton', 
      command=quit_glados)
  quit_btn.grid(row=3, column=3)
  start_glados()

def lamp_off():
  global hmqtt, settings
  hmqtt.client.publish(settings.hscn_pub, "closing", False, 1)
  
def lasers_off():
  global hmqtt, settings, turrets
  for tur in turrets:
    pdt = {'power':  0}
    hmqtt.client.publish(f"{tur['topic']}/set", json.dumps(pdt), False, 1)
   
def on_mute():
  # Button pushed - change the image and global var
  # TODO: why is hspc_pub a tuple? 
  global settings, hmqtt,mic_muted
  topic = settings.hspc_pub[0]
  if mic_muted:
    # if muted  (mic off) then unmute (which is mute off)
    print(f"SENDING mute off to {topic}")
    hmqtt.client.publish(topic, "off")
    mic_muted = False
  else:
    print(f"SENDING mute on to {topic}")
    hmqtt.client.publish(topic, "on")
    mic_muted = True

  
# hackish but why bother to do better? 
def do_exec():
  global turrents, hmqtt, laser_cmds, lb, lb3, lb4, lb5, lb6, lb7, cbox1, cbox2
  dt = {}
  cmd = laser_cmds[lb.get()]
  dt['exec'] = cmd
  dt['count'] = int(lb3.get())
  dt['time'] = float(lb4.get())
  if cmd == 'hzig' or cmd == 'vzig':
    dt['lines'] = int(lb5.get())
  elif cmd == 'diamond' or cmd == 'crosshairs' or cmd == 'random':
    dt['length'] = int(lb6.get())
  elif cmd == 'circle':
    dt['radius'] = int(lb7.get())
    
  payload = json.dumps(dt)
  if cbox1.get() is True:
      hmqtt.client.publish(f"{turrets[0]['topic']}/set", payload, False, 1)
      #print(f"{turrets[0]['topic']} <== {payload}")
  if cbox2.get() is True:
      hmqtt.client.publish(f"{turrets[1]['topic']}/set", payload, False, 1)
      #print(f"{turrets[1]['topic']} <== {payload}")
  keepalive()
  
# provides the builtin laser 'exec' routines
# also buttons to bring up manual, calibrate and track panels.
def laser_panel():
  global panel_fr, content, laser_cmds, turrets
  global lb, lb3, lb4, lb5, lb6, lb7, cbox1, cbox2
  lasers_off()
  screen_timer_reset()
  panel_fr.grid_forget()
  panel_fr.destroy()
  panel_fr = ttk.Frame(content, width=700, height=580, borderwidth=5)
  panel_fr.pack(side=RIGHT, expand=True)
  
  lbl1 = ttk.Label(panel_fr,text="Exercise The Lasers", style="MenloLg.TLabel")
  lbl1.grid(row=1, column=1, columnspan=2)
  
  lbl2 = ttk.Label(panel_fr, text='Routine:', style="MenloMd.TLabel")
  lbl2.grid(row=2,column=1)
  t = []
  for k in laser_cmds.keys():
    t.append(k)
  lb = ttk.Combobox(panel_fr,values = t, style= 'Menlo.TCombobox')
  lb.state(["readonly"])
  lb.set("Horizontal Sweep")
  lb.grid(row=3, column=1, sticky=W)
  

  cbox1 = BooleanVar(value=False)
  cbx1 = ttk.Checkbutton(panel_fr, text=turrets[0]['name'], style='Menlo.TCheckbutton',
			variable=cbox1)
  cbx1.grid(row=4, column=1)
  
  cbox2 = BooleanVar(value=False)
  cbx2 = ttk.Checkbutton(panel_fr, text=turrets[1]['name'], style='Menlo.TCheckbutton',
			variable=cbox2)
  cbx2.grid(row=5, column=1)
  
    
  exec_btn = ttk.Button(panel_fr, text="Execute", style='Menlo.TButton',
      command=do_exec)
  exec_btn.grid(row=7, column=1)
  
  # column 3 empty
  # column 4: 
  lbl3 = ttk.Label(panel_fr, text="Time allowed:", style="MenloMd.TLabel")
  lb3 = ttk.Combobox(panel_fr, values=('  2','  4','  6',' 10'), style= 'Menlo.TCombobox')
  lbl3.grid(row=2, column=4)
  lb3.grid(row=3,column=4)
  lb3.set('2')
  
  lbl4 = ttk.Label(panel_fr, text="Count:", style="MenloMd.TLabel")
  lb4 = ttk.Combobox(panel_fr, values=('1','2','3','4','6','8'), style= 'Menlo.TCombobox')
  lbl4.grid(row=4, column=4)
  lb4.grid(row=5,column=4)
  lb4.set('2')
  
  lbl5 = ttk.Label(panel_fr, text="Lines (sweeps)", style="MenloMd.TLabel")
  lb5 = ttk.Combobox(panel_fr, values=('4', '5', '7', '9'), style= 'Menlo.TCombobox')
  lbl5.grid(row=6, column=4)
  lb5.grid(row=7,column=4)
  lb5.set('5')
  
  lbl6 = ttk.Label(panel_fr, text="Length (diamonds)", style="MenloMd.TLabel")
  lb6 = ttk.Combobox(panel_fr, values=('10', '15', '20', '30', '50'), style= 'Menlo.TCombobox')
  lbl6.grid(row=8, column=4)
  lb6.grid(row=9,column=4)
  lb6.set('30')

  lbl7 = ttk.Label(panel_fr, text="Radius (circles)", style="MenloMd.TLabel")
  lb7 = ttk.Combobox(panel_fr, values=('10', '15', '20', '30', '50'), style= 'Menlo.TCombobox')
  lbl7.grid(row=10, column=4)
  lb7.grid(row=11,column=4)
  lb7.set('20')
  
  btn_row = 9
  lamp_btn = ttk.Button(panel_fr, text="Lamp Off", style='Menlo.TButton',
      command=lamp_off)
  lamp_btn.grid(column=1, row=btn_row, sticky=(S,W))
  man_btn = ttk.Button(panel_fr, text="Manual", style='Menlo.TButton',
      command=manual_panel)
  man_btn.grid(column=1, row=btn_row+1, sticky=(S,W))
  cal_btn = ttk.Button(panel_fr, text="Calibrate", style='Menlo.TButton',
      command=calibrate_panel)
  cal_btn.grid(column=1, row=btn_row+2, sticky=(S,W))
  trk_btn = ttk.Button(panel_fr, text="Tracking", style='Menlo.TButton',
      command=tracking_panel)
  trk_btn.grid(column=1, row=btn_row+3, sticky=(S,W))
 
# compared to Shoes+Ruby, this is really ugly.
def manual_panel():
  global hmqtt, settings, panel_fr, content, laser_cmds, turrets
  global lb, lb3, lb4, lb5, lb6, lb7, cbox1, cbox2
  lasers_off() 
  screen_timer_reset()
  panel_fr.grid_forget()
  panel_fr.destroy()
  panel_fr = ttk.Frame(content, width=700, height=580, borderwidth=5)
  panel_fr.pack(side=RIGHT, expand=True)
  
  def set_pwr(idx):
    global hmqtt, settings, turrets
    if idx > 0:
      idx=1
    tur = turrets[idx]
    pwr = tur['power'].get()
    #print(tur['name'], pwr)
    if pwr != 0:
      npwr = 100
    else:
      npwr = 0
    pdt = {'power':  npwr}
    hmqtt.client.publish(f"{tur['topic']}/set", json.dumps(pdt), False, 1)
  '''
  def set_pan(idx, lbl):
    global hmqtt, settings, turrets
    if idx > 0:
      idx=1
    tur = turrets[idx]
    nm = tur['name']
    val = round(tur['pan_cur'].get(), 1)
    #print(nm, val)
    lbl['text']=str(val)
    pdt = {'pan':  val}
    hmqtt.client.publish(f"{tur['topic']}/set", json.dumps(pdt), False, 1)
    return 0
    
  def set_tilt(idx, lbl):
    global hmqtt, settings, turrets
    if idx > 0:
      idx=1
    tur = turrets[idx]
    nm = tur['name']
    val = round(tur['tilt_cur'].get(), 1)
    #print(nm, val)
    lbl['text']=str(val)
    pdt = {'tilt':  val}
    hmqtt.client.publish(f"{tur['topic']}/set", json.dumps(pdt), False, 1)
    return 0
  
  # another helper. For Slider (aka Scale)
  def mySlider(fr, inrow, col, name, scalewidth, minvalue, maxvalue, curvalue, proc):
    pl = ttk.Label(panel_fr, text=name, style="MenloMd.TLabel")
    pmin = ttk.Label(panel_fr, text=str(minvalue), style="MenloSm.TLabel")
    pmax = ttk.Label(panel_fr, text=str(maxvalue), style="MenloSm.TLabel")
    pctr = (maxvalue-minvalue) / 2 + minvalue
    pv = ttk.Label(panel_fr, text=str(pctr), style="MenloMd.TLabel")
    curvalue = DoubleVar(value=pctr)
    pscl = ttk.Scale(panel_fr, orient='horizontal', from_=minvalue,
        to=maxvalue, variable=curvalue, length=scalewidth,
        command=lambda t=tur,s=side,p=pv: proc(s, p) )
    pl.grid(row=inrow, column=col+1)
    pmin.grid(row=inrow+1, column=col+0, sticky='e')
    pscl.grid(row=inrow+1, column=col+1)
    pmax.grid(row=inrow+1, column=col+2, sticky='w')
    pv.grid(row=inrow+2, column=col+1)
  '''
  side = 0
  pwr_widgets = {}
  for tur in turrets:
    # a frame for the turret name and radio buttons
    rad_fr = ttk.Frame(panel_fr)
    rad_fr.grid(row=1,column=side+1)
    
    lbl = ttk.Label(rad_fr, text=tur['name'], width=12, style="MenloMd.TLabel")
    lbl.grid(row=1, column=2)
    plbl = ttk.Label(rad_fr, text="Power", width=5, style="MenloMd.TLabel")
    plbl.grid(row=2, column=1, sticky='e')
    rd_fr = ttk.Frame(rad_fr)
    tur['power'] = IntVar(value=0)
    pb1 = ttk.Radiobutton(rd_fr, text="On", variable=tur['power'], value=100, 
        style = "Menlo.TRadiobutton",
        command=lambda t=tur, s=side: set_pwr(s))
    pb0 = ttk.Radiobutton(rd_fr, text="Off", variable=tur['power'], value=0, 
        style = "Menlo.TRadiobutton",
        command=lambda t=tur,s=side: set_pwr(s))
    pb1.grid(row=1, column=1, sticky='e')
    pb0.grid(row=1, column=2, sticky='w')
    rd_fr.grid(row=2, column=2)
    s1 = ttk.Separator(panel_fr, orient=HORIZONTAL)
    s1.grid(row=2, column=1, columnspan=3, sticky='ew')
    
    pan = TurretSlider(panel_fr, "Pan", 200, tur, hmqtt)
    #pan.frame.grid(row=3,column=1+side)
    pan.grid(row=3,column=1+side)
    
    s2 = ttk.Separator(panel_fr, orient=HORIZONTAL)
    s2.grid(row=4, column=1, columnspan=3, sticky='ew')
    
    tilt = TurretSlider(panel_fr, "Tilt", 200, tur, hmqtt)
    #tilt.frame.grid(row=5,column=1+side)
    tilt.grid(row=5,column=1+side)
    side += 1


def ranger_panel():
  global hmqtt, settings, panel_fr, content, center_img, pnl_middle 
  global msg_hdr
  panel_fr.grid_forget()
  panel_fr.destroy()
  panel_fr = ttk.Frame(content, width=700, height=580, borderwidth=5)
  panel_fr.pack(side=RIGHT, expand=True)
  
  lbl1 = ttk.Label(panel_fr, text="Ranger Calibration", 
      style="MenloMd.TLabel")
  lbl1.grid(row=1,column=1)
  lbl2 = ttk.Label(panel_fr, text="Meters from Camera", style="MenloMd.TLabel")
  lbl2.grid(row=2,column=1)
  cb1 = ttk.Combobox(panel_fr, values=('1', '2', '3', '4'), style= 'Menlo.TCombobox')
  cb1.set('1')
  cb1.grid(row=2, column=2)
  lbl3 = ttk.Label(panel_fr, text="Delay Time (sec)", style="MenloMd.TLabel")
  lbl3.grid(row=3, column=1)
  cb2 = ttk.Combobox(panel_fr, values=('1', '2', '3'), style= 'Menlo.TCombobox')
  cb2.set('1')
  cb2.grid(row=3, column=2)
  
  # bottom is a horizontal flow
  f1 = ttk.Frame(panel_fr)
  f1.grid(rows=5, columns=8,sticky=S)
  l1 = ttk.Label(f1, text="Messages: ", style="MenloMd.TLabel")
  l1.grid(column=1, row=1, sticky=S)
  msg_hdr = ttk.Label(f1, text="Here", style="MenloMd.TLabel")
  msg_hdr.grid(row=2, column=1, columnspan=7, sticky=S)
 
  
  def do_calib():
    dt = {'cmd': 'ranger_test'}
    dt['delay'] = int(cb2.get())
    dt['distance'] = int(cb1.get())
    hmqtt.client.publish(settings.hcmd_pub,json.dumps(dt))
      
  btn = ttk.Button(panel_fr, text="Begin", style="Menlo.TButton", 
    command=do_calib)
  btn.grid(row=5, column=2)  
  
  
def calibrate_panel():
  global hmqtt, settings, panel_fr, content, center_img, pnl_middle
  lasers_off() 
  screen_timer_reset()
  panel_fr.grid_forget()
  panel_fr.destroy()
  panel_fr = ttk.Frame(content, width=700, height=580, borderwidth=5)
  panel_fr.pack(side=RIGHT, expand=True)
  
  lbl1 = ttk.Label(panel_fr, text="Calibration writes a video file!\nCamera must be trumpybear owned!", 
      style="MenloMd.TLabel")
  lbl1.grid(row=1,column=1)
  lbl2 = ttk.Label(panel_fr, text="Meters from Camera", style="MenloMd.TLabel")
  lbl2.grid(row=2,column=1)
  cb1 = ttk.Combobox(panel_fr, values=('1', '2', '3', '4'), style= 'Menlo.TCombobox')
  cb1.set('1')
  cb1.grid(row=2, column=2)
  lbl3 = ttk.Label(panel_fr, text="Sweep Time (sec)", style="MenloMd.TLabel")
  lbl3.grid(row=3, column=1)
  cb2 = ttk.Combobox(panel_fr, values=('5', '10', '15', '20'), style= 'Menlo.TCombobox')
  cb2.set('10')
  cb2.grid(row=3, column=2)
  def do_calib():
    dt = {'cmd': 'calib'}
    dt['time'] = int(cb2.get())
    dt['distance'] = int(cb1.get())
    hmqtt.client.publish(settings.hcmd_pub,json.dumps(dt))

  btn = ttk.Button(panel_fr, text="Begin", style="Menlo.TButton", 
    command=do_calib)
  btn.grid(row=5, column=2)
 
def tracking_panel():
  global hmqtt, settings, panel_fr, content, laser_cmds, turrets
  global msg_hdr, vid_widget, vlc_instance, log
  screen_timer_reset()
  panel_fr.grid_forget()
  panel_fr.destroy()
  panel_fr = ttk.Frame(content, width=700, height=580, borderwidth=5)
  panel_fr.pack(side=RIGHT, expand=True)

  vlc_instance = vlc.Instance()
  vid_widget = vlc_instance.media_player_new()
  # need a frame for the video so we can get the vlc handle for a player
  vid_fr = ttk.Frame(panel_fr, width=400, height=300)
  vid_fr.grid(row=3, column=1, padx=20, pady=20, rowspan=14, columnspan=16)
  h = vid_fr.winfo_id()
  vid_widget.set_xwindow(h)  
  
  # bottom is a horizontal flow
  f1 = ttk.Frame(panel_fr)
  f1.grid(rows=5, columns=8,sticky=S)
  l1 = ttk.Label(f1, text="Messages: ", style="MenloMd.TLabel")
  l1.grid(column=0, row=0, sticky=S)
  msg_hdr = ttk.Label(f1,text=" ", style="MenloMd.TLabel")
  msg_hdr.grid(row=0, column=1, columnspan=7, sticky=S)
  '''
  def vid_test():
    media = vlc_instance.media_new("images/fma.mp4")
    vid_widget.set_media(media)
    vid_widget.play()
    
  test_btn = ttk.Button(f1, text="Test", style="MenloButton.TButton",
      command=vid_test)
  test_btn.grid(row=1, column=0)
  '''
  def send_trk():
    dt = {'cmd': 'track', 'debug': False, 'test': True}
    hmqtt.client.publish(settings.hcmd_pub, json.dumps(dt))
    log.info(f'sending {dt}')
            
  btn = ttk.Button(f1, text="Track Me", style="MenloButton.TButton",
      command=send_trk)
  btn.grid(row = 1, column = 1)
  
  
#
# ------------------------Screensaver/notify -------
# TODO: clean up all the globals. Make a class or two or three
# really ugly with the scrooling and globals. Really.
# compute some settings based on font size and screen size

def screenCmdOn():
  pass
  
def screenCmdOff():
  global saver_cvs
  saver_cvs.delete('all')
  log.info('cmdOff')

def screenParseSettings(dt):
  global devFnt, font1, font2, font3
  print(f'parseSettings: {dt}')
  if dt['font']:
    set_font(dt['font'])
    

def set_font(fnt):
  global log, devFnt, devLnH, settings, saver_cvs
  global screen_height, screen_width, lnY, font1, font2, font3
  global viewPortW, devLns
  lnY = []
  if fnt == 2:
    devFnt = font2
    devLnH = devFnt.metrics()['linespace'] 
    lns = 3
  elif fnt == 3:
    devFnt = font3
    devLnH = devFnt.metrics()['linespace']
    lns = 4
  else:
    devFnt = font1 
    devLnH = devFnt.metrics()['linespace'] 
    lns = 2
  fw = devFnt.measure('MWTH')/4
  lw = fw * 8;
  vh = (lns * devLnH) 
  yp = (screen_height-vh)/2
  viewPortW = lw
  for i in range(lns):
    lnY.append(yp)
    yp += devLnH
  devLns = lns  # number of lines on screen. Fixed by font choice. 
  log.info(f' {devLnH} {screen_width} X {screen_height}')
  log.info(f'lnY: {lnY}')


# returns True if we need to scroll 
def layoutLines(lns, nln, nwd, words):
  global viewPortW, devFnt, devLnH
  lns.clear()
  #log.info(f'layoutLines nln: {nln}, nwd: {nwd}, words: {words}')
  if nwd <= nln:
    y = 0
    for wd in words:
      wid = devFnt.measure(text=wd)
      lns.append(wd)
      y += devLnH
  else: 
    ln = ""
    wid = 0
    for wd in words:
      w = devFnt.measure(text=' ' + wd)
      if (wid + w) > viewPortW:
        lns.append(ln)
        wid = 0
        ln = ""
      if wid == 0:
        ln = wd
        wid = devFnt.measure(text=ln)
        #wid = w
        #log.info(f'first word |{ln}|{wid}')
      else:
        ln = ln+' '+wd
        wid = devFnt.measure(text=ln)
        #log.info(f'partial |{ln}|')

    # anything left over in ln ?
    if wid > 0:
      lns.append(ln)
  return len(lns) > nln


# st is index (0 based), end 1 higher  
def displayLines(st, end, textLines):
  global device, devLnH, firstLine,screen_width,saver_cvs,lnY
  firstLine = st
  saver_cvs.delete('all')
  y = lnY[0]
  #log.info(f'displayLines st: {st} end: {end}')
  # bug from layoutlines() is fixed up here with the min()
  for i in range(st, min(len(textLines), end)):      
    saver_cvs.create_text(
      (screen_width / 2 ),
      y, 
      font=devFnt, fill=stroke_fill,
      justify='center',
      text = textLines[i])
    y += devLnH

# need to track the top line # displayed: global firstLine, 0 based.
def scroll_timer_fired():
  global firstLine, textLines, nlns, devLns, scroll_thread
  #log.info(f'scroll firstLine: {firstLine}')
  firstLine = firstLine + devLns
  maxl = len(textLines)
  if firstLine > maxl:
    # at the end, roll around
    firstLine = 0
  end = min(firstLine + devLns, maxl)
  displayLines(firstLine, end, textLines)
  scroll_thread =  threading.Timer(1, scroll_timer_fired)
  scroll_thread.start()

  

if __name__ == '__main__':
  sys.exit(main())
