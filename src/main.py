from flask_socketio import SocketIO

from flask import Flask, render_template

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def hello_world():
    return render_template('home.html')

if __name__ == '__main__':
    socketio.run(app=app, debug=True, host= '192.168.1.154')
