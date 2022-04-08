# edit: 22.04.08

import cv2
import time
import threading
from flask import Response, Flask, render_template
import numpy as np
import datetime
import math
import time
import logging
import RPi.GPIO as GPIO
import os

#ADC module import
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)
                                                                   
# Create the ADC object using the I2C bus
ads = ADS.ADS1115(i2c)

# Create single-ended input on channel 0
V0 = AnalogIn(ads, ADS.P0)
V1 = AnalogIn(ads, ADS.P1)

#initial
img_w = 640
img_h = 480
product_number = 0
timeC=0
check=0
n=0
c_cnt = 0
#RPM=0
#checkR=0

n_img=np.zeros((img_h,img_w,3),np.uint8)
img2=np.zeros((img_h,img_w,3),np.uint8)
img3=np.zeros((img_h,img_w,3),np.uint8)

if check==0:
    for i in range(0,img_h-1):
        for j in range(0,img_w-1):
            img2[i,j,0]=60
            img2[i,j,1]=60
            img2[i,j,2]=255
                    
            img3[i,j,0]=60
            img3[i,j,1]=60
            img3[i,j,2]=60
                    
            n_img[i,j,0]=0
            n_img[i,j,1]=0
            n_img[i,j,2]=0

#color
red=(0,0,255)
green=(0,255,0)
blue=(255,0,0)
white=(255,255,255)
yellow=(0,255,255)
cyan=(255,255,0)
magenta=(255,0,255)

#position
center_x=int(img_w/2.0)
center_y=int(img_h/2.0)
L_time=(center_x-300,center_y+200)
L_count=(center_x-200,center_y-200)
L_countT=(center_x-300,center_y-200)
L_temp=(center_x+50,center_y-200)
L_tempT=(center_x-100,center_y-200)
L_RPM=(center_x+50,center_y-180)
L_RPMT=(center_x-100,center_y-180)
L_Vib=(center_x+250,center_y-200)
L_VibT=(center_x+150,center_y-200)

#log
#set path
now_dir = os.path.dirname(os.path.abspath(__file__))
day = time.strftime('%Y-%m-%d',time.localtime(time.time()))
log_path1 = f'{now_dir}/log/{day}server.log'
log_path2 = f'{now_dir}/log/server.log'

#if not exist log folder -> create log folter
if not os.path.exists(now_dir+'/log'):
    os.mkdir(now_dir+'/log')
    
logger1=logging.getLogger()
#logger2=logging.getLogger()

logger1.setLevel(logging.INFO)
#logger2.setLevel(logging.INFO)

formatter1 = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
#formatter2 = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')

day = time.strftime('%Y-%m-%d',time.localtime(time.time()))
file_handler1=logging.FileHandler(log_path1)
file_handler2=logging.FileHandler(log_path2)
file_handler1.setFormatter(formatter1)
file_handler2.setFormatter(formatter1)
logger1.addHandler(file_handler1)
logger1.addHandler(file_handler2)

#remove werkzeug messages from logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

#text
thickness =2
font=cv2.FONT_HERSHEY_PLAIN
fontscale =1

# Image frame sent to the Flask object
global video_frame
video_frame = None

# Use locks for thread-safe viewing of frames in multiple browsers
global thread_lock 
thread_lock = threading.Lock()

#function
def add_product(channel):
    global product_number
    product_number += 1
    #logger1.info(f'Proudction : {product_number}')
    #logger2.info(f'Proudction : {product_number}')
    
