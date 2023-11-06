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
from sqlalchemy import update,desc,and_
import Model
import logging
from Log import init_log
from QPElem import QPElem, TorrentElements
from Prowlarr import Prowlarr
from rd import RealDebrid as RD, File 

rd:RD
pr:Prowlarr


class ArgumentParser(argparse.ArgumentParser):

    def error(self, message):
        raise Exception(message) 

SECONDS_FOR_INACTIVE_SESSION=300
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
   from models.collected import Collected
   from models.added import Added

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
    rd.download_link=f"./downloads/user/{session.user_id}/"
    return session


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
    if exists:
        session = Session(user_id=user.id,token=resHex,last_command=datetime.utcnow())
        db.session.add(session)
        db.session.commit()
    else:
        raise InvalidParamsError(data={'message': 'User Not allowed'})
    return resHex

@jsonrpc.method("search")
def search(*argv:Any) -> str:
    token=argv[0]
    session=validateSession(token)
    session_id=session.id
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
    session=validateSession(token)
    session_id=session.id
    logger.debug("session validated")
    msg="Format for filter: \n"
    msg+="filter cat nnn -> filter category containing nnn\n"
    msg+="filter seeders n -> filter with minimum n seeders\n"
    msg+="filter name mmmm -> filter by name mmmm\n"
    if len(argv) < 3:
       return msg
    command=argv[1]
    
    parser=ArgumentParser()
    parser.add_argument("-name",nargs="+")
    parser.add_argument("-seeders",type=int)
    parser.add_argument("-cat",nargs=1)
    q=' '.join(map(str,argv[1:]))
    try:
        args=parser.parse_args(q.split())
    except Exception as e:
        return str(e)
    
    if not (args.cat or args.seeders or args.name):
        return msg
    
    search = db.session.query(Search).filter_by(session_id=session_id).order_by(Search.search_date).first()
    if (search is None):
        return "No active query"
    filtered = db.session.query(Result).filter_by(search_id=search.id)
    if (filtered.first() is None):
        return "No results stored"
    res=""
    if (args.seeders):
        minS=args.seeders  
        filtered=filtered.filter(Result.seeders>=minS)
    if (args.cat):
        opt=f"%{args.cat[0].lower()}%"
        filtered=filtered.filter(func.lower(Result.category).like(opt))
    if (args.name):
        opt=" ".join(args.name).lower()
        opt=f"%{opt}%"
        filtered=filtered.filter(func.lower(Result.title).like(opt))

   # users = db.session.execute(db.select(User).order_by(User.username)).scalars()
    if filtered.count()>0:
        te=TorrentElements()
        for f in filtered:
            te.append(f.toQPElem)
            res+=f"{f.picknumber}:{f.category} - {f.title} - {f.seeders}\n"
        return res
    return f"No results for filer {command} {opt}\n"

@jsonrpc.method("select")
def select(*argv:Any) -> str:
    token=argv[0]
    session=validateSession(token)
    session_id=session.id
    logger.debug("session validated")
    if len(argv) < 2:
       return "Need to select"
    number=argv[1]
    if not isinstance(number,int):
        return "Need to specify number"
    search = db.session.query(Search).filter_by(session_id=session_id).order_by(Search.search_date).first()
    if (search is None):
        return "No active query"
    
    stmt = update(Result).where(Result.search_id == search.id).values(selected=False)
    db.session.execute(stmt)
    db.session.commit()
    res_elem = db.session.query(Result).filter(and_(Result.search_id==search.id,Result.picknumber==number)).first()
    if (res_elem is None):
        return "Result not found"
    res_elem.selected=True
    db.session.commit()
    '''
    coll=Collected(session.user_id,res_elem)
    db.session.add(coll)
    db.session.commit()
    '''
    res=f"Selected {res_elem.picknumber}:{res_elem.category} - {res_elem.title} - {res_elem.seeders}\n"
    return res

@jsonrpc.method("info")
def info(*argv:Any) -> str:
    token=argv[0]
    session=validateSession(token)
    session_id=session.id
    logger.debug("session validated")
    search = db.session.query(Search).filter_by(session_id=session_id).order_by(Search.search_date).first()
    if (search is None):
        return "No active query"
    res_elem = db.session.query(Result).filter(and_(Result.search_id==search.id,Result.selected)).first()
    if (res_elem is None):
        return "No element select"
    qp=res_elem.toQPElem()
    typ,data=pr.get_magnet_or_file(qp)
    print (f"{typ} - {data}")
    if typ == "magnet":
      hash=rd.get_torrent_hash(data)
    else:
      hash=rd.get_torrent_hash_from_file(data)

    print(f"Hash de fichero: {hash}")

    res=f"Hash de torrent: {hash}\n"
    rdtorrent = rd.search_torrent(str(hash).lower())
    if (rdtorrent is not None):
        res+=f"Item {rdtorrent.guid} found in user cache\n"
        exist_in_added=db.session().query(Added).filter(guid=rdtorrent.guid).first()
        if exist_in_added:
            return f"Torrent stored already: type status {exist_in_added.Id}"
    else:
        res+="Item not found in user cache\n"
    files=rd.check_cached_files(hash)
    if files!=[]:
        res+=f"Item found in RD cache. cached files:\n"
        for f in files:
            c=File.from_dict(f)
            res+=f"Id: {c.id} - File:{c.filename} ({c.filesize})\n"
    else:
        res+=f"Item not found in RD cache\n"
    return res

@jsonrpc.method("add")
def add(*argv:Any) -> str:
    token=argv[0]
    session=validateSession(token)
    session_id=session.id
    logger.debug("session validated")
    search = db.session.query(Search).filter_by(session_id=session_id).order_by(Search.search_date).first()
    if (search is None):
        return "No active query"
    res_elem = db.session.query(Result).filter(and_(Result.search_id==search.id,Result.selected)).first()
    if (res_elem is None):
        return "No element select"
    qp=res_elem.toQPElem()
    typ,data=pr.get_magnet_or_file(qp)
    print (f"{typ} - {data}")
    if typ == "magnet":
      hash=rd.get_torrent_hash(data)
    else:
      hash=rd.get_torrent_hash_from_file(data)

    print(f"Hash de fichero: {hash}")

    res=f"Hash de torrent: {hash}\n"
    rdtorrent = rd.search_torrent(str(hash).lower())
    if (rdtorrent is not None):
        res+=f"Item {rdtorrent.guid} in user cache\n" 
        exist_in_added=db.session().query(Added).filter(guid=rdtorrent.guid).first()
        if exist_in_added:
            return f"Torrent stored already: type status {exist_in_added.Id}"
        else:
            addTorrent=Added(session.user_id,rdtorrent)
            db.session.add(Torrent) 
            db.sessin.commit()
            return f"{res}\nTorrent stored: type status {exist_in_added.Id} to check status"
    else:
        if typ == "magnet":
            rdtorrent=rd.add_magnet2rd(data)
        else:
            rdtorrent=rd.add_torrent2rd(data)

    elem=rd.get_info(rdtorrent)
    rdfiles=rd.get_files(elem)  
    if rdfiles!=[]:
        res+=f"Torrent filename: {rdfiles['filename']}\n"
        files=rdfiles['files']
        for i in range(len(files)):
            c=File.from_dict_ucache(files[i])
            res+=f"Id: {c.id} - File:{c.filename} ({c.filesize} bytes - Selected {c.selected})\n"
 
    return res

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

  rdCol={}


  print("ok")
  app.run(host='0.0.0.0')
