from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect    
import time
import random
import math
import serial

async_mode = None

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock() 
ser = serial.Serial("/dev/ttyS1",9600)    #priame citanie z mobilu
ser.baudrate=9600                         #priame citanie z mobilu

def background_thread(args):
    count = 0
    y="0"
    vstup = [0]*30
    while True:
        socketio.sleep(1)
        count += 1
        y = dict(args).get('start')
        read_ser=ser.readline()   #priame citanie z mobilu
        vstup = read_ser.split(',')
        print(read_ser)           #priame citanie z mobilu
        #print(vstup[1])
        fo = open("data.txt","a+")   #zapis nacitavanych dat z mobilu do suboru
        fo.write("%s\r\n" %read_ser) #zapis nacitavanych dat z mobilu do suboru
        if y =="1":
            socketio.emit('my_response',{'data': read_ser,'count': count},namespace='/test')
            #socketio.emit('my_response2',{'data': vstup[0],'data': vstup[1],'data': vstup[2], 'count': count},namespace='/test')

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
    emit('my_response', {'data': 'Pripojene', 'count': 0})

@socketio.on('start', namespace='/test')
def db_message(message):   
    session['start'] = message['value']
    
@socketio.on('stop', namespace='/test')
def db_message(message):   
    session['start'] = message['value']

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80, debug=True)