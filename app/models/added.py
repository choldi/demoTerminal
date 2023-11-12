from Model import db
from QPElem import QPElem
from rd import RDInfo

class Added(db.Model):
    __tablename__ = 'added'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rd_id = db.Column(db.String, unique=False, nullable=False)
    filename = db.Column(db.String, unique=False, nullable=False)
    original_filename = db.Column(db.String, unique=False, nullable=False)
    hash = db.Column(db.String,unique=False,nullable=False)
    bytes = db.Column(db.Integer,unique=False,nullable=False)
    original_bytes = db.Column(db.Integer,unique=False,nullable=False)
    host = db.Column(db.String, unique=False, nullable=False)
    split = db.Column(db.Integer,unique=False,nullable=False)
    progress = db.Column(db.Integer,unique=False,nullable=False)
    status = db.Column(db.String, unique=False, nullable=True)
    added = db.Column(db.String, unique=False, nullable=True)
    ended = db.Column(db.String, unique=False, nullable=False)    
    speed = db.Column(db.Integer,unique=False,nullable=False)
    seeders = db.Column(db.Integer,unique=False,nullable=False)
    #links = db.relationship('Link', backref='added', foreign_keys=[Link.added_id],lazy=True)
    #files = db.relationship('Filestore', backref='added',foreign_keys=[Filestore.added_id],lazy=True)
    links = db.relationship('Link', backref='added', lazy=True)
    files = db.relationship('Filestore', backref='added',lazy=True)


    def __init__(self,userId,rdi:RDInfo):

        self.user_id=userId
        self.rd_id=rdi.id
        self.filename=rdi.filename
        self.original_filename=rdi.original_filename
        self.hash=rdi.hash
        self.bytes=rdi.bytes
        self.original_bytes=rdi.original_bytes
        self.host=rdi.host
        self.split=rdi.split
        self.progress=rdi.progress
        self.status=rdi.status
        self.added=rdi.added
        self.ended=rdi.ended
        self.speed=rdi.speed
        self.seeders=rdi.seeders
        

    def toRDInfo(self)->RDInfo:
        elem=RDInfo()
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
