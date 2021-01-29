require 'paho-mqtt'
require 'json'

$hscn_sub = "homie/trumpy_bear/screen/control/set"
$hscn_pub = "homie/trumpy_bear/screen/control"
$hcmd_pub = "homie/trumpy_bear/control/cmd/set"
$hdspm_sub = 'homie/trumpy_ranger/display/mode/set'
$hdspt_sub = 'homie/trumpy_ranger/display/text/set'
# turrets
$htur1_pub = 'homie/turret_front/turret_1/control/set'
$htur2_pub = 'homie/turret_back/turret_1/control/set'
$htur1_sub = 'homie/turret_font/turret_1/control'
$htur2_sub = 'homie/turret_back/turret_1/control'
# tracker video
$htrkv_sub = 'homie/panel_tracker/track/control/set'
# alarm 
$alarm_pub= 'homie/trumpy_bear/control/cmd'
$laser_cmds = {'Square': 'square', 'Circle': 'circle', 'Diamond': 'diamond', 
  'Crosshairs':'crosshairs', 'Horizontal Sweep': 'hzig', 'Vertical Sweep': 'vzig',
   'Random': 'random', 'TB Tame': 'tame', 'TB Mean': 'mean'}

$turrets = nil

Shoes.app width: 900, height: 580 do 
  app.name = "Trumpy Bear"
  #app.fullscreen = true
   
  flow do
    @menu = stack width: 200, margin: 25  do
      @alarm_btn = button "Alarm", height: 80, width: 100, margin: 20,
          font: "Menlo Bold 14" do
        alarm_panel
      end
      @voice_btn = button "Voice", height: 80, width: 100, margin: 20,
          font: "Menlo Bold 14" do
        mycroft_panel
      end
      @lasers_btn = button "Lasers", height: 80, width: 100, margin: 20,
          font: "Menlo Bold 14" do
        laser_panel
      end   
      @login_btn = button "Login", height: 80, width: 100, margin: 20,
          font: "Menlo Bold 14" do 
        login
      end
      @logout_btn = button "Logout", height: 80, width: 100, margin: 20,
          font: "Menlo Bold 14"  do 
        logout
      end
    end
    @panel = stack width: 700 do
      @hdr = title "Trumpy Bear"
      @status = subtitle "Login"
      @img = image "/home/pi/login/images/IF-Garden.JPG", height: 300, width: 400, cache: false,
          align: "center"
      flow do
        tagline "Messages:", margin_right: 20
        @msg = tagline "display: #{ENV['DISPLAY']}"
      end
    end
      
  end # top level flow
  start {    
    $client = PahoMqtt::Client.new({persistent: true, keep_alive: 7, client_id: "TB Login-#{Process.pid}"})
    $client.connect("192.168.1.7", 1883)
    $client.on_message { |msg|
      debug "#{msg.topic} #{msg.payload}"
      if msg.topic == $hscn_sub 
        if msg.payload == 'wake'
          wake_up
        elsif msg.payload.start_with?('{')
          hsh = JSON.parse(msg.payload)
          debug "json parse: #{hsh.inspect}"
          cmd =  hsh['cmd']
          if cmd == 'wake'
            wake_up
          elsif cmd == 'register'
            do_register
          elsif cmd == 'user'
            #@img.path = '/var/www/camera/face.jpg'
            user = hsh['user']
            role = hsh['role']
            #@img.path = "/home/pi/.trumpybear/#{user}/face/#{user}.jpg"
            @img.path = pict_for(user)
            debug "#{user} logged in"
            @status.text = "#{user} is logged in"
            @alarm_btn.show
            @voice_btn.show
            @lasers_btn.show
            @login_btn.hide
            @logout_btn.show
            dt = {'cmd': 'get_turrets'}
            $client.publish($hcmd_pub,dt.to_json)
          elsif cmd == 'set_turrets'
            # TODO (re) build $turrets ary of hash
            $turrets = hsh['turrets']
            debug $turrets
          elsif cmd == 'logout'
            logout
          elsif cmd == 'tracking'
            @tgt_msg.text = hsh['msg']
            #@tgt_img.path = '/home/pi/Projects/tmp/tracking.jpg'
          end
        end
      elsif msg.topic == $htrkv_sub
        $stderr.puts "got #{msg.topic} #{msg.payload}"
        hsh = JSON.parse(msg.payload)
        if hsh['uri'] != nil
          uri = hsh['uri']
          @vid_widget.path = uri
          @vid_widget.play
        elsif hsh['uri'] == nil
          if @vid_widget 
            @vid_widget.stop
          end        
        else
          $stderr.puts "ignore #{msg.payload}"
        end
      elsif msg.topic == $hdspm_sub
        # display_mode command. 
        if msg.payload == 'off'
          # trigger screen saver - hide our stuff
          monitor_sleep
        elsif msg.payload == 'on'
          # turn screen saver off - show our goods.
          monitor_wake
        end
      elsif msg.topic == $hdspt_sub
        # text command
        @msg.text = msg.payload
      elsif msg.topic == $htur1_sub || msg.topic == $htur2_sub
        # 'OK' is a possible payload
        if msg.payload.start_with?('{')
          dt = JSON.parse(msg.payload)
          #debug "#{dt['bounds']}"
          #manual_panel dt['bounds']
        end
      end
    }
    $client.subscribe([$hscn_sub, 1], [$hdspm_sub, 1], [$hdspt_sub, 1],
      [$htur1_sub, 1], [$htur2_sub, 1], [$htrkv_sub, 1]) 
    Thread.new do
      $client.loop_read
      sleep 0.1
    end
    @alarm_btn.hide
    @voice_btn.hide
    @lasers_btn.hide
    @logout_btn.hide
    $stderr.puts "Using #{ENV['DISPLAY']}"
    debug "Using #{ENV['DISPLAY']}"
    Shoes.show_log
  }
  
  def pict_for(name)
    fps = Dir.glob("/home/pi/.trumpybear/#{name}/face/*.jpg")
    fps.sort!
    return fps[-1]
  end
  
  def wake_up
    # run Hubitat lighting/Muting automations 
    debug "Wake up runs"
    $client.publish($hscn_pub, "awake", false, 1)
  end
  
  def monitor_wake
    debug "waking monitor"
    system('DISPLAY=:0; xset s reset')
  end
  
  def monitor_sleep
    debug "sleeping monitor"
    system('DISPLAY=:0; xset s activate')
  end
  
  def keepalive
    dt = {'cmd' => 'keepalive', 'minutes' => 2}
    $client.publish($hcmd_pub,dt.to_json)
  end
  
  def do_register
    # unsleep screen saver
    monitor_wake
    # tell hubitat we are working.
    wake_up
    # put Trumpybear in Register Mode
    dt = {'cmd': 'register'}
    $client.publish($hcmd_pub,dt.to_json)
    @status.text = "Registering"
  end
  
  def login
    # turn on the lamp
    $client.publish($hscn_pub, "awake", false, 1)
    sleep(1)   # enough time to turn on the lamp?
    dt = {'cmd' => 'login'}
    $client.publish($hcmd_pub, dt.to_json, false, 1)
    # async response from trumpy.py will arrive.
  end
  
  def logout
    @panel.clear do
      @hdr = title "Trumpy Bear", align: "center"
      @status = subtitle "Login", align: "center"
      @img = image "images/IF-Garden.JPG", height: 300, width: 400, cache: false,
          align: "center"
      flow do
        tagline "Messages:", margin_right: 20
        #@msg = tagline "#{Dir.pwd}"
        @msg = tagline ""
      end
      @alarm_btn.hide
      @voice_btn.hide
      @lasers_btn.hide
      @login_btn.show
      @logout_btn.hide
      @status.text = 'Please Login'
      $client.publish($hscn_pub, "closing", false, 1)
      @msg.text = "Please Login"
      #$client.publish($hdspt_sub, "Please Login", false, 1)
      lasers_off
    end
  end
  
  def alarm_panel
    @panel.clear do
      stack width: 650 do
        title "Control Alarms"
        tagline "May not work quickly"
        # turn on/off the housekeeping switch. On means Alarm Off.
        flow do 
          button "Turn OFF Alarm", height: 80, width: 100, margin_left: 20,
              font: "Menlo Bold 14" do
            $client.publish($alarm_pub, "on", false, 1)
            # watch out for looping on this. hdspt is the Display
            $client.publish($hdspt_sub, "Alarm Off", false, 1)
          end
       end
      end
    end
  end
  
  def mycroft_panel
    @panel.clear do
      stack width: 650 do
        title "Talk with Mycroft and Trumpy Bear"
        tagline "Push the 'Talk' button and Say 'Hey Mycroft' and "
        tagline "after the beep, ask a question. Like"
        tagline "Hey Mycroft, what about the lasers?"
        flow do 
          button "Talk", font: 'Sans 16' do
            dt = {'cmd': 'mycroft'}
            $client.publish($hcmd_pub,dt.to_json)
          end
        end
      end
    end
  end
  
  def lasers_off
    pdt = {'power' =>  0}
    $turrets.each {|tur| $client.publish("#{tur['topic']}/set", pdt.to_json, false, 1)}
  end
  
  def laser_panel
    # turn off lasers, just in case.
    lasers_off
    $turrets[0]['selected'] = true
    @panel.clear do
      stack width: 650 do 
        @sel_tur = {}
        title "Exercise The Lasers", align: "center"
        flow  do
          stack width: 300 do
            tagline "Select Options", margin: 12
            # watch out for sym vs string and implicit conversions. Gotcha.
            @exec = list_box items: $laser_cmds.keys,
              font: 'Sans 16', margin: 12, choose: 'Vertical Sweep'.to_sym
            $turrets.each do |tur|
              f = flow do 
                check checked: tur['selected'] do |chk| 
                  tur['selected'] = chk.checked?
                end
                para "#{tur['name']}", font: 'Sans 16'
              end
            end
            button "Execute", font: 'Sans 16', margin: 12 do
              dt = {}
              cmd = $laser_cmds[@exec.text]
              dt['exec'] = cmd
              dt['count'] = @count.text.to_i 
              dt['time'] = @time.text.to_f
              if cmd == 'hzig' || cmd == 'vzig'
                dt['lines'] = @lines.text.to_i
              elsif cmd == 'diamond' || cmd == 'crosshairs' or cmd == 'random'
                dt['length'] = @length.text.to_i
              elsif cmd == 'circle'
                dt['radius'] = @radius.text.to_i 
              end
              $turrets.each do |tur|
                if tur['selected'] 
                  $client.publish("#{tur['topic']}/set", dt.to_json, false, 1)
                end
              end
              keepalive
            end
            button "Lamp Off", font: 'Sans 16', margin: 12 do
              $client.publish($hscn_pub, "closing", false, 1)
            end
            button "Calibrate", font: 'Sans 16', margin: 12 do
              calibrate_panel
            end
            button "Manual", font: 'Sans 16', margin: 12 do
              manual_panel
            end
            button "Tracking", font: 'Sans 16', margin: 12 do
              target_panel
            end
          end
          stack width: 300 do
            para "Time allowed:", font: 'Sans 16', width: 50, margin: 8
            @time = list_box items: ['2','4','6','10'], choose: '2',
                font: 'Sans 16', margin_bottom: 6
            para "Count", font: 'Sans 16', width: 50, margin: 8
            @count = list_box items: ['1','2','3','4','6','8'], choose: '2',
                font: 'Sans 16', margin_bottom: 6
            para "Lines (sweeps)", font: 'Sans 16',  margin: 8
            @lines = list_box items: ['4', '5', '7', '9'], choose: '5', 
                font: 'Sans 16',  margin_bottom: 8
            para "Length (diamonds)", font: 'Sans 16', margin: 8 
            @length = list_box items: ['10', '15', '20', '30', '50'], 
                choose: '30', font: 'Sans 16',  margin: 8
            para "Radius (circles)", font: 'Sans 16', margin: 8
            @radius = list_box items: ['10', '15', '20', '30', '50'], 
                choose: '20', font: 'Sans 16',  margin: 8
          end
        end
      end
    end
  end
  
  def calibrate_panel
    @panel.clear do 
      flow width: 650 do
        stack do
          @tgt_img = image @img.path, height: 300, width: 400, cache: false,
              align: "center"
          flow do 
            @dist_lb = list_box items: ['1', '2', '3', '4'],
              choose: '1', font: 'Sans 16',  margin: 8
            para "Distance from Camera", font: 'Sans 16', margin: 8
          end
          flow do 
            @time_lb = list_box items: ['5', '10', '15', '20'],
              choose: '10', font: 'Sans 16',  margin: 8
            para "Time for sweep (seconds)", font: 'Sans 16', margin: 8
          end
          button "Begin", font: 'Sans 16', margin: 12 do
              dt = {'cmd': 'calib'}
              dt['time'] = @time_lb.text.to_i
              dt['distance'] = @dist_lb.text.to_i
              $client.publish($hcmd_pub,dt.to_json)
          end 
        end
      end
    end
  end

  def manual_panel
      @panel.clear do 
        flow width: 650 do
          $turrets.each do |tur| 
            stack width: 300 do 
              #@tgt_img = image @img.path, height: 300, width: 400, cache: false,
              #align: "center"
              flow do
                tagline "Power", margin_right: 5
                tur['widget_p'] = switch font: 'Sans 16', margin: 10 do |n|
                  tur['power'] = tur['widget_p'].active? ? 100 : 0
                  pdt = {'power' =>  tur['power']}
                  debug "power set to #{tur['power'] }"
                  $client.publish("#{tur['topic']}/set", pdt.to_json, false, 1)
                end
              end
              tagline "Pan (x)", align: 'center', margin_top: 10
              flow do
                tagline "#{tur['pan_min']}"
                slider fraction: 0.5 , state: nil, margin: 5 do |f|
                  pf = f.fraction
                  rng = tur['pan_max'] - tur['pan_min']
                  v = (rng * pf) + tur['pan_min']
                  vs = sprintf('%3.1f', v)
                  tur['pan_cur'] = vs
                  debug "pan set to #{vs}"
                  tur['widget_x'].text = tur['pan_cur']
                  pdt = {'pan' =>  v}
                  #pdt['power'] =  @sw.active? ? 100 : 0
                  $client.publish("#{tur['topic']}/set", pdt.to_json, false, 1)
                  keepalive
                end
                tagline "#{tur['pan_max']}"
              end
              tur['widget_x'] = tagline "", align: "center"
              tagline "Tilt (y)", align: 'center'
              flow do
                tagline "#{tur['tilt_min']}"
                slider fraction: 0.5, state: nil, margin: 5 do |f|
                  pf = f.fraction
                  rng = tur['tilt_max'] - tur['tilt_min']
                  v = (rng * pf) + tur['tilt_min']
                  vs = sprintf('%3.1f', v)
                  debug "tilt set to #{vs}"
                  tur['tilt_cur'] = vs
                  tur['widget_y'].text = tur['tilt_cur']
                  pdt = {'tilt' =>  v}
                  #pdt['power'] =  @sw.active? ? 100 : 0
                  $client.publish("#{tur['topic']}/set", pdt.to_json, false, 1)
                  keepalive
                end
                tagline "#{tur['tilt_max']}"
              end
              tur['widget_y'] = tagline "", align: "center"
            end
          end
        end
      end

  end
  
  def target_panel(uri="")
    @panel.clear do 
      $stderr.puts "starting target_panel with #{uri}"
      require 'shoes/videoffi'
      stack do
        @vid_widget = video("", auto_play: false,
            height: 300, width: 400, align: "center")
        flow do
          tagline "Messages:", margin_right: 20
          @tgt_msg = tagline "waiting.."
        end
        button "Track Me", font: 'Sans 16', margin: 10 do
          dt = {'cmd': 'track', 'debug': false, 'test': true}
          $client.publish($hcmd_pub,dt.to_json)
        end
      end
    end
  end
end