'''
def count_RPM(channel) :
    global RPM
    global checkR
    global timeC
    checkR+=1
    RPM=1/(time.time()-timeC)*60
    RPM=round(RPM,1)
    if RPM<30:
        RPM=0
    timeC=time.time()
'''
#set proximity sensor
#product counter
proximity_pin = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(proximity_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(proximity_pin, GPIO.FALLING, callback=add_product, bouncetime=1000)

#declare Flask Server
app = Flask(__name__)

def captureFrames():
    global video_frame, thread_lock

    # Video capturing
    cap = cv2.VideoCapture(0)

    # Set Video Size
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, img_w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, img_h)
    
    while True:
        #warning img create
        global check, c_cnt
        
        ret, frame = cap.read()
        
        if not ret:
            frame = n_img
            cv2.putText(frame,'Camera is not detected!',(center_x-200, center_y),font,2,white,thickness,cv2.LINE_AA)
            if c_cnt == 0:
                logger1.warning('Camera is not detected!')
                c_cnt += 1
                    
        #calculates
        time=str(datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S'))
        
        tempR=1000/(1-(V0.value)/(26555))
        temp=round(706.6*(tempR**(-0.1541))-146,2)
        
        VibV=V1.value/26555*3.3
        VibV=round(abs(0.58-round(VibV,2)),2)
        
        #filter
        cv2.putText(frame,time,L_time,font,fontscale,white,thickness,cv2.LINE_AA)
        
        cv2.putText(frame,'Production: ',L_countT,font,fontscale,white,thickness,cv2.LINE_AA)
        cv2.putText(frame,str(product_number),L_count,font,fontscale,white,thickness,cv2.LINE_AA)
        
        cv2.putText(frame,'Temperature',L_tempT,font,fontscale,white,thickness,cv2.LINE_AA)
        cv2.putText(frame,str(temp)+"'C",L_temp,font,fontscale,white,thickness,cv2.LINE_AA)
        '''
        cv2.putText(frame,'RPM',L_RPMT,font,fontscale,white,thickness,cv2.LINE_AA)
        if checkR==0:
            cv2.putText(frame,'0',L_RPM,font,fontscale,white,thickness)
        else:
            cv2.putText(frame,str(RPM),L_RPM,font,fontscale,white,thickness)
        ''' 
        cv2.putText(frame,'Vibration',L_VibT,font,fontscale,white,thickness,cv2.LINE_AA)
        cv2.putText(frame,str(VibV),L_Vib,font,fontscale,white,thickness,cv2.LINE_AA)
        
        #warning
        global n
        
        if temp>50 and n%5==0:
           n=n+1
           check=check+1
           logger1.warning('Too high Temp')
           frame = img2
        elif VibV>0.5 and n%5==0:
            n=n+1
            check=check+1
            logger1.warning('Too high Vibration')
            frame = img3
        else:
            check=check+1
            n=n+1
            if n%100==0:
                logger1.info(f'{"Production"} : {product_number} | {"Temperature"} : {temp:.1f} | {"Vibration"} : {VibV:.2f}')
                #including RPM 
                #logger1.info(f'{"Production"} : {product_number} | {"Temperature"} : {temp:.1f} | {"RPM"} : {RPM:.1f} | {"Vibration"} : {VibV:.2f}')
                        
        # Create a copy of the frame and store it in the global variable,
        # with thread safe access
        with thread_lock:
            video_frame = frame.copy()

    cap.release()

def encodeFrame():
    global thread_lock
    while True:
        # Acquire thread_lock to access the global video_frame object
        with thread_lock:
            global video_frame
            if video_frame is None:
                continue
            return_key, encoded_image = cv2.imencode(".jpg", video_frame)
            if not return_key:
                continue

        # Output image as a byte array
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encoded_image) + b'\r\n')

@app.route('/video')
def streamFrames():
    return Response(encodeFrame(), mimetype = "multipart/x-mixed-replace; boundary=frame")

@app.route('/')
def index():

    return render_template('index.html')

#log file open
@app.route('/log/today')
def today_log()->str:
    f = open(log_path1,'r')
    fl = f.readlines()
    f_out = []
    for i in range(len(fl)):
        if 'root' in fl[i]:
            f_out.append(fl[i])
        else:
            pass
    f_out.reverse()
    return "</br>".join(f_out)
    
@app.route('/log/all')
def all_log()->str:
    f = open(log_path2,'r')
    fl = f.readlines()
    f_out = []
    for i in range(len(fl)):
        if 'root' in fl[i]:
            f_out.append(fl[i])
        else:
            pass
    f_out.reverse()
    return "</br>".join(f_out)

# check to see if this is the main thread of execution
if __name__ == '__main__':

    # Create a thread and attach the method that captures the image frames, to it
    process_thread = threading.Thread(target=captureFrames)
    process_thread.daemon = True

    # Start the thread
    process_thread.start()

    # start the Flask Web Application
    # While it can be run on any feasible IP, IP = 0.0.0.0 renders the web app on
    # the host machine's localhost and is discoverable by other machines on the same network 
    app.run(host="0.0.0.0", port="8080")