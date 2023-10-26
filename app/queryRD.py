import os
import time
import yaml
import argparse
import requests
import re
from operator import itemgetter
import logging
from Log import init_log
from QPElem import QPElem, TorrentElements
from Prowlarr import Prowlarr
from rd import RealDebrid as RD
  
cats=[ 'WEBRip', 'WEB-DL', 'HDRip', 'DVDRip', 'BRRip', 'BluRay', '1080p', '720p', '480p', '2160p', '4K']
cats+=[ 'HDTV','PDTV','x264','x265','AVC','H265','H264']
cats=[ c.lower() for c in cats ]
print (cats)

    
def print_list_with_line_numbers(lst):
    current_page = 0
    while True:
        rows, columns = os.popen('stty size', 'r').read().split()
        page_size =  int(rows) - 3  # Subtract 3 for header and prompt
        width=int(columns)
        start_index = current_page * page_size
        end_index = start_index + page_size
        if end_index >= len(lst):
           end_index = len(lst)-1
        page_items = lst[start_index:end_index]
        if not page_items:
            print("No more items to display.")
            input("Enter to continue: ")
            current_page = 0
            start_index = current_page * page_size
            end_index = start_index + page_size
        lenrest=4 + 4 + 16 + 1 # 4 seeders + 4 line_number + 16 CAT
        maxlentitle = width - lenrest
        equ="=" * maxlentitle
        print(f"NUM SDR  MAIN CATEGORY  Title")
        print(f"=== === =============== {equ}")
        for i, item in enumerate(page_items):
            line_number = start_index + i 
            seeders=item.seeders if item.seeders<999 else 999
            title=item.title
            cat=item.cat
            lentitle=len(title)
            title=title if lentitle < maxlentitle else title[0:maxlentitle]
            print(f"{line_number: <3} {seeders: <3} {cat: <15} {title}")
        choice = (input("Enter line number or press Enter to continue: ")).lower()
        if (choice == "exit"):
           return -1
        elif  (choice=="up"):
            current_page -= 1 if current_page > 0 else current_page
        elif (choice== "down" or choice==""):
            current_page += 1 if end_index < len(lst) else current_page
        elif (choice.isdigit()):
            line_number= int(choice)
            return line_number
        else:
            print("Wrong select, try again")





def mainfunc(*args,config,**kwargs):
  logger=init_log(lname="queryRD")
  logger.debug("init qprow")
  
  try:
    with open(config) as f:
      cfg=yaml.safe_load(f)
  except Exception as e:
    logger.error(f"config error:{e} ")

  logger.debug("init qp main")
  
  try:
    rd_apikey=cfg['realdebrid']['api']
    pr_apikey=cfg['prowlarr']['api']
    pr_url=cfg['prowlarr']['url']
  except Exception as e:
    logger.error(f"Not required parameters in {config} file")
    exit()

  rd = RD(rd_apikey)
  logger.debug("created rd instance")
  pr = Prowlarr(pr_apikey,pr_url)
  logger.debug("created pr instance")

  query=input("Enter string to search:")

  te=pr.search(query)

  for t in te.with_category("XXX").with_min_seeders(5):
      print(f"{t.title} Seeders: {t.seeders} {t.categories[0].name}")
  for t in te.sort_by("seeders","desc").with_min_seeders(5):
      print(f"{t.title} Seeders: {t.seeders} {t.categories[0].name}")
  for t in te.sort_by("title").with_category('XXX'):
      print(f"{t.title} Seeders: {t.seeders}")



  i=0
  shows=[]
  fullseason=[]
  movies=[]
  xxx=[]
  others=[]

  elements=te.with_min_seeders(1).sort_by("seeders","desc")
  select=print_list_with_line_numbers(elements)
  if (select >=0 ):
    torrent=elements[select]
    print(torrent)
    typ,data=pr.get_magnet_or_file(torrent)
    print (f"{typ} - {data}")
    if typ == "magnet":
      hash=rd.get_torrent_hash(data)
    else:
      hash=rd.get_torrent_hash_from_file(data)

    print(f"Hash de fichero: {hash}")

    rdtorrent = rd.search_torrent(str(hash).lower())
    if (rdtorrent!={}):
      print(f"Item {rdtorrent['id']} found")
    else:
      isInCache=rd.check_cache(hash)
      if typ == "magnet":
        rdtorrent=rd.add_magnet2rd(data)
      else:
        rdtorrent=rd.add_torrent2rd(data)

    time.sleep(3)
    rdinfo=rd.get_info(rdtorrent)
    status=rdinfo['status']
    print(f"Status: {status}")
    if status != 'downloaded':
      print(f"Not completed, try in a while. Percentatge={rdinfo['progress']} - Speed: {rdinfo['speed']}")
      exit()
    torrentdata=rd.get_files(rdtorrent)
    files=torrentdata['files']
    i=0
    for file in files:
      selected="Downloable" if file['selected']==1 else "To enqueue" 
      print(f"{file['id']} - {file['path']} Bytes={file['bytes']}:Selected={selected})")
    selectPending=True
    while selectPending:
      res=input ("select files, comma separated , downloables (d) or all:")
      selectPending=False
      if re.match("^\d+(,\d+)*$",res):
        toDownload="some"
        files_to_download=re.split(",",res) 
        selectPending=not all(1 <= int(x) <= len(files) for x in files_to_download)
        res=list(set(files_to_download))
      elif res=="d":
        toDownload="downloables"
      elif res=="all":
        toDownload="all"
      else:
        selectPending=True
    
    print(f"Option selected:{res}")
    print(f"Files to download:{toDownload}")
    
    if (toDownload=="downloables"):
      i=0
      for file in files:
        if (file['selected']):
          link=rd.unrestrict_link(torrentdata['links'][i])
          rd.download_link(link)
          i+=1


      

if __name__=='__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("--config", "-c", default="config.yml")
  args=parser.parse_args()
  mainfunc(config=args.config)
  exit()
