import RPi.GPIO as GPIO
import time
import cv2

proximity_pin = 18
GPIO.setmode(GPIO.BCM)
product_number = 0

def add_product(channel):
    global product_number
    product_number += 1
    
GPIO.setup(proximity_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(proximity_pin, GPIO.RISING, callback=add_product, bouncetime=1000)

while True:
    try:
        print(product_number)
        time.sleep(1)
    except KeyboardInterrupt as e:
        print('Exit', e)
        break
        
    #break
    #if GPIO.input(proximity_pin) == GPIO.HIGH:
    #    print('detect!')
    #time.sleep(0.1)
