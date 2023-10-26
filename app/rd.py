import requests
import libtorrent as lt
import json
import sys
import logging
import colorlog
import time
import os
from Log import init_log

logger = logging.getLogger("rd.py")

stdout = colorlog.StreamHandler(stream=sys.stdout)

fmt = colorlog.ColoredFormatter(
    "%(name)s: %(white)s%(asctime)s%(reset)s | %(log_color)s%(levelname)s%(reset)s | %(blue)s%(filename)s:%(lineno)s - %(funcName)20s()%(reset)s | %(process)d >>> %(log_color)s%(message)s%(reset)s"
)

stdout.setFormatter(fmt)
logger.addHandler(stdout)

logger.setLevel(logging.DEBUG)

class RealDebrid:
  def __init__(self, api_key,loglevel=logging.DEBUG):
    self.api_key = api_key
    self.rootUrl = "https://api.real-debrid.com/rest/1.0"
    #self.logger = self.set_logging(loglevel)
    self.logger = init_log()
    self.headers = { "Authorization": f"Bearer {api_key}" }
    self.path='./downloads/'
    
  def set_logging(self,loglevel):
    logger = logging.getLogger("RealDebrid")
    stdout = colorlog.StreamHandler(stream=sys.stdout)

    fmt = colorlog.ColoredFormatter(
      "%(name)s: %(white)s%(asctime)s%(reset)s | %(log_color)s%(levelname)s%(reset)s | %(blue)s%(filename)s:%(lineno)s - %(funcName)20s()%(reset)s | %(process)d >>> %(log_color)s%(message)s%(reset)s"
    )
    stdout.setFormatter(fmt)
    logger.addHandler(stdout)
    logger.setLevel(loglevel)
    return logger

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
        value=torrent_info[first_key]
        if (torrent_info[first_key]!=[]):
            self.logger.debug("Torrent is cached in Real Debrid")
        else:
            self.logger.debug("Torrent is not cached in Real Debrid")
        return value
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
              return item
        num+=len(items)
        if (num < limit):
          return {} 
        page=page+1
      else:
        self.logger.error(f"response code error: {response.status_code}")
        return {} 

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
    logger.debug(f"search for torrent in account")
    hash=self.get_torrent_hash(magnet)
    id=search_torrent(hash)
    if (id=={}):
      logger.debug("torrent not in account")
    cache=check_cache(hash)
    if (cache):
      logger.debug(f"{hash} in cache, mas rapido")
      id=add_torrent2rd(magnet)
    
      
      
  def check_cache(self,hash):
    torrentcache=self.check_torrent_cache(hash)

    if (torrentcache!=[]):
      logger.debug("torrent in cache")
      return True
    else:
      return False

  def add_magnet2rd(self,magnet):
    host=self.get_available_srv()
    logger.debug(f"Available host:{host}")
    if (host!=""):
      apicall=f"{self.rootUrl}/torrents/addMagnet"
      data={'magnet':magnet,'host':host}
      logger.debug(f"apicall:{apicall}")
      logger.debug(f"data:{data}")
      response = requests.post(apicall, data=data, headers=self.headers)
      logger.debug (f"response status code: {response.status_code}")
      if response.status_code == 201:
        rdtorrent=response.json()
        logger.debug(f"json: {rdtorrent}")
        if self.select_all_files(rdtorrent):
          return rdtorrent 
      
    return {}

  def select_all_files(self,rdtorrent,all=True):
    apicall=f"{self.rootUrl}/torrents/info/"
    apicall=rdtorrent['uri']
    logger.debug(f"apicall:{apicall}")
    response = requests.get(apicall, headers=self.headers)
    logger.debug (f"response status code: {response.status_code}")
    if response.status_code == 200:
      torrentinfo=response.json()
      logger.debug(f"json: {torrentinfo}")
      files=torrentinfo['files'] 
      logger.debug(f"files: {torrentinfo}")
      if all:
        params='all'
      else:
        params = ','.join([str(file['id']) for file in files]) 
      data = {'files':params}
      apicall=f"{self.rootUrl}/torrents/selectFiles/{rdtorrent['id']}"
      logger.debug(f"apicall:{apicall}")
      logger.debug(f"data: {data}")
      response = requests.post(apicall, data=data,headers=self.headers)
      logger.debug (f"response status code: {response.status_code}")
      return response.status_code == 204
    return False  

  def add_torrent2rd(self,file):
    host=get_available_srv()
    logger.debug(f"Available host:{host}")
    if (host!=""):
      apicall=f"{self.rootUrl}/torrents/addTorrent"
      params={'host':host}
      logger.debug(f"params:{params}")
      response = requests.put(apicall, data=open(file,'rb'), headers=self.headers)
      logger.debug (f"response status code: {response.status_code}")
      if response.status_code == 201:
        rdtorrent=response.json()
        logger.debug(f"json: {rdtorrent}")
        if select_all_files(rdtorrent):
          return rdtorrent 
      
    return {} 

  def get_info(self,rdtorrent):
    apicall=f"{self.rootUrl}/torrents/info/{rdtorrent['id']}"
    logger.debug (f"apicall:{apicall}")
    response = requests.get(apicall, headers=self.headers)
    logger.debug (f"response status code: {response.status_code}")
    if response.status_code == 200:
      info=response.json()
      logger.debug(f"json: {info}")
      return response.json()

  def get_files(self,rdtorrent):
    info=self.get_info(rdtorrent)
    print(f"Status torrent:{info['status']}")
    if (info['status']!='downloaded'):
      logger.debug("f{rdtorrent['id']} not downloaded. Status {info['status']}")
    else:
      logger.debug("f{rdtorrent['id']}. Original filename: {info['original_filename']}")
    return info


