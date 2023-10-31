import os
import time
from datetime import datetime
import argparse
import hashlib
import yaml
from typing import Any
from flask import Flask, render_template, Response, request
from flask_jsonrpc import JSONRPC
from flask_jsonrpc.exceptions import InvalidParamsError,InvalidRequestError
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import desc
import Model
import logging
from Log import init_log
from QPElem import QPElem, TorrentElements
from Prowlarr import Prowlarr
from rd import RealDebrid as RD

rd:RD
pr:Prowlarr

SECONDS_FOR_INACTIVE_SESSION=300
MAX_QUERIES_FOR_SESSION=5
# init SQLAlchemy so we can use it later in our models

app = Flask(__name__)

# configure the SQLite database, relative to the app instance folder
db_dir = "./app/instance/project.db"
database="sqlite:///" + os.path.abspath(db_dir)
app.config["SQLALCHEMY_DATABASE_URI"] = database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# initialize the app with the extension
db=Model.db


db.init_app(app)
with app.app_context():
   from models.user import User
   from models.session import Session
   from models.search import Search
   from models.result import Result

jsonrpc = JSONRPC(app, "/api", enable_web_browsable_api=True)

def validateSession(token):
    session = db.session.query(Session).filter_by(token=token).first()
    if (session is None):
     raise InvalidRequestError(data={'message':'Session not found'})
    last = session.last_command
    print(f"last:{last}")
    now = datetime.utcnow()
    differ = now - last
    if differ.total_seconds() > SECONDS_FOR_INACTIVE_SESSION:
        #get searches from session
        searches=db.session.query(Search.id).filter(Search.id==session.id)
        results=db.session.query(Result).filter(Result.search_id.in_(searches))
        #to do :cascade deleting (manually?)
        results.delete()
        db.session.query(Search).filter(Search.id.in_(searches)).delete()
        db.session.query(Session).filter(Session.id==session.id).delete()
        raise InvalidRequestError(data={'message':'Session expired'})
    session.last_command=now 
    db.session.commit()
    return session.id


@app.route('/')
def hello():
    return render_template('index.html', utc_dt=datetime.utcnow())

@app.route('/terminal/')
def terminal():
    return render_template('terminal.html')

@app.route('/about/')
def about():
    return render_template('about.html')

@jsonrpc.method("App.index")
def index() -> str:
    return "Welcome to Flask JSON-RPC"

@jsonrpc.method("ls")
def ls(*argV:str) -> str:
    token=argV[0]
    validateSession(token)
    return "Welcome to Flask JSON-RPC"

@jsonrpc.method("login")
def login(*argv:str) -> str:
    if len(argv) != 2:
       raise InvalidParamsError(data={'message': 'Incorrect number of params'}) 
   # users = db.session.execute(db.select(User).order_by(User.username)).scalars()
    usr=argv[0]
    pwd=argv[1]
    user = db.session.query(User.id).filter_by(username=usr,password=pwd).first() 
    exists = user is not None
    millis=round(time.time() * 1000)
    s=f"{usr}:{pwd}:{millis}"
    res = hashlib.md5(s.encode('utf-8'))
    resHex = res.hexdigest()
    print (resHex)
    if exists:
        session = Session(user_id=user.id,token=resHex,last_command=datetime.utcnow())
        db.session.add(session)
        db.session.commit()
        return resHex
    else:
        raise InvalidParamsError(data={'message': 'User Not allowed'})

@jsonrpc.method("search")
def search(*argv:Any) -> str:
    token=argv[0]
    session_id=validateSession(token)
    logger.debug("session validated")
    if len(argv) < 2:
       return 'Incorrect number of params'
   # users = db.session.execute(db.select(User).order_by(User.username)).scalars()
    res=""
    q=' '.join(map(str,argv[1:]))
    '''
    nums = db.session.query(Search).filter_by(session_id=session_id).order_by(Search.id)
    n=nums.with_entities(func.count()).scalar()
    if n>MAX_QUERIES_FOR_SESSION:
        first_search_id=nums.first().id
        db.session.query(Search).filter(Search.id==first_search_id).delete()
        db.session.commit()
        res+="Deleted old session number {first_search_id}"
    '''
    nums = db.session.query(Search).filter_by(session_id=session_id)
    if nums.count()==0:
        pass
    elif nums.count()==1:
        db.session.query(Result).filter_by(search_id=nums.first().id).delete()
        nums.delete()
        db.session.commit()

    te=pr.search(q)
    te=te.with_min_seeders(1).sort_by("sortTitle")
    s=te.to_str()
    if len(te)>0:
        sea=Search(session_id=session_id)
        db.session.add(sea)
        db.session.commit()
        db.session.refresh(sea)
        res+=f"Search result num {sea.id} \n"
        i=0
        for t in te:
            resdb=Result(search_id=sea.id,elem=t)
            resdb.picknumber=i
            db.session.add(resdb)
            res+=f"{i}:{t.cat} - {t.title} - {t.seeders}\n"
            i+=1
        db.session.commit()
        return res
    return f"No results for {q}\n"

@jsonrpc.method("filter")
def filter(*argv:Any) -> str:
    token=argv[0]
    session_id=validateSession(token)
    logger.debug("session validated")
    msg="Format for filter: \n"
    msg+="filter cat nnn -> filter category containing nnn\n"
    msg+="filter seeders n -> filter with minimum n seeders\n"
    msg+="filter name mmmm -> filter by name mmmm\n"
    if len(argv) < 3:
       return msg
    command=argv[1]
    opt=str(argv[2])
    if not (command=="cat" or command=="seeders" or command=="name"):
        return msg
    
    search = db.session.query(Search).filter_by(session_id=session_id).order_by(Search.search_date).first()
    if (search is None):
        return "No active query"
    results = db.session.query(Result).filter_by(search_id=search.id)
    if (results.first() is None):
        return "No results stored"
    res=""
    if (command=="seeders"):
        if opt.isnumeric():
            minS=int(opt)  
            filtered=results.filter(Result.seeders>=minS)
        else:
            return f"filter seeders has to be numeric. {opt} is not"
    if (command=="cat"):
        opt=f"%{opt.lower()}%"
        filtered=results.filter(func.lower(Result.category).like(opt))
    if (command=="name"):
        opt=f"%{opt.lower()}%"
        filtered=results.filter(func.lower(Result.title).like(opt))

   # users = db.session.execute(db.select(User).order_by(User.username)).scalars()
    if filtered.count()>0:
        te=TorrentElements()
        for f in filtered:
            te.append(f.toQPElem)
            res+=f"{f.picknumber}:{f.category} - {f.title} - {f.seeders}\n"
        return res
    return f"No results for filer {command} {opt}\n"


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
  logger=init_log(lname="Terminal")
  parser = argparse.ArgumentParser()
  parser.add_argument("--config", "-c", default="config.yml")
  args=parser.parse_args()
  config=args.config
  try:
    with open(config) as f:
      cfg=yaml.safe_load(f)
  except Exception as e:
    logger.error(f"config error:{e} ")
    exit()
  
  logger.debug("init qp main")
    
  try:
     rd_apikey=cfg['realdebrid']['api']
     pr_apikey=cfg['prowlarr']['api']
     pr_url=cfg['prowlarr']['url']
  except Exception as e:
     logger.error(f"Not required parameters in {config} file")
     exit()

  rd = RD(rd_apikey)
  logger.debug("created rd instance")
  pr = Prowlarr(pr_apikey,pr_url)
  logger.debug("created pr instance")


  print("ok")
  app.run(host='0.0.0.0')
