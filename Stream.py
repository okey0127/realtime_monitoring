# edit: 22.11.29

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

# initial
img_w = 640
img_h = 480
product_number = 0
timeC=0
check=0
n=0
c_cnt = 0
information = '-'

# 영상 글꼴
thickness = 2
font=cv2.FONT_HERSHEY_PLAIN
fontscale = 1

# 영상 텍스트 위치
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
L_FPS = (center_x+250,center_y+200)
L_FPST = (center_x+150,center_y+200)

# Image frame sent to the Flask object
global video_frame
video_frame = None

# Use locks for thread-safe viewing of frames in multiple browsers
global thread_lock 
thread_lock = threading.Lock()

# 문제 발생시 송출할 화면 생성(고온: 빨강, 충격: 회색, 동시 발생: 보라)
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

# Colors
black = (0,0,0)
red=(0,0,255)
green=(0,255,0)
blue=(255,0,0)
white=(255,255,255)
yellow=(0,255,255)
cyan=(255,255,0)
magenta=(255,0,255)

# 파일 경로 가져오기
now_dir = os.path.dirname(os.path.abspath(__file__))

# if not exist log folder -> create log folter
if not os.path.exists(now_dir+'/log'):
    os.mkdir(now_dir+'/log')

## LCD ##
# Setting LCD
def try_lcd():
    global lcd, lcd_flag
    try:
        lcd=CharLCD('PCF8574', 0x3f)
        lcd_flag = True
    except:
        lcd_flag = False
try_lcd()

## Get IP ##
global i_flag
global ipaddr
global i_cnt

def get_ip():
    global i_flag, ipaddr
    try:
        URL = 'https://icanhazip.com'
        respons = requests.get(URL)
        ex_ip = respons.text.strip()
        i_flag = True
    except:
        i_flag = False
        if lcd_flag:
            lcd.clear()
            lcd.cursor_pos=(0,0)
            lcd.write_string('No internet')
        ex_ip = 'No internet'
    in_ip = os.popen('hostname -I').read().strip()
    ipaddr={'in_ip':in_ip, 'ex_ip':ex_ip}
get_ip()

# LCD 동작 함수 
ip_st = 0
ip_en = 17
inf_st = 0
inf_en = 17
def run_lcd():
    global ip_st, ip_en, inf_st, inf_en, data_dic, i_flag, ipaddr, lcd_flag
    try:
        if lcd_flag:
            get_ip()
            ip_addr = ipaddr['in_ip']+':8080'
            str_len = len(ip_addr)
            if i_flag:
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
            
        else:
            try_lcd()
    except:
        pass

## load config data ##
config_data={}
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

## save config data ##
def save_config_data():
    global config_data
    with open(now_dir+'/config_data.txt', 'wt') as cf:
        for key in config_data:
            cf.write(f'{key}:{config_data[key]}\n')

## remove old data ##
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


# information 수정 함수
def modify_inform(a):
    global information
    if information == '-':
        information = a
    else:
        information += ', ' + a
        
## setting ADC module(Vibration Sensor) ##
vib_flag = True
try:
    # Create the I2C bus
    i2c = busio.I2C(board.SCL, board.SDA)
                                                                   
    # Create the ADC object using the I2C bus
    ads = ADS.ADS1115(i2c)

    # Create single-ended input on channel 0
    V0 = AnalogIn(ads, ADS.P0)
    
except:
    vib_flag=False
    modify_inform('No vibration sensor')

## setting temperature sensor ##
temp_flag = True
try:
    i2c_temp=board.I2C()
    mlx = adafruit_mlx90614.MLX90614(i2c_temp)
except:
    temp_flag = False
    modify_inform('No temperature sensor')

## set proximity sensor ##
# 제품 갯수 측정 함수 
def add_product(channel):
    global product_number
    product_number += 1
    
