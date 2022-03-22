import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1115(i2c)

# Create single-ended input on channel 0
V1 = AnalogIn(ads, ADS.P1)
V2 = AnalogIn(ads, ADS.P2)

tempR=1000/(1-(V1.voltage)/(26555))
temp=706.6*(tempR**(-0.1541))-146

# Create differential input between channel 0 and 1
#chan = AnalogIn(ads, ADS.P0, ADS.P1)
print(f"{'raw':>5}\t{'v':>5}")
while True:
    print(f"{V1.value:>5}\t{V1.voltage:>5}")
    print(f"{V2.value:>5}\t{V2.voltage:>5}")
    print(f"temperature: {temp}")
    time.sleep(0.5)