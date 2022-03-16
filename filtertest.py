
import cv2
import numpy as np
import datetime
import RPi.GPIO as GPIO
import Adafruit_ADS1x15
import math
import time
import logging

logger1=logging.getLogger()
logger2=logging.getLogger()

logger1.setLevel(logging.INFO)
logger2.setLevel(logging.INFO)

formatter1 = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
formatter2 = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')



GAIN = 1
adc = Adafruit_ADS1x15.ADS1115()
GPIO.setmode(GPIO.BCM)
product_number=0
n=0
img_w = 640
img_h = 480
img2=np.zeros((img_h,img_w,3),np.uint8)
img3=np.zeros((img_h,img_w,3),np.uint8)
check=0
timeC=0
checkR=0

stream_handler1=logging.StreamHandler()
stream_handler2=logging.StreamHandler()
stream_handler1.setFormatter(formatter1)
stream_handler2.setFormatter(formatter2)
logger1.addHandler(stream_handler1)
logger2.addHandler(stream_handler2)

day=time.strftime('%Y-%m-%d',time.localtime(time.time()))    
file_handler1=logging.FileHandler(f'log/{day}server.log')
file_handler2=logging.FileHandler(f'log/server.log')
file_handler1.setFormatter(formatter1)
file_handler2.setFormatter(formatter2)
logger1.addHandler(file_handler1)
logger2.addHandler(file_handler2)
    

def add_product(channel):
    global product_number
    product_number+=1
    logger1.info(f'Proudction : {product_number}')
    logger2.info(f'Proudction : {product_number}')

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


GPIO.setup(12,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(12,GPIO.FALLING, callback=add_product,bouncetime=1000)
GPIO.setup(5,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(5,GPIO.FALLING, callback=count_RPM)
        
class MyFilter:
    
    def process(self, img):
        '''
            :param img: A numpy array representing the input image
            :returns: A numpy array to send to the mjpg-streamer output plugin
        '''

        #bpp = 3
        values = [0]*4
        #img = np.zeros((img_h,img_w,bpp),np.uint8)
        
        red=(0,0,255)
        green=(0,255,0)
        blue=(255,0,0)
        white=(255,255,255)
        yellow=(0,255,255)
        cyan=(255,255,0)
        magenta=(255,0,255)

        values[0] = adc.read_adc(0, gain=GAIN)
        values[1] = adc.read_adc(1,gain=GAIN)

        tempR=1000/(1-(values[0])/(26555))
        temp=706.6*(tempR**(-0.1541))-146
        temp=round(temp,1)
        VibV=values[1]/26555*3.3
        VibV=round(abs(0.58-round(VibV,2)),2)
        
#        TEST check
        
        global check
        if check==0:
            for i in range(0,img_h-1):
                for j in range(0,img_w-1):
                    img2[i,j,0]=60
                    img2[i,j,1]=60
                    img2[i,j,2]=255
        
        if check==0:
            for i in range(0,img_h-1):
                for j in range(0,img_w-1):
                    img3[i,j,0]=60
                    img3[i,j,1]=60
                    img3[i,j,2]=60      
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

        thickness=2
        count_number=str("""number of product = 56     RPM=2000         Temperature=36'C""")
        for i in range(4):
        # Read the specified ADC channel using the previously set gain value.
            values[i] = adc.read_adc(i, gain=GAIN)

        time=str(datetime.datetime.now())
        font=cv2.FONT_HERSHEY_PLAIN
        fontscale = 1
        cv2.putText(img,time,L_time,font,fontscale,white,thickness)
        cv2.putText(img,'Production',L_countT,font,fontscale,white,thickness)
        cv2.putText(img,str(product_number),L_count,font,fontscale,white,thickness)
        cv2.putText(img,'Temperature',L_tempT,font,fontscale,white,thickness)
        cv2.putText(img,str(temp),L_temp,font,fontscale,white,thickness)
        cv2.putText(img,'RPM',L_RPMT,font,fontscale,white,thickness)
        if checkR==0:
            cv2.putText(img,'0',L_RPM,font,fontscale,white,thickness)
        else:
            cv2.putText(img,str(RPM),L_RPM,font,fontscale,white,thickness)
        
            
        cv2.putText(img,'Vibration',L_VibT,font,fontscale,white,thickness)
        cv2.putText(img,str(VibV),L_Vib,font,fontscale,white,thickness)
        #cv2.imshow("drawing",img)
        #cv2.waitKey(0)

        
        global n
        
        if temp>50 and n%5==0:
        
           n=n+1
           check=check+1
           logger1.warning('Too high Temp')
           logger2.warning('Too high Temp')
           return img2
        elif VibV>0.5 and n%5==1:
            n=n+1
            check=check+1
            logger1.warning('Too high Vibration')
            logger2.warning('Too high Vibration')
            return img3
        else :
            check=check+1
            n=n+1
            if n%100==0:
                logger1.info(f'Temp : {temp} RPM : {RPM}')
                logger2.info(f'Temp : {temp} RPM : {RPM}')
            return img

        
def init_filter():
    '''
        This function is called after the filter moduleed. It MUST
        return a callable object (such as a function or bound method). 
    '''
    f = MyFilter()
    return f.process


