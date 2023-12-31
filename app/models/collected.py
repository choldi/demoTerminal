from Model import db
from QPElem import QPElem
from models.result import Result

class Collected(db.Model):
    __tablename__ = 'collected'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    guid = db.Column(db.String, unique=False, nullable=False)
    age = db.Column(db.Integer,unique=False,nullable=False)
    size = db.Column(db.Integer,unique=False,nullable=False)
    title = db.Column(db.String, unique=False, nullable=False)
    sortTitle = db.Column(db.String, unique=False, nullable=True)
    approved = db.Column(db.String, unique=False, nullable=True)
    imdbId = db.Column(db.String, unique=False, nullable=True)
    downloadUrl = db.Column(db.String, unique=False, nullable=True)
    magnetUrl = db.Column(db.String, unique=False, nullable=True)
    seeders = db.Column(db.Integer,unique=False,nullable=False)
    category = db.Column(db.String, unique=False, nullable=False)    


    def __init__(self,userId,elem:Result):
        self.user_id=userId
        self.guid = elem.guid
        self.age = elem.age
        self.size = elem.size
        self.title = elem.title
        self.approved = elem.approved
        self.imdbId = elem.imdbId
        self.downloadUrl = elem.downloadUrl
        self.magnetUrl = elem.magnetUrl
        self.seeders = elem.seeders
        self.category = elem.category

    def toQPElem(self,elem:QPElem)->QPElem:
        elem=QPElem()
        elem.guid = self.guid
        elem.age = self.age
        elem.size = self.size  
        elem.title = self.title 
        elem.approved = self.approved 
        elem.imdbId = self.imdbId
        elem.downloadUrl = self.downloadUrl 
        elem.magnetUrl = self.magnetUrl 
        elem.seeders = self.seeders
        elem.cat = self.category
        return elem        
