from Model import db
from sqlalchemy.sql import func



class Search(db.Model):
    __tablename__ = 'search'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    search_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    results = db.relationship('Result', backref='search', lazy=True)

