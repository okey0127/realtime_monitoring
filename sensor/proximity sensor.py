import RPi.GPIO as GPIO
import time
import cv2

proximity_pin = 8
GPIO.setmode(GPIO.BOARD)
product_number = 0

def add_product(channel):
    global product_number
    product_number += 1
    
GPIO.setup(proximity_pin, GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
#GPIO.add_event_detect(proximity_pin,GPIO.FALLING, callback=add_product,bouncetime=1000)

while True:
	#print(product_number)
	#time.sleep(1)
	#if cv2.waitKey(1) & 0xFF == 27:
    #break
    if GPIO.input(proximity_pin) == GPIO.HIGH:
        print('detect!')
    time.sleep(0.1)
