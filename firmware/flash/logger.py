import time

# ---- Global variables ----
import shared_variables as var

class Logger:
    def __init__(self, name, debug_enabled=False):
        self.name = name
        self.debug_enabled = debug_enabled
        self.MAX_LINES = 100

    def _timestamp(self):
        # short timestamp HH:MM:SS
        t = time.localtime()
        return "{:02}:{:02}:{:02}".format(t[3], t[4], t[5])

    def _print(self, level, *args):
        # print like normal print(), but prefixed
        prefix = "[{}][{}][{}]".format(self._timestamp(), self.name, level)
        if args:
            print(prefix, *args)
            
            if level == "WARN" or level == "ERROR": # or level == "INFO":
                prefix = prefix.replace("WARN", "#ffff00 WARN#")
                prefix = prefix.replace("INFO", "#00ff00 INFO#")
                prefix = prefix.replace("ERROR", "#ff0000 ERROR#")
                prefix = prefix.replace("DEBUG", "#00ffff DEBUG#")
            
                msg = " ".join(str(x) for x in (prefix,) + args)
            
                var.logger_error.append(msg)
                
                if len(var.logger_error) > self.MAX_LINES:
                    del var.logger_error[0:len(var.logger_error) - self.MAX_LINES]

        else:
            print(prefix)

    # Public log methods
    def info(self, *args):
        self._print("INFO", *args)

    def warning(self, *args):
        self._print("WARN", *args)

    def error(self, *args):
        self._print("ERROR", *args)

    def debug(self, *args):
        if self.debug_enabled:
            self._print("DEBUG", *args)