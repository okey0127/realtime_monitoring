# edit: 22.09.12

import cv2
import time
import threading
from flask import Response, Flask, render_template, request, redirect, session, send_file
from flask import abort, jsonify, url_for, Blueprint, make_response
import numpy as np
import datetime
import math
import schedule
import json

import RPi.GPIO as GPIO
import os
import io
import base64
import requests

#data visualize
import pandas as pd
from RPLCD.i2c import CharLCD
import I2C_LCD

#temperature sensor
import adafruit_mlx90614

#ADC module import(Vibration Sensor)
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

# Image frame sent to the Flask object
global video_frame
video_frame = None

# Use locks for thread-safe viewing of frames in multiple browsers
global thread_lock 
thread_lock = threading.Lock()

def modify_inform(a):
    global information
    if information == '-':
        information = a
    else:
        information += ', ' + a
        
#setting ADC module(Vibration Sensor)
vib_flag = 'Y'
try:
    # Create the I2C bus
    i2c = busio.I2C(board.SCL, board.SDA)
                                                                   
    # Create the ADC object using the I2C bus
    ads = ADS.ADS1115(i2c)

    # Create single-ended input on channel 0
    V0 = AnalogIn(ads, ADS.P0)
    
except:
    vib_flag='N'
    modify_inform('No vibration sensor')

#setting temperature sensor
temp_flag = 'Y'
try:
    i2c_temp=board.I2C()
    mlx = adafruit_mlx90614.MLX90614(i2c_temp)
except:
    temp_flag = 'N'
    modify_inform('No temperature sensor')

x_list = [x for x in range(60)]
vib_data = [0]*60
temp_data = [0]*60
time_data = [0]*60

n_img=np.zeros((img_h,img_w,3),np.uint8)
img2=np.zeros((img_h,img_w,3),np.uint8)
img3=np.zeros((img_h,img_w,3),np.uint8)
img4=np.zeros((img_h,img_w,3),np.uint8)

for i in range(0,img_h-1):
    for j in range(0,img_w-1):
        img2[i,j,0]=60
        img2[i,j,1]=60
        img2[i,j,2]=255
                    
        img3[i,j,0]=60
        img3[i,j,1]=60
        img3[i,j,2]=60
            
        img4[i,j,0]=128
        img4[i,j,1]=0
        img4[i,j,2]=128
                    
        n_img[i,j,0]=0
        n_img[i,j,1]=0
        n_img[i,j,2]=0

#color
black = (0,0,0)
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
L_fps = (center_x+150,center_y+180)
#log

now_dir = os.path.dirname(os.path.abspath(__file__))
day = time.strftime('%Y-%m-%d',time.localtime(time.time()))
log_path1 = f'{now_dir}/log/{day}server.csv'
vib_path = f'{now_dir}/log/vib/{day}vib.csv'

#if not exist log folder -> create log folter
if not os.path.exists(now_dir+'/log'):
    os.mkdir(now_dir+'/log')
if not os.path.exists(now_dir+'/log/vib'):
    os.mkdir(now_dir+'/log/vib')
    
#set path
#get ip
lcd_flag = 'Y'
try:
    lcd=CharLCD('PCF8574', 0x3f)
except:
    lcd_flag = 'N'
    
i_flag = 'Y'
while True:
    try:
        URL = 'https://icanhazip.com'
        respons = requests.get(URL)
        ex_ip = respons.text.strip()
        ex_video_ip = 'http://'+ex_ip+':8080/video'
        ex_log_all_ip = 'http://'+ex_ip+':8080/log/all'
        ex_log_today_ip = 'http://'+ex_ip+':8080/log/today'
        ex_temp_ip = 'http://'+ex_ip+':8080/temp_graph'
        ex_vib_ip = 'http://'+ex_ip+':8080/vib_graph'
        break
    except:
        if i_flag == 'Y':
            if lcd_flag == 'Y':
                lcd.cursor_pos=(0,0)
                lcd.write_string('No internet')
            i_flag = 'N'

