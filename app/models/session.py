from Model import db

class Session(db.Model):
    __tablename__ = 'session'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String, unique=False, nullable=False)
    last_command = db.Column(db.DateTime(timezone=True), unique=False, nullable=False)
    searches = db.relationship('Search', backref='session', lazy=True)
