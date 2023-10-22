import logging
import colorlog
import sys

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Logging():
    def __init__(self,module,loglevel=logging.DEBUG):
      self.to_stdout=True
      self.to_file=False
      self.filename=""
      self.logger = logging.getLogger(module)
      stdout = colorlog.StreamHandler(stream=sys.stdout)

      self.fmt = colorlog.ColoredFormatter(
        "%(name)s: %(white)s%(asctime)s%(reset)s | %(log_color)s%(levelname)s%(reset)s | %(blue)s%(filename)s:%(lineno)s - %(funcName)20s()%(reset)s | %(process)d >>> %(log_color)s%(message)s%(reset)s"
      )

      stdout.setFormatter(self.fmt)
      self.logger.addHandler(stdout)
      self.logger.setLevel(loglevel)
      

class Log(Logging, metaclass=Singleton):
    pass

