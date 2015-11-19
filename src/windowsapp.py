# In order to create an executable, the windows pyinstaller needs the libraries that will be used
#in all the windows plugins. We import them here directly

import pyHook, pythoncom
import win32gui
from multiprocessing import Process, Value, freeze_support
import csv #Not sure why... but pyinstaller complains

import guilaptoplogger

if __name__=="__main__":
    freeze_support()    #Need to have freeze support
    guilaptoplogger.runapp()
