import requests
import re
import time
import logging
from Log import init_log
from QPElem import QPElem, TorrentElements

class Prowlarr:
  api_key:str
  url_search:str
  logger: logging.Logger

  def __init__(self,prowlar_key,prowlar_host):
     self.api_key=prowlar_key
     self.url_search=prowlar_host
     self.headers = {"Accept": "application/json",
                     "Content-Type": "application/json",
                     "X-Api-Key": prowlar_key}
     self.logger=init_log(lname="Prowlarr")


  def getFilename_fromCd(self,cd):
    if not cd:
      return "filename"
    fname = re.findall('filename=\"(.+)\"', cd)
    if len(fname) == 0:
      return None
    return fname[0]

  def get_magnet_or_file(self,elem):
    if elem.magnetUrl != "None":
       self.logger.debug(f"Magnet url: {elem.magnetUrl}")
       r=requests.get(elem.magnetUrl,allow_redirects=False)
       time.sleep(3)
       link=r.headers['Location']
       return "magnet",link
    if elem.downloadUrl != "None":
       self.logger.debug(f"Download url: {elem.downloadUrl}")
       try:
         r = requests.get(elem.downloadUrl, allow_redirects=True)
         filename=self.getFilename_fromCd(r.headers['Content-Disposition'])
         with open(filename, 'wb') as f:
           f.write(r.content)
         return "file",filename
       except requests.exceptions.RequestException as e:
         s=str(e)
         pos=s.find("magnet")
         if pos==-1:
          raise e
         else:
          magnet=s[pos:]
          return "magnet",magnet
    else:
       return "error",""

  def search(self,query):
    params = { 'query':query}
    r = requests.get(self.url_search, params=params,headers=self.headers)
    torrents_raw=r.json()
    torrents=TorrentElements()
    for t in torrents_raw:
      q=QPElem.from_dict(t)
      torrents.append(q)
      q=None
    return torrents
    
