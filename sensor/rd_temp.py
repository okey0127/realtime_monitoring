import board
import adafruit_mlx90614
import time

i2c=board.I2C()
mlx = adafruit_mlx90614.MLX90614(i2c)
while True:
    print(f'Ambient Temp: {mlx.ambient_temperature}')
    print(f'object Temp: {mlx.object_temperature}')
    time.sleep(0.5)