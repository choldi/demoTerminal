from Model import db
from rd import File

class Filestore(db.Model):
    __tablename__ = 'filestore'
    id  = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.String, unique=True, nullable=False)
    filename = db.Column(db.String, unique=False, nullable=False)
    filesize = db.Column(db.String, unique=False, nullable=False)
    selected = db.Column(db.String, unique=False, nullable=False)
    added_id = db.Column(db.Integer, db.ForeignKey('added.id'), nullable=False)

    def __init__(self,f:File,_added):
      self.file_id=f.id
      self.filename=f.filename
      self.filesize=f.filesize
      self.selected=f.selected
      self.added_id=_added
