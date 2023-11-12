import requests
import libtorrent as lt
import json
import sys
import logging
import colorlog
import time
import os
from Log import init_log
from typing import List,Any
from QPElem import QPElem

class File:
  id: int
  filename: str
  filesize: int
  selected: int
  def __init__(self,_id,_filename,_filesize,_selected):
    self.id=_id
    self.filename=_filename
    self.filesize=_filesize
    self.selected=_selected

  @staticmethod
  def from_dict(obj: Any) -> 'Root':
    _id=list(obj.keys())[0]
    elem = obj.get(_id)
    _filename = str(elem.get("filename"))
    _filesize = int(elem.get("filesize"))
    _selected = 0
    return File(_id,_filename,_filesize,_selected)

  def from_dict_ucache(obj: Any) -> 'Root':
    _filename = str(obj.get("path"))
    _filesize = int(obj.get("bytes"))
    _id=int(obj.get("id",0))
    _selected=int(obj.get("selected",0))
    return File(_id,_filename,_filesize,_selected)


class RDInfo:
  def __init__(self,_id,_filename,_original_filename,_hash,_bytes,_original_bytes,_host,_split,
               _progress,_status,_added,_ended,_speed,_seeders,_links,_files):
    self.id=_id
    self.filename=_filename
    self.original_filename=_original_filename
    self.hash=_hash
    self.bytes=_bytes
    self.original_bytes=_original_bytes
    self.host=_host
    self.split=_split
    self.progress=_progress
    self.status=_status
    self.added=_added
    self.ended=_ended
    self.speed=_speed
    self.seeders=_seeders
    self.links=_links
    self.files=_files

  @staticmethod
  def from_dict(obj:Any)->'Root':
    _id = str(obj.get('id'))
    _filename = str(obj.get('filename'))
    _original_filename=str(obj.get('original_filename'))
    _hash=str(obj.get('hash'))
    _bytes=int(obj.get('bytes'))
    _original_bytes=int(obj.get('original_bytes'))
    _host=str(obj.get('host'))
    _split=int(obj.get('split'))
    _progress=int(obj.get('progress'))
    _status=str(obj.get('status'))
    _added=str(obj.get('added',""))
    _ended=str(obj.get('ended',""))
    _speed=int(obj.get('speed',0))
    _seeders=int(obj.get('seeders',0))
    _links=obj.get('links')
    _f=obj.get('files')
    _files=[ File.from_dict_ucache(f) for f in _f ]
    return RDInfo(_id,_filename,_original_filename,_hash,_bytes,_original_bytes,_host,_split,
               _progress,_status,_added,_ended,_speed,_seeders,_links,_files)

 

class RealDebrid:
  def __init__(self, api_key,loglevel=logging.DEBUG):
    self.api_key = api_key
    self.rootUrl = "https://api.real-debrid.com/rest/1.0"
    #self.logger = self.set_logging(loglevel)
    self.logger = init_log("RealDebrid")
    self.headers = { "Authorization": f"Bearer {api_key}" }
    self.path='./downloads/'
    

  #get hash from magnet link 
  def get_torrent_hash(self,magnet_link):
    ses = lt.session()
    params = lt.parse_magnet_uri(magnet_link)
    self.logger.debug(f"hash: {params.info_hash}")
    return params.info_hash

  #get hash from torrent file
  def get_torrent_hash_from_file(self,torrent_file):
    ses = lt.session()
    info = lt.torrent_info(torrent_file)
    self.logger.debug(f"hash: {info.info_hash}")
    return info.info_hash()
  
  #check if a torrent is cached
  def check_torrent_cache(self, torrent_hash):
    apicall=f"{self.rootUrl}/torrents/instantAvailability/{torrent_hash}"
    response = requests.get(apicall, headers=self.headers)
    self.logger.debug(f"response status code: {response.status_code}")
     
    if response.status_code == 200:
        torrent_info = response.json()
        self.logger.debug(f"json: {torrent_info}")
        first_key = next(iter(torrent_info))
        if 'rd' in torrent_info[first_key]:
          value=torrent_info[first_key]['rd']
          if (value!=[]):
              self.logger.debug("Torrent is cached in Real Debrid")
          else:
              self.logger.debug("Torrent is not cached in Real Debrid")
          return value
        else:
            self.logger.debug("Torrent is not cached in Real Debrid")
            return []
    else:
        self.logger.error("Failed to check torrent cache status")
        return ""
 
  #check available server 
  def get_available_srv(self):
    apicall=f"{self.rootUrl}/torrents/availableHosts"
    response = requests.get(apicall, headers=self.headers)
    self.logger.debug (f"response status code: {response.status_code}")
    if response.status_code == 200:
      torrent_info = response.json()
      available_hosts=response.json()
      host=available_hosts[0]['host']
      self.logger.debug(f"Host: {host}")
      return host
    return ""  

  def search_torrent(self,hash,limit=100):
    page=1
    num=0
    apicall=f"{self.rootUrl}/torrents"
    while True:   
      params={'page':page,'limit':limit}
      self.logger.debug(f"params:{params}")
      response = requests.get(apicall, params=params, headers=self.headers)
      self.logger.debug (f"response status code: {response.status_code}")
      if response.status_code == 200:
        items=response.json()
        self.logger.debug(f"json: {items}")
        for item in items:
           print(f"Torrent id:{item['id']} Filename:{item['filename']}")
           if (hash==item['hash'].lower()):
              print(f"Hash found: {item['hash']} = id: {item['id']}")
              elem=self.get_info(item)
              return elem
        num+=len(items)
        if (num < limit):
          return None
        page=page+1
      else:
        self.logger.error(f"response code error: {response.status_code}")
        return None

  def unrestrict_link(self,link):
    apicall=f"{self.rootUrl}/unrestrict/link"
    data={'link':link}
    self.logger.debug(f"{data}")
    response = requests.post(apicall, data=data, headers=self.headers)
    self.logger.debug (f"response status code: {response.status_code}")
    if response.status_code == 200:
      link=response.json()
      self.logger.debug(f"json: {link}")
      return link
    else:
        self.logger.error(f"response code error: {response.status_code}")
        return {} 
  def download_link(self,link):
    response = requests.get(link['download'], stream=True)
    response.raise_for_status()
    chunk_size=int(link['filesize'] / (link['chunks'] - 1))
    dir=f"{self.path}{os.path.dirname(link['filename'])}"
    os.makedirs(dir,exist_ok=True)
    with open(link['filename'], "wb") as file:
      for chunk in response.iter_content(chunk_size=chunk_size):
        print (".",end="")
        if chunk:
          file.write(chunk)
    print()


