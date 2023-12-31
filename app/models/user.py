from Model import db

class User(db.Model):
    __tablename__ = 'user'
    id  = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, unique=False, nullable=False)
    email = db.Column(db.String)
    sessions = db.relationship('Session', backref='user', lazy=True)
    collects = db.relationship('Collected', backref='user', lazy=True)
    adds = db.relationship('Added', backref='user', lazy=True)

