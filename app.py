from flask import Flask,render_template,url_for,request
import pandas as pd 
import pickle
import numpy as np
import warnings
import joblib
import sqlite3
import imutils
import time
import cv2
from flask import Flask, render_template, Response

app = Flask(__name__)


@app.route('/')
def home():
	return render_template('home.html')

@app.route("/signup")
def signup():
    
    
    name = request.args.get('username','')
    number = request.args.get('number','')
    email = request.args.get('email','')
    password = request.args.get('psw','')

    con = sqlite3.connect('signup.db')
    cur = con.cursor()
    cur.execute("insert into `detail` (name,number,email, password) VALUES (?, ?, ?, ?)",(name,number,email,password))
    con.commit()
    con.close()

    return render_template("signin.html")

@app.route("/signin")
def signin():

    mail1 = request.args.get('name','')
    password1 = request.args.get('psw','')
    con = sqlite3.connect('signup.db')
    cur = con.cursor()
    cur.execute("select `name`,`password` from detail where name = ? and password = ?",(mail1,password1,))
    data = cur.fetchone()
    print(data)

    if data == None:
        return ("invalid credentials")   

    elif mail1 == 'admin' and password1 == 'admin':
        return render_template("index.html")

    elif mail1 == str(data[0]) and password1 == str(data[1]):
        return render_template("index.html")
    else:
        return render_template("signup.html")

@app.route('/logon')
def logon():
	return render_template('signup.html')

@app.route('/login')
def login():
	return render_template('signin.html')


@app.route('/index')
def index():
    """Video streaming home page."""
    return render_template('index.html')

def find_max(k):
    d = {}
    maximum = ( '', 0 ) # (occurring element, occurrences)
    for n in k:
        if n in d: 
            d[n] += 1
        else: 
            d[n] = 1

        # Keep track of maximum on the go
        if d[n] > maximum[1]: 
            maximum = (n,d[n])

    return maximum

def gen():
    """Video streaming generator function."""
    cap = cv2.VideoCapture(0) #replace video.mp4 by the address of the video you want to play or replace with 0
    avg = None
    xvalues = list()
    motion = list()
    count1 = 0
    count2 = 0

    
    # Read until video is completed
    while cap.isOpened():
        ret, frame = cap.read()
        flag = True
        frame = imutils.resize(frame, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
    
        if avg is None:
            avg = gray.copy().astype("float")
            continue
    
        cv2.accumulateWeighted(gray, avg, 0.5)
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
        thresh = cv2.threshold(frameDelta, 2, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        (cnts,_) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for c in cnts:
            if cv2.contourArea(c) < 5000:
                continue
            (x, y, w, h) = cv2.boundingRect(c)
            xvalues.append(x)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            flag = False
    	
        no_x = len(xvalues)
        
        if (no_x > 2):
            difference = xvalues[no_x - 1] - xvalues[no_x - 2]
            if(difference > 0):
                motion.append(1)
            else:
                motion.append(0)
    
        if flag is True:
            if no_x > 5:
                val, times = find_max(motion)
                if val == 1 and times >= 15:
                    count1 += 1
                else:
                    count2 += 1
                    
            xvalues = list()
            motion = list()
        
        cv2.line(frame, (260, 0), (260,480), (0,255,0), 2)
        cv2.line(frame, (420, 0), (420,480), (0,255,0), 2)	
        cv2.putText(frame, "In: {}".format(count1), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, "Out: {}".format(count2), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.imshow("Frame",frame)
        
        frame = cv2.imencode('.jpg', frame)[1].tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    #time.sleep(0.1)
    


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
	app.run(debug=True)