#product counter
GPIO.setmode(GPIO.BCM)
proximity_pin = 18
GPIO.setup(proximity_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(proximity_pin, GPIO.FALLING, callback=add_product, bouncetime=1000)

## setting buzzer ##
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

def buzz_loop():
    while True:
        global wv_flag, wt_flag
        if wv_flag:
            vib_buzz()
        if wt_flag:
            temp_buzz()


## 센서로부터 수집된 데이터 처리 ##
data_dic = {'Date':'-', 'Time':'-', 'Product': '-', 'Temperature':'-', 'Vibration':'-', 'Information': information}        
time_list = []
temp_list = []
vib_list = []

global s_cnt
s_cnt = 0
def save_all_data():
    #save log data as CSV
    global data_dic, i_flag, s_cnt, information
    get_ip()
    day = time.strftime('%Y-%m-%d',time.localtime(time.time()))
    log_path = f'{now_dir}/log/{day}server.csv'
    if i_flag:
        df = pd.DataFrame([data_dic])
        if not os.path.exists(log_path):
            df.to_csv(log_path, index=False, header = True)
        else:
            os.system(f'sudo chmod 777 {log_path}')
            if s_cnt == 0:
                data_ = pd.read_csv(log_path)
                data_.dropna(axis = 0)
                data_.to_csv(log_path, index=False, header = True)
                s_cnt = 1
            df.to_csv(log_path, mode='a', index=False, header = False)
            
        time_list.append(str(datetime.datetime.now().strftime('%H:%M:%S')))
        temp_list.append(data_dic['Temperature'])
        vib_list.append(data_dic['Vibration'])
        if len(time_list) > 60:
            time_list.pop(0)
            temp_list.pop(0)
            vib_list.pop(0)
    else:
        if data_dic['Information'] != '-':
            data_dic['Date'] = '-'
            data_dic['Time'] = '-'
            df = pd.DataFrame([data_dic])
            df.to_csv(log_path, mode='a', index=False, header = False)
    information = '-'
        
# run schedule
schedule.every(1).seconds.do(run_lcd)
schedule.every(1).seconds.do(save_all_data)
schedule.every(12).hours.do(delete_old_data)

#declare Flask Server
app = Flask(__name__)

global d_cnt
d_cnt = 0
global wt_flag, wv_flag

def captureData():
    while True:
        global information
        global data_dic, d_cnt, config_data
        global vib_flag, temp_flag
        global wt_flag, wv_flag
        time_ymd=str(datetime.datetime.now().strftime('%Y-%m-%d'))
        time_hms=str(datetime.datetime.now().strftime('%H:%M:%S.%f'))
        
        # run only in the first loop
        if d_cnt == 0:
            VibV = 0.0; temp = 0.0;
            d_cnt += 1
            if information != '-':
                save_all_data()
        
        #warning temperature, warning vibration
        wt_flag = False
        wv_flag = False
        w_temp = config_data['w_temp']
        w_vib = config_data['w_vib']
        
        #Capture Data
        if vib_flag:
            try:
                VibV= V0.value /(pow(2,15)/10000)
                if VibV > w_vib:
                    modify_inform('high Vibration')
                    wv_flag = True
            except:
                modify_inform('Vibration sensor is not working')
                vib_flag = False
                VibV = '-'
                
        if temp_flag:
            try:
                temp = round(mlx.object_temperature, 2)
                if temp > w_temp:
                    modify_inform('high Temperature')
                    wt_flag = True
            except:
                modify_inform('Temperature sensor is not working')
                temp_flag = False
                temp = '-'
        if wv_flag or wt_flag:
            data_dic = {'Date':time_ymd, 'Time':time_hms, 'Product':product_number, 'Temperature':temp, 'Vibration':VibV, 'Information': information}
            save_all_data()
            run_lcd()
        
        #save All data as dictionary                
        data_dic = {'Date':time_ymd, 'Time':time_hms, 'Product':product_number, 'Temperature':temp, 'Vibration':VibV, 'Information': information}
        schedule.run_pending()
    
def captureFrames():
    global video_frame, thread_lock
    
    # Video capturing
    cap = cv2.VideoCapture(-1)   
    
    # Set Video Size
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, img_w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, img_h)
    
    # Time measurement
    prev_time = 0
    FPS_list = []
    while True:
        global check, c_cnt
        global information
        global data_dic
        global vib_flag, temp_flag
        
        time_now=str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        ret, frame = cap.read()
        
        if not ret:
            frame = n_img
            cv2.putText(frame,'Camera is not detected!',(center_x-200, center_y),font,2,white,thickness,cv2.LINE_AA)
            if c_cnt == 0:
                modify_inform('Camera is not detected!')
                data_dic['Information'] = information
                save_all_data()
                c_cnt += 1
 
        #filter
        if vib_flag:
             VibV=data_dic['Vibration']
             cv2.putText(frame,'Vibration',L_VibT,font,fontscale,black,thickness,cv2.LINE_AA)
             cv2.putText(frame,str(round(VibV,2)),L_Vib,font,fontscale,black,thickness,cv2.LINE_AA)
                
             cv2.putText(frame,'Vibration',L_VibT,font,fontscale,white,thickness-1,cv2.LINE_AA)
             cv2.putText(frame,str(round(VibV,2)),L_Vib,font,fontscale,white,thickness-1,cv2.LINE_AA)
                
        if temp_flag:
            temp = data_dic['Temperature']
            cv2.putText(frame,'Temperature',L_tempT,font,fontscale,black,thickness,cv2.LINE_AA)
            cv2.putText(frame,str(temp)+"'C",L_temp,font,fontscale,black,thickness,cv2.LINE_AA)
          
            cv2.putText(frame,'Temperature',L_tempT,font,fontscale,white,thickness-1,cv2.LINE_AA)
            cv2.putText(frame,str(temp)+"'C",L_temp,font,fontscale,white,thickness-1,cv2.LINE_AA)
                
        if product_number > 0:
            cv2.putText(frame,'Production: ',L_countT,font,fontscale,black,thickness,cv2.LINE_AA)
            cv2.putText(frame,str(product_number),L_count,font,fontscale,black,thickness,cv2.LINE_AA)
            
            cv2.putText(frame,'Production: ',L_countT,font,fontscale,white,thickness-1,cv2.LINE_AA)
            cv2.putText(frame,str(product_number),L_count,font,fontscale,white,thickness-1,cv2.LINE_AA)
        
        cv2.putText(frame,time_now,L_time,font,fontscale,black,thickness,cv2.LINE_AA)
        cv2.putText(frame,time_now,L_time,font,fontscale,white,thickness-1,cv2.LINE_AA)
        
        #warning
        global n, config_data
        w_temp = config_data['w_temp']
        w_vib = config_data['w_vib']
        
        # modify warning video
        if vib_flag or temp_flag:
            if vib_flag and temp_flag and temp>w_temp and VibV>w_vib and n%5==0:
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
        '''
        # calculate time interval for measuring FPS
        cur_time = time.time()
        diff = cur_time - prev_time
        prev_time = cur_time
        fps = round(1/diff,2)
        FPS_list.append(fps)
        if len(FPS_list) > 30:
            FPS_list.pop(0)
        M_FPS = round(sum(FPS_list)/len(FPS_list),2)
        cv2.putText(frame,'FPS: ',L_FPST,font,fontscale,black,thickness,cv2.LINE_AA)
        cv2.putText(frame,str(M_FPS),L_FPS,font,fontscale,black,thickness,cv2.LINE_AA)
            
        cv2.putText(frame,'FPS: ',L_FPST,font,fontscale,white,thickness-1,cv2.LINE_AA)
        cv2.putText(frame,str(M_FPS),L_FPS,font,fontscale,white,thickness-1,cv2.LINE_AA)
        print(FPS_list)
        '''
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

@app.route('/data', methods=["GET", "POST"])
def data_info():
    global data_dic
    global time_list, temp_list, vib_list
    time = data_dic['Time'].split('.')[0]
    return jsonify({'time':time, 'time_list':time_list,'info':data_dic['Information'], 'temp_list':temp_list, 'vib_list':vib_list})

@app.route('/temp_graph')
def temp_graph():
    return render_template('temp_graph.html')

@app.route('/vib_graph')
def vib_graph():
    return render_template('vib_graph.html')

@app.route('/')
def index():
    return render_template('index.html', ipaddr = ipaddr)

# open log file in the web
search_date = 0
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

    # Capature Data thread
    data_thread = threading.Thread(target=captureData)
    data_thread.daemon = True
    
    # buzzer Thread
    buzz_thread = threading.Thread(target=buzz_loop)
    buzz_thread.daemon = True
    
    # Start the thread
    process_thread.start()
    data_thread.start()
    buzz_thread.start()
    
    
    # start the Flask Web Application
    # While it can be run on any feasible IP, IP = 0.0.0.0 renders the web app on
    # the host machine's localhost and is discoverable by other machines on the same network 
    app.run(host="0.0.0.0", port="8080")
