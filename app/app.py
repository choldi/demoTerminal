import os
import time
import datetime
import hashlib
from flask import Flask, render_template, Response, request
from flask_jsonrpc import JSONRPC
from flask_jsonrpc.exceptions import InvalidParamsError
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column
import Model
# init SQLAlchemy so we can use it later in our models

app = Flask(__name__)

# configure the SQLite database, relative to the app instance folder
db_dir = "./instance/project.db"
database="sqlite:///" + os.path.abspath(db_dir)
app.config["SQLALCHEMY_DATABASE_URI"] = database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# initialize the app with the extension
db=Model.db


db.init_app(app)
with app.app_context():
   from modules.user import User
   from modules.session import Session

jsonrpc = JSONRPC(app, "/api", enable_web_browsable_api=True)

@app.route('/')
def hello():
    return render_template('index.html', utc_dt=datetime.datetime.utcnow())

@app.route('/terminal/')
def terminal():
    return render_template('terminal.html')

@app.route('/about/')
def about():
    return render_template('about.html')

@jsonrpc.method("App.index")
def index() -> str:
    return "Welcome to Flask JSON-RPC"

@jsonrpc.method("login")
def login(*argv:str) -> str:
    if len(argv) != 2:
       raise InvalidParamsError(data={'message': 'Incorrect number of params'}) 
   # users = db.session.execute(db.select(User).order_by(User.username)).scalars()
    usr=argv[0]
    pwd=argv[1]
    exists = db.session.query(User.email).filter_by(username=usr,password=pwd).first() is not None
    millis=round(time.time() * 1000)
    s=f"{usr}:{pwd}:{millis}"
    res = hashlib.md5(s.encode('utf-8'))
    print (res.hexdigest())
    if exists:
        return res.hexdigest()
    else:
        raise InvalidParamsError(data={'message': 'User Not allowed'})

@jsonrpc.method("help")
def help(*argv:str) -> str:
    r=request.get_json()
    if len(argv) == 0:
       return "This is help"
    else:
       raise InvalidParamsError(data={'message': 'Incorrect number of params'}) 


@app.route("/", methods=["POST"])
def index():
    print(request.get_data().decode())
    data=request.get_data().decode()
    d=dispatch(request.get_data().decode())
    return Response(
        d, content_type="application/json"
    )


if __name__ == '__main__':
  print(__name__)   # I add two more lines here
  print("ok")
  app.run(host='0.0.0.0')