api_key = "S63V2MUWJQAISMIZVRVBZVLWODGOKFFDNDUECFXFNJOAENII436Q"

def get_torrent_hash(magnet_link):
    ses = lt.session()
    params = lt.parse_magnet_uri(magnet_link)
    logger.debug(f"hash: {params.info_hash}")
    return params.info_hash

def get_torrent_hash_from_file(torrent_file):
    ses = lt.session()
    info = lt.torrent_info(torrent_file)
    logger.debug(f"hash: {info.info_hash}")
    return info.info_hash()

def check_torrent_cache(api_key, torrent_hash):
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    apicall=f"https://api.real-debrid.com/rest/1.0/torrents/instantAvailability/{torrent_hash}"
    response = requests.get(apicall, headers=headers)
    logger.debug(f"response status code: {response.status_code}")
     
    if response.status_code == 200:
        torrent_info = response.json()
        logger.debug(f"json: {torrent_info}")
        first_key = next(iter(torrent_info))
        value=torrent_info[first_key]
        if (torrent_info[first_key]!=[]):
            logger.debug("Torrent is cached in Real Debrid")
        else:
            logger.debug("Torrent is not cached in Real Debrid")
        return value
    else:
        logger.error("Failed to check torrent cache status")
        return ""

def get_available_srv():
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    apicall="https://api.real-debrid.com/rest/1.0/torrents/availableHosts"
    response = requests.get(apicall, headers=headers)
    logger.debug (f"response status code: {response.status_code}")
    if response.status_code == 200:
      torrent_info = response.json()
      available_hosts=response.json()
      host=available_hosts[0]['host']
      logger.debug(f"Host: {host}")
      return host
    return "" 
       
def search_torrent(hash):
    page=1
    limit=100
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    apicall="https://api.real-debrid.com/rest/1.0/torrents"
    while True:   
      params={'page':page,'limit':limit}
      logger.debug(f"params:{params}")
      response = requests.get(apicall, params=params, headers=headers)
      logger.debug (f"response status code: {response.status_code}")
      if response.status_code == 200:
        items=response.json()
        logger.debug(f"json: {items}")
        for item in items:
           if (hash==item['hash']):
              print(f"Hash found: {item['hash']} = id: {item['id']}")
              return item['id']
        num=len(items)
        if (num < limit):
          return ""
        page=page+1
      else:
        logger.error(f"response code error: {response.status_code}")
        return ""

