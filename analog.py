# Importing modules
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, time, requests, json, smtplib, urllib.request
import spidev # To communicate with SPI devices
from numpy import interp	# To scale values
from time import sleep	# To add delay
import RPi.GPIO as GPIO	# To use GPIO pins

# Start SPI connection
spi = spidev.SpiDev() # Created an object
spi.open(0,0)	

# Initializing LED pin as OUTPUT pin
led_pin = 20
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(led_pin, GPIO.OUT)
GPIO.setup(18,GPIO.OUT)

def getserial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line[0:6]=='Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"
    return cpuserial
myserial = getserial()

# Creating a PWM channel at 100Hz frequency
pwm = GPIO.PWM(led_pin, 100)
pwm.start(0) 

# Read MCP3008 data
def analogInput(channel):
    spi.max_speed_hz = 1350000
    adc = spi.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data

time.sleep(60)
newpumpstatus = "off"
pumpstatus = "off"

loopcounter = 0
while True:
    
    print ('pumpstatus {}'.format(pumpstatus))
    print ('newpumpstatus {}'.format(newpumpstatus))
    if loopcounter > 599:
        loopcounter = 0
        r = requests.post("http://microdata.website/sensoradd.php", data={'tankVolume': round(output*10)/10, 'hum1': 88, 'deviceID': myserial})
		
        if pumpstatus != newpumpstatus:
		    # Gmail Sign In
            gmail_sender = 'malcolmkinross@gmail.com '
            gmail_passwd = 'Cabon1c68!*#'
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.login(gmail_sender, gmail_passwd)
            TO = 'malcolm@dulcamara.co.uk'
            #TEXT = 'The pump has been switched off or on.'
            TEXT  = 'The pump has been switched {}'.format(pumpstatus)
            # The code below was copied from a tutorial and uses old school '%' formating, but it still seems to work. See here for explanation https://matthew-brett.github.io/teaching/string_formatting.html
            BODY = '\r\n'.join(['To: %s' % TO,
                    'From: %s' % gmail_sender,
                    'Subject: %s' % myserial,
                    '', TEXT])
            try:
                server.sendmail(gmail_sender, [TO], BODY)
                print ('email sent')
            except:
                print ('error sending mail')
            server.quit()
            newpumpstatus = pumpstatus
    loopcounter = loopcounter + 1
    output = analogInput(0) # Reading from CH0
    #thing = analogInput(0) # Reading from CH0
    #print(thing)
    # The line below converts the signal from the output of the sensor into a range fror 0 to 100
    output = interp(output, [600, 800], [0, 100])
    # Convert output to volute of water in reservoir, which is (output/4.93) + 18
    output = (output/4.93) + 18
    print(output)
    print(" count = ")
    print(loopcounter)
    print(" deviceID = ")
    print(myserial)
    # The line below determines the threshold in the 0 to 100 range that will turn on the pump
    if output > 20:
        GPIO.output(18,GPIO.HIGH)
        print("pump on")
        pumpstatus = "on"
    else:
        GPIO.output(18,GPIO.LOW)
        print("pump off")
        pumpstatus = "off"
		
    pwm.ChangeDutyCycle(output)
	# Below is the time interval in seconds between each sensor reading
    sleep(1.0)

	