in_ip = os.popen('hostname -I').read().strip()
in_video_ip = 'http://'+in_ip+':8080/video'
in_log_all_ip = 'http://'+in_ip+':8080/log/all'
in_log_today_ip = 'http://'+in_ip+':8080/log/today'
in_temp_ip = 'http://'+in_ip+':8080/temp_graph'
in_vib_ip = 'http://'+in_ip+':8080/vib_graph'
in_ipaddr={'in_ip':in_ip, 'ex_ip':ex_ip, 'video':in_video_ip, 'log_all':in_log_all_ip, 'log_today':in_log_today_ip, 'temp':in_temp_ip, 'vib':in_vib_ip}
ex_ipaddr={'in_ip':in_ip, 'ex_ip':ex_ip, 'video':ex_video_ip, 'log_all':ex_log_all_ip, 'log_today':ex_log_today_ip, 'temp':ex_temp_ip, 'vib':ex_vib_ip}

#lcd
#lcd=I2C_LCD.lcd()
ip_st = 0
ip_en = 17

inf_st = 0
inf_en = 17

def run_lcd():
    if lcd_flag == 'Y':
        global ip_st, ip_en, inf_st, inf_en, in_ip, data_dic
        ip_addr = in_ip+':8080'
        str_len = len(ip_addr)
        if str_len <= 16:
            lcd.cursor_pos=(0,0)
            lcd.write_string(ip_addr)
        else:
            ip_st += 1
            ip_en += 1
            if ip_en > str_len +1 :
                ip_st = 0
                ip_en = 17
            lcd.cursor_pos=(0,0)
            lcd.write_string(ip_addr[ip_st:ip_en])
    
        lcd_inf = data_dic['Information']
        info_len = len(lcd_inf)
        if info_len <= 16:
            lcd.cursor_pos=(1,0)
            lcd.write_string(lcd_inf + ' '*(16 - info_len))
        else:
            inf_st += 1
            inf_en += 1
            if inf_en > info_len+1 :
                inf_st = 0
                inf_en = 17
            lcd.cursor_pos=(1,0)
            lcd.write_string(lcd_inf[inf_st:inf_en])
#text
thickness =2
font=cv2.FONT_HERSHEY_PLAIN
fontscale =1

config_data={}
#load config data
def load_config_data():
    global config_data
    with open(now_dir+'/config_data.txt', 'rt') as cf:
        config_data_source = cf.readlines()
        config_data_list = []
        for d in config_data_source:
            d = d.strip('\n')
            config_data_list.append(d.split(':'))
    for index, value in enumerate(config_data_list):
        config_data[value[0]] = int(value[1])

load_config_data()

#save config data
def save_config_data():
    global config_data
    with open(now_dir+'/config_data.txt', 'wt') as cf:
        for key in config_data:
            cf.write(f'{key}:{config_data[key]}\n')
# remove old data
#save_term = 365 #initial save_range

def delete_old_data():
  global config_data
  save_term = config_data['save_term']
  #delete old date-server.csv file
  for f in os.listdir(now_dir+'/log'):
    f = os.path.join(now_dir+'/log', f)
    if os.path.isfile(f):
      timestamp_now = datetime.datetime.now().timestamp()
      is_old = os.stat(f).st_mtime < timestamp_now-(save_term * 24 * 60 * 60)
      if is_old:
        try:
          os.remove(f)
          print(f, 'is deleted')
        except OSError:
          pass #오류 무시

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

data_dic = {'Date':'-', 'Time':'-', 'Product': '-', 'Temperature':'-', 'Vibration':'-', 'Information': information}        
time_list = []
temp_list = []
vib_list = []
def save_all_data():
    #save log data as CSV
    global data_dic
    if data_dic != {}:
        df = pd.DataFrame([data_dic])
        if not os.path.exists(log_path1):
            df.to_csv(log_path1, index=False, header = True)
        else:
            os.system(f'sudo chmod 777 {log_path1}')
            df.to_csv(log_path1, mode='a', index=False, header = False)
        time_list.append(str(datetime.datetime.now().strftime('%H:%M:%S')))
        temp_list.append(data_dic['Temperature'])
        vib_list.append(data_dic['Vibration'])
        if len(time_list) > 60:
            time_list.pop(0)
            temp_list.pop(0)
            vib_list.pop(0)