def get_files_hash(hash,magnet):
    logger.debug(f"search for torrent in account")
    id=search_torrent(hash)
    if (id==""):
      logger.debug("torrent not in account")
    cache=check_cache(hash)
    if (cache):
      logger.debug(f"{hash} in cache, mas rapido")
      id=add_torrent2rd(magnet)
    
      
      
def check_cache(hash):
    torrentcache=check_torrent_cache(api_key,hash)

    if (torrentcache!=[]):
      logger.debug("torrent in cache")
      return True
    else:
      return False
     

def add_magnet2rd(magnet):
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    host=get_available_srv()
    logger.debug(f"Available host:{host}")
    if (host!=""):
      apicall="https://api.real-debrid.com/rest/1.0/torrents/addMagnet"
      params={'magnet':magnet,'host':host}
      logger.debug(f"params:{params}")
      response = requests.get(apicall, params=params, headers=headers)
      logger.debug (f"response status code: {response.status_code}")
      if response.status_code == 201:
        rdtorrent=response.json()
        logger.debug(f"json: {rdtorrent}")
        if select_all_files(rdtorrent):
          return rdtorrent 
      
    return {}

#per borrar
def list_files(rdtorrent):
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    apicall="https://api.real-debrid.com/rest/1.0/torrents/info/"
    apicall=rdtorrent['uri']
    logger.debug(f"apicall:{apicall}")
    response = requests.get(apicall, headers=headers)
    logger.debug (f"response status code: {response.status_code}")
    if response.status_code == 200:
      torrentinfo=response.json()
      logger.debug(f"json: {torrentinfo}")
      files=torrentinfo['files'] 
      logger.debug(f"files: {torrentinfo}")
      return files
    return [] 

def select_all_files(rdtorrent):
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    apicall="https://api.real-debrid.com/rest/1.0/torrents/info/"
    apicall=rdtorrent['uri']
    logger.debug(f"apicall:{apicall}")
    response = requests.get(apicall, headers=headers)
    logger.debug (f"response status code: {response.status_code}")
    if response.status_code == 200:
      torrentinfo=response.json()
      logger.debug(f"json: {torrentinfo}")
      files=torrentinfo['files'] 
      logger.debug(f"files: {torrentinfo}")
      params = ','.join([str(file['id']) for file in files]) 
      data = {'files':'all'}
      apicall=f"https://api.real-debrid.com/rest/1.0/torrents/selectFiles/{rdtorrent['id']}"
      logger.debug(f"apicall:{apicall}")
      logger.debug(f"data: {data}")
      response = requests.post(apicall, data=data,headers=headers)
      logger.debug (f"response status code: {response.status_code}")
      return response.status_code == 204
    return False  

def add_torrent2rd(file):
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    host=get_available_srv()
    logger.debug(f"Available host:{host}")
    if (host!=""):
      apicall="https://api.real-debrid.com/rest/1.0/torrents/addTorrent"
      params={'host':host}
      logger.debug(f"params:{params}")
      response = requests.put(apicall, data=open(file,'rb'), headers=headers)
      logger.debug (f"response status code: {response.status_code}")
      if response.status_code == 201:
        rdtorrent=response.json()
        logger.debug(f"json: {rdtorrent}")
        if select_all_files(rdtorrent):
          return rdtorrent 
      
    return {} 

