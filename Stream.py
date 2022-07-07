# edit: 22.06.25

import cv2
import time
import threading
from flask import Response, Flask, render_template, request, redirect, session, send_file
from flask import abort, jsonify, url_for, Blueprint, make_response
import numpy as np
import datetime
import math
import time
import schedule
import json

import RPi.GPIO as GPIO
import os
import io
import base64

import requests
#data visualize
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as img
from matplotlib.figure import Figure


#ADC module import
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


#initial
img_w = 640
img_h = 480
product_number = 0
timeC=0
check=0
n=0
c_cnt = 0

information = '-'
#RPM=0
#checkR=0

#setting ADC module
i2c_flag = 'Y'
try:
    # Create the I2C bus
    i2c = busio.I2C(board.SCL, board.SDA)
                                                                   
    # Create the ADC object using the I2C bus
    ads = ADS.ADS1115(i2c)

    # Create single-ended input on channel 0
    V0 = AnalogIn(ads, ADS.P0)
    V1 = AnalogIn(ads, ADS.P1)
except:
    i2c_flag='N'
    information = 'Remote I/O error!'
    
x_list = [x for x in range(60)]
vib_data = [0]*60
temp_data = [0]*60
time_data = [0]*60

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
log_path1 = f'{now_dir}/log/{day}server.csv'
log_path2 = f'{now_dir}/log/server.csv'

#if not exist log folder -> create log folter
if not os.path.exists(now_dir+'/log'):
    os.mkdir(now_dir+'/log')

#get ip
URL = 'https://icanhazip.com'
respons = requests.get(URL)
ex_ip = respons.text.strip()
ex_video_ip = 'http://'+ex_ip+':8080/video'
ex_log_all_ip = 'http://'+ex_ip+':8080/log/all'
ex_log_today_ip = 'http://'+ex_ip+':8080/log/today'
ex_temp_ip = 'http://'+ex_ip+':8080/temp_graph'
ex_vib_ip = 'http://'+ex_ip+':8080/vib_graph'

in_ip = os.popen('hostname -I').read().strip()
in_video_ip = 'http://'+in_ip+':8080/video'
in_log_all_ip = 'http://'+in_ip+':8080/log/all'
in_log_today_ip = 'http://'+in_ip+':8080/log/today'
in_temp_ip = 'http://'+in_ip+':8080/temp_graph'
in_vib_ip = 'http://'+in_ip+':8080/vib_graph'
in_ipaddr={'in_ip':in_ip, 'ex_ip':ex_ip, 'video':in_video_ip, 'log_all':in_log_all_ip, 'log_today':in_log_today_ip, 'temp':in_temp_ip, 'vib':in_vib_ip}
ex_ipaddr={'in_ip':in_ip, 'ex_ip':ex_ip, 'video':ex_video_ip, 'log_all':ex_log_all_ip, 'log_today':ex_log_today_ip, 'temp':ex_temp_ip, 'vib':ex_vib_ip}

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

def modify_inform(a):
    global information
    if information == '-':
        information = a
    else:
        information += (', ' + a)

data_dic = {}
time_list = []
temp_list = []
vib_list = []
def save_all_data():
    #save log data as CSV
    global data_dic
    if data_dic != {}:
        df = pd.DataFrame([data_dic])
        df.to_csv(log_path1, mode='a', index=False, header = False)
        df.to_csv(log_path2, mode='a', index=False, header = False)
        time_list.append(data_dic['Time'])
        temp_list.append(data_dic['Temperature'])
        vib_list.append(data_dic['Vibration'])
        if len(time_list) > 60:
            time_list.pop(0)
            temp_list.pop(0)
            vib_list.pop(0)
        
