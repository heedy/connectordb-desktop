# This script gathers the active titlebar text on "run"
import win32gui
from ctypes import *
import time

# Totally copied from:
# http://stackoverflow.com/questions/911856/detecting-idle-time-using-python
from ctypes import Structure, windll, c_uint, sizeof, byref

class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]

def get_idle_duration():
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = sizeof(lastInputInfo)
    windll.user32.GetLastInputInfo(byref(lastInputInfo))
    millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
    return millis / 1000.0

class StreamGatherer():
    streamname = "active"
    streamschema = {"type": "boolean"}
    datatype = "toggle.active"
    description = "False if the computer is idle (no user input)"
    icon = "material:hourglass_empty"

    def __init__(self):
        self.prevcheck = time.time()
        self.prevvalue = False

    def start(self,cache):
        pass
    def stop(self):
        pass

    def run(self,cache):
        newvalue =  time.time() - self.prevcheck > get_idle_duration()
        self.prevcheck = time.time()
        if newvalue != self.prevvalue:
            cache.insert(self.streamname,newvalue)
        self.prevvalue = newvalue
