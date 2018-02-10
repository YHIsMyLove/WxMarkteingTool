
from flask import Response, Flask
from flask import render_template, jsonify
import base64,shutil,os


# from wxpy import *
app = Flask(__name__)

# clear file
with open('./info.txt','w+') as f:
    f.truncate()
# 
shutil.rmtree('./static/images')
os.mkdir('./static/images')  


@app.route("/")
def index():
    return render_template('index.html')

@app.route("/qr")
def getqr():
    with open('./info.txt', 'r') as f:
        paths = f.read()
        path = paths.split()[0]
    return path

app.run(host='127.0.0.1',port=80)