def check_cache_old(magnet):
    hash=get_torrent_hash(magnet)
    torrentcache=check_torrent_cache(api_key,hash)
    print ("torrentcache")
    print (torrentcache)
    if (torrentcache!=[]):
     
       rdcache=torrentcache['rd']
       print ("rd cache")
       print (rdcache)
       files = []
       i = 0
       for rdelem in rdcache:
           print ("rdelem")
           print (rdelem)

       for rdelem in rdcache:
           first_key = next(iter(rdelem))
           typed=rdelem[first_key]
           rdfile=rdelem[first_key]
           print(f"first key:{first_key} - {rdfile}")
           print ("rdfile")
           print (rdfile)
           i = i+1 
           file={}
           file['name']=rdfile['filename']
           file['pos']=i
           file['size']=round(rdfile['filesize'] / 1000000,2)
           file['type']=first_key
           files.append(file) 
       for file in files:
           print (f"{file['pos']}-{file['name']} - {file['size']}MB")
 
        
          
        


def main():
    magnet_link = "magnet:?xt=urn:btih:cac6dfac86a1244266677ce53c55907897b6e6d3&dn=Physical.S03E09.WEB.x264-TORRENTGALAXY&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.cyberia.is%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.torrent.eu.org%3A451%2Fannounce&tr=udp%3A%2F%2Fexplodie.org%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.birkenwald.de%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.moeking.me%3A6969%2Fannounce&tr=udp%3A%2F%2Fipv4.tracker.harry.lu%3A80%2Fannounce&tr=udp%3A%2F%2Ftracker.tiny-vps.com%3A6969%2Fannounce"
    magnet_link = "magnet:?xt=urn:btih:dbffc06b9379f999f1cff90b63e30abf123609b3&dn=Cerebrum.2022.1080p.WEB-DL.DDP5.1.x264-AOC[TGx]&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.cyberia.is%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.torrent.eu.org%3A451%2Fannounce&tr=udp%3A%2F%2Fexplodie.org%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.birkenwald.de%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.moeking.me%3A6969%2Fannounce&tr=udp%3A%2F%2Fipv4.tracker.harry.lu%3A80%2Fannounce&tr=udp%3A%2F%2Ftracker.tiny-vps.com%3A6969%2Fannounce"
    torrent_hash = get_torrent_hash(magnet_link)
    print("Torrent Hash:", torrent_hash)

    apicall=f"https://api.real-debrid.com/rest/1.0/user"
    headers = {
         "Authorization": f"Bearer {api_key}"
    }
    response = requests.get(apicall, headers=headers)
    print (response.json())

    #get_files_magnet(magnet_link)
    torrent_file=r'Cursed Is The Blood, The Dark Divinity (01) by Jordyn Moretti EPUB.torrent'
    hash=get_torrent_hash_from_file(torrent_file)
    print(f"Hash de fichero: {hash}")
    add_torrent2rd(torrent_file)
    #check_torrent_cache(api_key,hash)
    #get_files_magnet(magnet_link)
    

    hash=get_torrent_hash(magnet_link)
    check_torrent_cache(api_key,hash)
    
#magnet_link = "magnet:?xt=urn:btih:dbffc06b9379f999f1cff90b63e30abf123609b3&dn=Cerebrum.2022.1080p.WEB-DL.DDP5.1.x264-AOC[TGx]&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.cyberia.is%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.torrent.eu.org%3A451%2Fannounce&tr=udp%3A%2F%2Fexplodie.org%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.birkenwald.de%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.moeking.me%3A6969%2Fannounce&tr=udp%3A%2F%2Fipv4.tracker.harry.lu%3A80%2Fannounce&tr=udp%3A%2F%2Ftracker.tiny-vps.com%3A6969%2Fannounce"
#rd = RealDebrid(api_key)
#hash=rd.get_torrent_hash(magnet_link)
#print(f"Hash={hash}")
#isCached=rd.check_torrent_cache(hash)
#print(f"isCached={isCached}")
#rd.search_torrent("ssss")
#rdtorrent=rd.add_magnet2rd(magnet_link)
#if (rdtorrent !={}):
   #while True:
     #info=rd.get_info(rdtorrent)
     #print(f"status: {info['status']}" )
     #if info['status']=='downloaded':
       #break
     #time.sleep (3)
