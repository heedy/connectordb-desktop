# This script gathers the active titlebar text on "run"
import pyxhook as pyHook
from multiprocessing import Process, Array, Lock
import logging

MAX_STRING_SIZE = 500
#This function is run in its own process to allow it to gather titlebar info
def log_titlebar(val):
    def OnEvent(event):
        if len(event.WindowName) < MAX_STRING_SIZE:
            val.value = event.WindowName
        else:
            logging.warning("Window name too long!")

    hm = pyHook.HookManager()
    hm.KeyUp = OnEvent
    hm.MouseAllButtonsUp = OnEvent
    hm.HookKeyboard()
    hm.HookMouse()
    hm.run()

class StreamGatherer():
    streamname = "activewindow"
    streamschema = {"type": "string"}

    description = "Gathers the currently active window's titlebar text"

    def __init__(self):
        self.prevtext = ""
        self.titlebar_process = None
        self.current_text = Array('c',MAX_STRING_SIZE + 10)

    def start(self,logger):
        # Starts the background processes and stuff. The cache is passed, so that
        # if the gatherer catches events, they can be logged as they come in
        if self.titlebar_process is None:
            self.titlebar_process = Process(target=log_titlebar,args=(self.current_text,))
            self.titlebar_process.daemon = True
            self.titlebar_process.start()

    def stop(self):
        if self.titlebar_process is not None:
            self.titlebar_process.terminate()
            self.titlebar_process = None
            self.click_number.value = 0

    def run(self,cache):
        wt = self.windowtext()
        if wt != self.prevtext:
            self.prevtext = wt
            cache.insert(self.streamname,wt)

    #Gets the titlebar text of the currently active window
    def windowtext(self):
        return unicode(self.current_text.value,errors="ignore")
