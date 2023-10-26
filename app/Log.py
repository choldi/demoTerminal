import logging
import colorlog
import sys

      
def init_log(*args,lname="Log",loglevel=logging.DEBUG,filename="initlog"):
  stdout = colorlog.StreamHandler(stream=sys.stdout)
  fmt = colorlog.ColoredFormatter(
    "%(name)s: %(white)s%(asctime)s%(reset)s | %(log_color)s%(levelname)s%(reset)s | %(blue)s%(filename)s:%(lineno)s - %(funcName)20s()%(reset)s | %(process)d >>> %(log_color)s%(message)s%(reset)s"
  )
  stdout.setFormatter(fmt)
  logger=logging.getLogger(lname)
  logger.addHandler(stdout)
  logger.setLevel(loglevel)
  if (filename!=""):
    fileHandler = logging.FileHandler(f"{filename}.log")
    fileHandler.setFormatter(fmt)
    logger.addHandler(fileHandler)
  logger.debug("Fin logger")
  return logger