#set proximity sensor
#product counter
GPIO.setmode(GPIO.BCM)
proximity_pin = 18
GPIO.setup(proximity_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(proximity_pin, GPIO.FALLING, callback=add_product, bouncetime=1000)

#buzzer
buzzer_pin = 23
GPIO.setup(buzzer_pin, GPIO.OUT)

def temp_buzz():
    try:
        GPIO.output(buzzer_pin, GPIO.HIGH)
        time.sleep(0.3)
        GPIO.output(buzzer_pin, GPIO.LOW)
        time.sleep(0.2)
    except:
        pass

def vib_buzz():
    try:
        GPIO.output(buzzer_pin, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(buzzer_pin, GPIO.LOW)
        time.sleep(0.2)
    except:
        pass


# run schedule
schedule.every(1).seconds.do(run_lcd)
schedule.every(1).seconds.do(save_all_data)
schedule.every(12).hours.do(delete_old_data)

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
        
        time_now=str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        time_ymd=str(datetime.datetime.now().strftime('%Y-%m-%d'))
        time_hms=str(datetime.datetime.now().strftime('%H:%M:%S.%f'))
        
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
        if information != '-':
            save_all_data()
        
        information = '-'
        
        #filter
        if vib_flag == 'Y':
            try:
                VibV=V0.value
                cv2.putText(frame,'Vibration',L_VibT,font,fontscale,black,thickness,cv2.LINE_AA)
                cv2.putText(frame,str(V0.value),L_Vib,font,fontscale,black,thickness,cv2.LINE_AA)
                
                cv2.putText(frame,'Vibration',L_VibT,font,fontscale,white,thickness-1,cv2.LINE_AA)
                cv2.putText(frame,str(V0.value),L_Vib,font,fontscale,white,thickness-1,cv2.LINE_AA)
            except:
                modify_inform('Vibration sensor is not working')
        if temp_flag == 'Y':
            try:
                temp = round(mlx.object_temperature, 2)
                cv2.putText(frame,'Temperature',L_tempT,font,fontscale,black,thickness,cv2.LINE_AA)
                cv2.putText(frame,str(temp)+"'C",L_temp,font,fontscale,black,thickness,cv2.LINE_AA)
                
                cv2.putText(frame,'Temperature',L_tempT,font,fontscale,white,thickness-1,cv2.LINE_AA)
                cv2.putText(frame,str(temp)+"'C",L_temp,font,fontscale,white,thickness-1,cv2.LINE_AA)
            except:
                modify_inform('Temperature sensor is not working')
        if product_number > 0:
            cv2.putText(frame,'Production: ',L_countT,font,fontscale,black,thickness,cv2.LINE_AA)
            cv2.putText(frame,str(product_number),L_count,font,fontscale,black,thickness,cv2.LINE_AA)
            
            cv2.putText(frame,'Production: ',L_countT,font,fontscale,white,thickness-1,cv2.LINE_AA)
            cv2.putText(frame,str(product_number),L_count,font,fontscale,white,thickness-1,cv2.LINE_AA)
        
        cv2.putText(frame,time_now,L_time,font,fontscale,black,thickness,cv2.LINE_AA)
        cv2.putText(frame,time_now,L_time,font,fontscale,white,thickness-1,cv2.LINE_AA)
        
        '''
            cv2.putText(frame,'RPM',L_RPMT,font,fontscale,white,thickness,cv2.LINE_AA)
            if checkR==0:
                cv2.putText(frame,'0',L_RPM,font,fontscale,white,thickness)
            else:
                cv2.putText(frame,str(RPM),L_RPM,font,fontscale,white,thickness)
        ''' 
        #warning
        global n, config_data
        #warning temperature, warning vibration
        w_flag = False
        w_temp = config_data['w_temp']
        w_vib = config_data['w_vib']
        
        # modify warning inform
        if temp > w_temp:
            modify_inform('high Temperature')
            temp_buzz()
            w_flag = True
        if VibV > w_vib:
            modify_inform('high Vibration')
            vib_buzz()
            w_flag = True
        if w_flag:
            data_dic = {'Date':time_ymd, 'Time':time_hms, 'Product':product_number, 'Temperature':temp, 'Vibration':VibV, 'Information': information}
            save_all_data()
        
        # modify warning video
        if temp>w_temp and VibV>w_vib and n%5==0:
            n=n+1
            check=check+1
            frame = img4 
        elif temp>w_temp and n%5==0:
            n=n+1
            check=check+1
            frame = img2
        elif VibV>w_vib and n%5==0:
            n=n+1
            check=check+1
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
            
        GPIO.output(buzzer_pin, GPIO.LOW)
    
    cap.release()
    GPIO.cleanup()
    
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

@app.route('/data/info', methods=["GET", "POST"])
def data_info():
    try:
        global data_dic
        return jsonify({'time':data_dic['Time'], 'info':data_dic['Information']})
    except:
        return '<h1> Error </h1>'

@app.route('/data/temp', methods=["GET", "POST"])
def data_temp():
    global time_list, temp_list
    return jsonify({'time':time_list, 'temp_list':temp_list})

@app.route('/temp_graph')
def temp_graph():
    return render_template('temp_graph.html')

@app.route('/data/vib', methods=["GET", "POST"])
def data_vib():
    global time_list, vib_list
    return jsonify({'time':time_list, 'vib_list':vib_list})

@app.route('/vib_graph')
def vib_graph():
    return render_template('vib_graph.html')

@app.route('/')
def index():
    return render_template('index.html', ipaddr = in_ipaddr)

search_date = 0
#log file open
@app.route('/log', methods=['GET', 'POST'])
def log():
    try:
        global search_date
        if request.method == 'GET':
            search_date = request.args.get('search_date')
            log_path = f'{now_dir}/log/{search_date}server.csv'
            df = pd.read_csv(log_path)
            df = df.iloc[::-1]
            
            return "<form action ='/log', method='POST'><button type='submit'>Download</button></form>"+df.to_html(header=True, index = False, justify='center')
        elif request.method == 'POST':
            return redirect(url_for('DownloadFile', date = search_date))
    except:
        return '<h1>Error:</h1> <p>해당 날짜에 데이터가 없습니다.</p>'

@app.route('/DownloadFile/<date>')
def DownloadFile(date):
    log_path = f'{now_dir}/log/{date}server.csv'
    return send_file(log_path, attachment_filename=f'{date}log.csv', as_attachment=True)

@app.route('/setting', methods=['GET', 'POST'])
def Settingpage():
    global config_data, data_dic, information
    if request.method == 'POST':
        #update save term
        try:
            save_term = int(request.form['alt_save_term'])
            if save_term < 30:
                save_term = 30            
            config_data['save_term'] = save_term
            save_config_data()
            load_config_data()
            ip = request.remote_addr
            modify_inform(f'{ip}:저장기간을 {config_data["save_term"]}로 수정')
            data_dic['Information'] = information
            save_all_data()
            return redirect('/setting')
        except:
            pass
        try:
            w_temp = int(request.form['alt_w_temp'])
            config_data['w_temp'] = w_temp
            save_config_data()
            load_config_data()
            ip = request.remote_addr
            modify_inform(f'{ip}:경고 온도를 {config_data["w_temp"]}로 수정')
            data_dic['Information'] = information
            save_all_data()
            return redirect('/setting')
        except:
            pass
        try:
            w_vib = int(request.form['alt_w_vib'])
            config_data['w_vib'] = w_vib
            save_config_data()
            load_config_data()
            ip = request.remote_addr
            modify_inform(f'{ip}:경고 진동을 {config_data["w_vib"]}로 수정')
            data_dic['Information'] = information
            save_all_data()
            return redirect('/setting')
        except:
            pass
    return render_template('setting.html', save_term = config_data['save_term'], w_temp = config_data['w_temp'], w_vib=config_data['w_vib'])
    
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
