from Model import db

class Link(db.Model):
    __tablename__ = 'link'
    id = db.Column(db.Integer, primary_key=True)
    added_id = db.Column(db.Integer, db.ForeignKey('added.id'), nullable=False)
    link = db.Column(db.String, unique=False,nullable=False)

