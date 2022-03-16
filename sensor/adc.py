import RPi.GPIO as GPIO
import time
import numpy as np
import math

GAIN = 1
adc = Adafruit_ADS1x15.ADS1115()
GPIO.setmode(GPIO.BCM)

while True:
	time.sleep(0.5)
	
	values = [0]*4
	
	values[0] = adc.read_adc(0, gain=GAIN)
    values[1] = adc.read_adc(1,gain=GAIN)
	
	tempR=1000/(1-(values[0])/(26555))
    temp=706.6*(tempR**(-0.1541))-146
    temp=round(temp,1)
    
    VibV=values[1]/26555*3.3
    VibV=round(abs(0.58-round(VibV,2)),2)
	
	for i in range(4):
        # Read the specified ADC channel using the previously set gain value.
        values[i] = adc.read_adc(i,gain=GAIN)
        
	print('temp: ', temp)
	print('Vib: ', VibV)
