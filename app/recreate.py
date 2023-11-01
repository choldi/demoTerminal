from Model import db
from app import app
from models.user import User
from models.session import Session
from models.result import Result
from models.stored import Stored

with app.test_request_context():

     db.drop_all()
     db.create_all()
     root=User(id=1,username='root',password='toor',email='root@mail.com')
     db.session.add(root)
     db.session.commit()
     
