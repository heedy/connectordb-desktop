import pyxhook as pyHook
from multiprocessing import Process, Value

#This function is run in its own process to allow it to gather keypresses
def log_click_count(val):
    def OnMouseEvent(event):
        val.value += 1
        return True

    hm = pyHook.HookManager()
    hm.SubscribeMouseAllButtonsDown(OnMouseEvent)
    hm.HookMouse()

    pythoncom.PumpMessages()

class StreamGatherer():
    streamname = "mouseclicks"
    streamschema = {"type": "integer"}
    description = "Gathers the number of clicks made with the mouse"

    def __init__(self):
        self.click_number = Value('i',0)
        self.clicklogger_process = None

    def start(self,cache):
        # Starts the background processes and stuff. The cache is passed, so that
        # if the gatherer catches events, they can be logged as they come in
        if self.clicklogger_process is None:
            self.clicklogger_process = Process(target=log_click_count,args=(self.click_number,))
            self.clicklogger_process.daemon = True
            self.clicklogger_process.start()

    def stop(self):
        if self.clicklogger_process is not None:
            self.clicklogger_process.terminate()
            self.clicklogger_process = None
            self.click_number.value = 0

    def run(self,cache):
        clk = self.clicks()
        if clk > 0:
            cache.insert(self.streamname,clk)


    #Gets the number of keypresses that are logged, and reset the counter
    def clicks(self):
        v = self.click_number.value
        self.click_number.value = 0
        return v
