# This script gathers the active titlebar text on "run"
import win32gui

class StreamGatherer():
    streamname = "activewindow"
    streamschema = {"type": "string"}

    description = "Gathers the currently active window's titlebar text"

    def start(self,cache):
        pass
    def stop(self):
        pass

    def run(self,cache):
        cache.insert(self.streamname,self.windowtext())

    #Gets the titlebar text of the currently active window
    def windowtext(self):
        return unicode(win32gui.GetWindowText(win32gui.GetForegroundWindow()),errors="ignore")
