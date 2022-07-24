import I2C_LCD
from time import *

mylcd=I2C_LCD.lcd()
str_ = "Hello"

mylcd.lcd_display_string(str_,1)
mylcd.lcd_display_string(str_,2)
#time.sleep(10)