schedule.every(1).seconds.do(save_all_data)
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
    camera_flag = ''
    # Video capturing
    cap = cv2.VideoCapture(-1)   
    
    # Set Video Size
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, img_w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, img_h)
    
    while True:
        #warning img create
        global check, c_cnt, check_first
        global information
        global data_dic
        
        time=str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        time_ymd=str(datetime.datetime.now().strftime('%Y-%m-%d'))
        time_hms=str(datetime.datetime.now().strftime('%H:%M:%S'))
        
        ret, frame = cap.read()
        #frame = cv2.flip(frame, 0)
        if c_cnt == 0: 
            if frame is None:
                frame = n_img
                cv2.putText(frame,'Camera is not detected!',(center_x-200, center_y),font,2,white,thickness,cv2.LINE_AA)
                modify_inform('Camera is not detected!')               
            VibV = 0.0; temp = 0.0;
            data_dic = {'Date':time_ymd, 'Time':time_hms, 'Product': '-', 'Temperature':'-', 'Vibration':'-', 'Information': information}        
            c_cnt += 1
        
        #if no previous cvs file, 'header = True' command exe (mode != 'a')
        df = pd.DataFrame([data_dic])
        if not os.path.exists(log_path1):
            df.to_csv(log_path1, index=False, header = True)
        if not os.path.exists(log_path2):
            df.to_csv(log_path2, index=False, header = True)
        if information != '-':
            save_all_data()
        
        information = '-'
        #filter
        if i2c_flag == 'Y':
            tempR=1000/(1-(V0.value)/(26555))
            temp=round(706.6*(tempR**(-0.1541))-146,2)
        
            VibV=V1.value/26555*3.3
            VibV=round(abs(0.58-round(VibV,2)),2)
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
    
        
        cv2.putText(frame,time,L_time,font,fontscale,white,thickness,cv2.LINE_AA)
        cv2.putText(frame,'Production: ',L_countT,font,fontscale,white,thickness,cv2.LINE_AA)
        cv2.putText(frame,str(product_number),L_count,font,fontscale,white,thickness,cv2.LINE_AA)
        
        #warning
        global n
        
        if temp>50 and n%5==0:
           n=n+1
           check=check+1
           
           modify_inform('Too high Temp')
           data_dic = {'Date':time_ymd, 'Time':time_hms, 'Product':product_number, 'Temperature':temp, 'Vibration':VibV, 'Information': information}
           information = '-'
           save_all_data()
           frame = img2
        elif VibV>0.5 and n%5==0:
            n=n+1
            check=check+1
            
            modify_inform('Too high Vibration')
            data_dic = {'Date':time_ymd, 'Time':time_hms, 'Product':product_number, 'Temperature':temp, 'Vibration':VibV, 'Information': information}
            information = '-'
            save_all_data()
            frame = img3
        else:
            check=check+1
            n=n+1
           
        #save All data as dictionary                
        data_dic = {'Date':time_ymd, 'Time':time_hms, 'Product':product_number, 'Temperature':temp, 'Vibration':VibV, 'Information': information}
        schedule.run_pending()
        information = '-'
                 
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

@app.route('/data/temp', methods=["GET", "POST"])
def data_temp():
    global data_dic
    global time_list, temp_list
    return jsonify({'time':time_list, 'temp':temp_list})

@app.route('/temp_graph')
def temp_graph():
    return render_template('temp_graph.html')

@app.route('/data/vib', methods=["GET", "POST"])
def data_vib():
    global data_dic
    global time_list, vib_list
    return jsonify({'time':time_list, 'vib':vib_list})

@app.route('/vib_graph')
def vib_graph():
    return render_template('vib_graph.html')

@app.route('/')
def in_index():    
    return render_template('in_index.html', ipaddr = in_ipaddr)

@app.route('/ex')
def ex_index():
    return render_template('ex_index.html', ipaddr = ex_ipaddr)

#log file open
@app.route('/log/today')
def today_log()->str:
    df1 = pd.read_csv(log_path1)
    df1 = df1.iloc[::-1]
    return df1.to_html(header=True, index = False)
    
@app.route('/log/all')
def all_log()->str:
    df2 = pd.read_csv(log_path2)
    df2 = df2.iloc[::-1]
    return df2.to_html(header=True, index = False)

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