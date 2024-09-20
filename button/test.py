# test switch on GPIO19 (pin 35), 
# 	Red LED on GPIO26 (pin 37)
#	Green LED on GPIO13 (pin 33)
from gpiozero import Button
from gpiozero import LED

#from gpiozero.pins.lgpio import LGPIOFactory
#from gpiozero import Device, PWMLED
#Device.pin_factory = LGPIOFactory(chip=4)

import time
which_led = 1
state = 0

def btn_callback(btn):
	global state
	print("she is released")
	if state == 0:
		red.on()
		green.off()
		state = 1
	elif state == 1:
		green.on();
		red.off()
		state = 2
	elif state == 2:
		green.on()
		red.on()
		state = 3
	elif state == 3:
		red.off()
		green.off()
		state = 0
	
			
red = LED(26)
green = LED(13)
button = Button(pin=19, bounce_time=0.01)
button.when_released = btn_callback
which_led = 1
led_state = False
	
while True:
	time.sleep(5)
