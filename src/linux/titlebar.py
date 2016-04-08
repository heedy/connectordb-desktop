# This script gathers the active titlebar text on "run"
# https://stackoverflow.com/questions/23786289/how-to-correctly-detect-application-name-when-changing-focus-event-occurs-with

# Workaround to get unicode working in both python 2 and 3
try:
    unicode = unicode
except:
    def unicode(txt,errors="lol"):
        return txt

import Xlib
import Xlib.display

disp = Xlib.display.Display()
root = disp.screen().root

NET_WM_NAME = disp.intern_atom('_NET_WM_NAME')
NET_ACTIVE_WINDOW = disp.intern_atom('_NET_ACTIVE_WINDOW')

root.change_attributes(event_mask=Xlib.X.FocusChangeMask)

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
        try:
            window_id = root.get_full_property(NET_ACTIVE_WINDOW, Xlib.X.AnyPropertyType).value[0]
            window = disp.create_resource_object('window', window_id)
            window.change_attributes(event_mask=Xlib.X.PropertyChangeMask)
            window_name = window.get_full_property(NET_WM_NAME, 0).value
        except Xlib.error.XError: #simplify dealing with BadWindow
            window_name = ""
        return unicode(window_name,errors="ignore")
