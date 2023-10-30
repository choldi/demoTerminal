from Model import db
from app import app
from sqlalchemy import func,text
from models.user import User
from models.session import Session
from models.search import Search
from models.result import Result
from datetime import datetime, timedelta

SECONDS_FOR_INACTIVE_SESSION=300

with app.test_request_context():
    now = datetime.now()
    expiration = now - timedelta(seconds=SECONDS_FOR_INACTIVE_SESSION)
     
    inactives = db.session.query(Session).filter(Session.last_command<expiration)
    for i in inactives:
       searches = db.session.query(Search).filter_by(session_id=i.id)
       for s in searches:
          results = db.session.query(Result).filter_by(search_id=s.id)
          if results:
               results.delete()
          db.session.query(Search).filter_by(id=s.id).delete()
       db.session.query(Session).filter_by(id=i.id).delete()
 
 
    db.session.commit()
