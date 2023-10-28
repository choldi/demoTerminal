from Model import db
from app import app

with app.test_request_context():

     db.drop_all()
     db.create_all()