#search if 
  def get_files_magnet(self,magnet):
    self.logger.debug(f"search for torrent in account")
    hash=self.get_torrent_hash(magnet)
    id=search_torrent(hash)
    if (id=={}):
      self.logger.debug("torrent not in account")
    cache=check_cache(hash)
    if (cache):
      self.logger.debug(f"{hash} in cache, mas rapido")
      id=add_torrent2rd(magnet)
    
      
      
  def check_cache(self,hash):
    torrentcache=self.check_torrent_cache(hash)

    if (torrentcache!=[]):
      self.logger.debug("torrent in cache")
      return True
    else:
      return False

  def check_cached_files(self,hash):
    torrentcache=self.check_torrent_cache(hash)

    if (torrentcache!=[]):
      self.logger.debug("torrent in cache")
    return torrentcache

  def add_magnet2rd(self,magnet):
    host=self.get_available_srv()
    self.logger.debug(f"Available host:{host}")
    if (host!=""):
      apicall=f"{self.rootUrl}/torrents/addMagnet"
      data={'magnet':magnet,'host':host}
      self.logger.debug(f"apicall:{apicall}")
      self.logger.debug(f"data:{data}")
      response = requests.post(apicall, data=data, headers=self.headers)
      self.logger.debug (f"response status code: {response.status_code}")
      if response.status_code == 201:
        rdtorrent=response.json()
        self.logger.debug(f"json: {rdtorrent}")
        if self.select_all_files(rdtorrent):
          return rdtorrent
      
    return None

  def select_all_files(self,rdtorrent,all=True):
    apicall=f"{self.rootUrl}/torrents/info/"
    apicall=rdtorrent['uri']
    self.logger.debug(f"apicall:{apicall}")
    response = requests.get(apicall, headers=self.headers)
    self.logger.debug (f"response status code: {response.status_code}")
    if response.status_code == 200:
      torrentinfo=response.json()
      self.logger.debug(f"json: {torrentinfo}")
      files=torrentinfo['files'] 
      self.logger.debug(f"files: {torrentinfo}")
      if all:
        params='all'
      else:
        params = ','.join([str(file['id']) for file in files]) 
      data = {'files':params}
      apicall=f"{self.rootUrl}/torrents/selectFiles/{rdtorrent['id']}"
      self.logger.debug(f"apicall:{apicall}")
      self.logger.debug(f"data: {data}")
      response = requests.post(apicall, data=data,headers=self.headers)
      self.logger.debug (f"response status code: {response.status_code}")
      return response.status_code == 204
    return False  

  def add_torrent2rd(self,file):
    host=self.get_available_srv()
    self.logger.debug(f"Available host:{host}")
    if (host!=""):
      apicall=f"{self.rootUrl}/torrents/addTorrent"
      params={'host':host}
      self.logger.debug(f"params:{params}")
      response = requests.put(apicall, data=open(file,'rb'), headers=self.headers)
      self.logger.debug (f"response status code: {response.status_code}")
      if response.status_code == 201:
        rdtorrent=response.json()
        self.logger.debug(f"json: {rdtorrent}")
        if self.select_all_files(rdtorrent):
          return rdtorrent
      
    return None

  def get_info(self,rdtorrent)->RDInfo:
    apicall=f"{self.rootUrl}/torrents/info/{rdtorrent['id']}"
    self.logger.debug (f"apicall:{apicall}")
    response = requests.get(apicall, headers=self.headers)
    self.logger.debug (f"response status code: {response.status_code}")
    if response.status_code == 200:
      info=response.json()
      self.logger.debug(f"json: {info}")
      rdi=RDInfo.from_dict(response.json())
      return rdi

  def get_files(self,rdtorrent)->RDInfo:
    info=self.get_info(rdtorrent)
    print(f"Status torrent:{info['status']}")
    if info.status !='downloaded':
      self.logger.debug(f"{rdtorrent['id']} not downloaded. Status {info.status}")
    else:
      self.logger.debug(f"{rdtorrent['id']}. Original filename: {info.original_filename}")
    return info.files

