import os
import logging
import coloredlogs
from sys import stdout

class Logger:
    class log_level:
        INFO     = logging.INFO
        DEBUG    = logging.DEBUG
        CRITICAL = logging.CRITICAL
        ERROR    = logging.ERROR
        WARNING  = logging.WARNING

    def __init__(self, name='IFORGE', log_level_var='IFORGE_LOG_LEVEL'):
        self.format = coloredlogs.ColoredFormatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s')
        self.name   = name
        self.logger = logging.getLogger(self.name)
        level = self.get_log_level_by_name(os.environ[log_level_var])
        self.setLogLevel(os.environ[log_level_var])

    def setLogLevel(self, level):
        level = self.get_log_level_by_name(level)
        self.logger.setLevel(level)
        if (level != "none"):
            coloredlogs.install(logger = self.logger, level=level)
        self.current_log_level = self.get_log_level_by_num(self.logger.level)
    
    def addFileHandler(self, logfilepath, log_level):
        handler = logging.FileHandler(logfilepath)
        handler.setLevel(log_level)
        self.logger.addHandler(handler)

    def info(self, msg):
        msg = self.formatMsg(msg)
        self.logger.log(self.log_level.INFO, msg)

    def debug(self, msg):
        msg = self.formatMsg(msg)
        self.logger.log(self.log_level.DEBUG, msg)

    def warning(self, msg):
        msg = self.formatMsg(msg)
        self.logger.log(self.log_level.WARNING, msg)

    def error(self, msg):
        msg = self.formatMsg(msg)
        self.logger.log(self.log_level.ERROR, msg)

    def fatal(self, msg):
        msg = self.formatMsg(msg)
        self.logger.log(self.log_level.CRITICAL, msg)

    def seperator(self, width=80):
        print('-'*width)

    def get_log_level_by_name(self, log_level):
        log_levels = {
            'info'    : logging.INFO,
            'debug'   : logging.DEBUG,
            'critical': logging.CRITICAL,
            'error'   : logging.ERROR,
            'warning' : logging.WARNING,
        }
        log_level = log_level.lower().strip()
        if log_level not in log_levels.keys():
            self.warning("Invalid log level supplied: %s, defaulting to log level INFO"%log_level)
            self.warning("Valid log levels: %s"%(', '.join(log_levels.keys())))
            return self.log_level.INFO
        return log_levels[log_level]

    def get_log_level_by_num(self, num):
        levels = {
            0  : "NOTSET",
            10 : "DEBUG",
            20 : "INFO",
            30 : "WARNING",
            40 : "ERROR",
            50 : "CRITICAL",
        }
        if num not in levels.keys():
            return "UNKNOWN"
        return levels[num]

    def formatMsg(self, msg):
        return msg # if msg.endswith('.') else "%s."%msg