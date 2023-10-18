
"""
class User(db.Model):
    __tablename__ = 'user'
    id  = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, unique=False, nullable=False)
    email = db.Column(db.String)
    sessions = db.relationship('Session', backref='user', lazy=True)

class Session(db.Model):
    __tablename__ = 'session'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String, unique=False, nullable=False)

"""

