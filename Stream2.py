#ver. 1.0.1

#해당 방법은 mjpg streamer로 송출되는 필터 미적용 영상을 웹에서(포트번호: 8000) 
#python으로 가져와 필터를 적용하여 다른 포트로(8080) 송출하는 방법임

import cv2
import time
import threading
from flask import Response, Flask, render_template, stream_with_context
import numpy as np
import datetime
import math
import time
import logging
import RPi.GPIO as GPIO

#initial value
img_w = 640
img_h = 480
GAIN = 1
GPIO.setmode(GPIO.BCM)
product_number = 0

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

#text
thickness =2
font=cv2.FONT_HERSHEY_PLAIN
fontscale =1

#declare Flask Server
app = Flask(__name__)

def captureFrames():
    global video_frame, thread_lock

    # Video capturing
    cap = cv2.VideoCapture(0)

    # Set Video Size
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, img_w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, img_h)
    
    while True and cap.isOpened():
        ret, frame = cap.read()
        
        if not ret:
            '''camera is not detected'''
            break
        
        #filter
        time=str(datetime.datetime.now())
        cv2.putText(frame,time,L_time,font,fontscale,white,thickness)
        cv2.putText(frame,'Production: ',L_countT,font,fontscale,white,thickness)
        cv2.putText(frame,str(product_number),L_count,font,fontscale,white,thickness)
        
        #encoding
        return_key, encoded_image = cv2.imencode(".jpg", frame)
        if not return_key:
            continue
        
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encoded_image) + b'\r\n')
            
@app.route('/video')
def streamFrames():
    return Response(captureFrames(), mimetype = "multipart/x-mixed-replace; boundary=frame")

@app.route('/')
def index():
    return render_template('index.html')

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
