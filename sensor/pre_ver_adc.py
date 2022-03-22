import Adafruit_ADS1x15

GAIN = 1
adc = Adafruit_ADS1x15.ADS1115()

values = [0]*4

values[0] = adc.read_adc(0, gain=GAIN)
values[1] = adc.read_adc(2, gain=GAIN)

for i in value:
    print(value)