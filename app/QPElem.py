from typing import List
from typing import Any
from dataclasses import dataclass
import json
import re
@dataclass
class Subcategory:
    id: int
    name: str

    def __init__(self,id,name):
        self.id=id
        self.name=name

    @staticmethod
    def from_dict(obj: Any) -> 'Root':
        _id = int(obj.get("id"))
        _name = str(obj.get("name")) if "name" in obj else "--"
        return Subcategory(_id, _name)

class Category:
    id: int
    name: str
    subCategories: List[Subcategory]

    def __init__(self,id,name,subCategories):
        self.id=id
        self.name=name
        self.subCategories=subCategories

    @staticmethod
    def from_dict(obj: Any) -> 'Root':
        _id = int(obj.get("id"))
        _name = str(obj.get("name")) if "name" in obj else "--"
        _subCategories = [Subcategory.from_dict(y) for y in obj.get("subCategories")]
        return Category(_id, _name, _subCategories)

@dataclass
class QPElem:
    guid: str
    age: int
    ageHours: float
    ageMinutes: float
    size: int
    indexerId: int
    indexer: str
    title: str
    sortTitle: str
    approved: bool
    imdbId: int
    publishDate: str
    downloadUrl: str
    magnetUrl: str
    infoUrl: str
    indexerFlags: List[str]
    categories: List[Category]
    seeders: int
    leechers: int
    protocol: str
    fileName: str

    def __init__(self,guid,age,ageHours,ageMinutes,size,indexerId,indexer,title,sortTitle,approved,imdbId,publishData,downloadUrl,magnetUrl,infoUrl,indexerFlags,categories,seeders,leechers,protocol,fileName,cat):
        self.guid=guid
        self.age=age
        self.ageHours=ageHours
        self.ageMinutes=ageMinutes
        self.size=size
        self.indexerId=indexerId
        self.indexer=indexer
        self.title=title
        self.sortTitle=sortTitle
        self.approved=approved
        self.imdbId=imdbId
        self.publishData=publishData
        self.downloadUrl=downloadUrl
        self.magnetUrl=magnetUrl
        self.infoUrl=infoUrl
        self.indexerFlags=indexerFlags
        self.categories=categories
        self.seeders=seeders
        self.leechers=leechers
        self.protocol=protocol
        self.fileName=fileName
        self.cat=cat

    def __repr__(self):
        return f"Title:{self.title} Seeders:{self.seeders} Category:{self.cat} "

    @staticmethod
    def from_dict(obj: Any) -> 'Root':
        _guid = str(obj.get("guid"))
        _age = int(obj.get("age"))
        _ageHours = float(obj.get("ageHours"))
        _ageMinutes = float(obj.get("ageMinutes"))
        _size = int(obj.get("size"))
        _indexerId = int(obj.get("indexerId"))
        _indexer = str(obj.get("indexer"))
        _title = str(obj.get("title"))
        _sortTitle = str(obj.get("sortTitle"))
        _approved = bool(obj.get("approved"))
        _imdbId = int(obj.get("imdbId"))
        _publishDate = str(obj.get("publishDate"))
        _downloadUrl = str(obj.get("downloadUrl"))
        _magnetUrl = str(obj.get("magnetUrl"))
        _infoUrl = str(obj.get("infoUrl"))
        _indexerFlags = [y for y in obj.get("indexerFlags")]
        _categories = [Category.from_dict(y) for y in obj.get("categories")]
        _seeders = int(obj.get("seeders"))
        _leechers = int(obj.get("leechers"))
        _protocol = str(obj.get("protocol"))
        _fileName = str(obj.get("fileName"))
        _cat=_categories[0].name
        return QPElem(_guid, _age, _ageHours, _ageMinutes, _size, _indexerId, _indexer, _title, _sortTitle, _approved, _imdbId, _publishDate, _downloadUrl, _magnetUrl,_infoUrl, _indexerFlags, _categories, _seeders, _leechers, _protocol, _fileName,_cat)

    @staticmethod
    def from_str(str) -> 'Root':
        elem=json.loads(str)
        return QPElem.from_dict(elem)

class TorrentElements(List):

    def loadFromList(self,elems):
        for elem in elems:
           qp=QPElem.from_dict(elem)
           self.append(qp)
           qp=None

    def with_min_seeders(self,seeders):
        s=TorrentElements()
        l=[t for t in self if t.seeders>=seeders ]
        s.extend(l)
        return s 
    def with_category(self,category):
        s=TorrentElements()

        l=[t for t in self if re.search(category,t.categories[0].name,flags=re.IGNORECASE) != None ]
        s.extend(l)
        return s 

    def sort_by(self,element,order=""):
        reverse=True if order=="desc" else False
        s=TorrentElements()
        s.extend(sorted(self,key=lambda x:getattr(x,element),reverse=reverse))
        return s

    def to_str(self)->str:
        s="\n".join([f"{t.guid}-{t.title}" for t in self])
        return s
#
#    def __repr__(self):
#        for l in self:
#           print (f"Title:{l.title} - Seeders:{l.seeders}")
