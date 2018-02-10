
from flask import Response, Flask
from flask import render_template, jsonify
import base64

# from wxpy import *
app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html')

@app.route("/qr")
def getqr():
    with open('./info.txt', 'r') as f:
        paths = f.read()
        path = paths.split()[0]
    return path

app.run(host='172.17.0.10',port=80)
