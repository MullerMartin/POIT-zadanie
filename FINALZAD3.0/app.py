from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect    
import time
import random
import math
import serial
import MySQLdb       
import ConfigParser

async_mode = None

app = Flask(__name__)

config = ConfigParser.ConfigParser()
config.read('config.cfg')
myhost = config.get('mysqlDB', 'host')
myuser = config.get('mysqlDB', 'user')
mypasswd = config.get('mysqlDB', 'passwd')
mydb = config.get('mysqlDB', 'db')

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock() 

def background_thread(args):
    count = 0
    dataCounter=0
    y="0"
    op="0"       
    vstup = [0]*30
    dataList = []
    db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb) 
    while True:   
        if args:
          A = dict(args).get('A')
          dbV = dict(args).get('db_value')
        else:
          A = 1
          dbV = 'nieco'
          
        socketio.sleep(0.3)
        count += 1
        dataCounter +=1
        y = dict(args).get('start')
        op = dict(args).get('open')
        if op == "1":
            ser = serial.Serial("/dev/ttyS1",9600)    #priame citanie z mobilu
            ser.baudrate=9600                         #priame citanie z mobilu
            read_ser=ser.readline()
            vstup = read_ser.split(',')
            print(read_ser)
            #print(float(A))
            fo = open("data.txt","a+")   #zapis nacitavanych dat z mobilu do suboru
            fo.write("%s\r\n" %read_ser) #zapis nacitavanych dat z mobilu do suboru
            
        #databaza
        if dbV == 'start':
          dataList.append(read_ser)
        else:
          if len(dataList)>0:
            #print (str(dataList))
            #fuj = str(dataList).replace("'", "\"")
            #print fuj
            cursor = db.cursor()
            cursor.execute("SELECT MAX(id) FROM MobilneData")
            maxid = cursor.fetchone()
            cursor.execute("INSERT INTO MobilneData (id, hodnoty) VALUES (%s, %s)", (maxid[0] + 1, read_ser))
            db.commit()
          dataList = []
          dataCounter = 0
          
        #databaza
        
        if y =="1":
            socketio.emit('my_response',{'data': read_ser,'count': count},namespace='/test')
            #socketio.emit('my_response2',{'data': vstup[0],'data': vstup[1],'data': vstup[2], 'count': count},namespace='/test')
    db.close()
    
@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)
  
@socketio.on('my_event', namespace='/test')
def test_message(message):   
    session['receive_count'] = session.get('receive_count', 0) + 1 
    session['A'] = message['value']    
    emit('my_response',
         {'data': message['value'], 'count': session['receive_count']})
 
@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Pripojenie bolo prerusene', 'count': session['receive_count']})
    disconnect()

@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread, args=session._get_current_object())
    #emit('my_response', {'data': 'Pripojene', 'count': 0})

@socketio.on('open', namespace='/test')
def db_message(message):   
    session['open'] = message['value']

@socketio.on('start', namespace='/test')
def db_message(message):   
    session['start'] = message['value']
    
@socketio.on('stop', namespace='/test')
def db_message(message):   
    session['start'] = message['value']

@socketio.on('db_event', namespace='/test')
def db_message(message):   
#    session['receive_count'] = session.get('receive_count', 0) + 1 
    session['db_value'] = message['value']    
#    emit('my_response',
#         {'data': message['value'], 'count': session['receive_count']})

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80, debug=True)