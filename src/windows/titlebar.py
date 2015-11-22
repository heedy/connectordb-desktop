# This script gathers the active titlebar text on "run"
import win32gui

class StreamGatherer():
    streamname = "activewindow"
    streamschema = {"type": "string"}

    description = "Gathers the currently active window's titlebar text"
    
    def __init__(self):
        self.prevtext = ""

    def start(self,cache):
        pass
    def stop(self):
        pass

    def run(self,cache):
        wt = self.windowtext()
        if wt != self.prevtext:
            self.prevtext = wt
            cache.insert(self.streamname,wt)

    #Gets the titlebar text of the currently active window
    def windowtext(self):
        return unicode(win32gui.GetWindowText(win32gui.GetForegroundWindow()),errors="ignore")
