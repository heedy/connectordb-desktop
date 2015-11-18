import pyHook, pythoncom
from multiprocessing import Process, Value

#This function is run in its own process to allow it to gather keypresses
def log_key_count(val):
    def OnKeyboardEvent(event):
        val.value += 1

    hm = pyHook.HookManager()
    hm.KeyDown = OnKeyboardEvent
    hm.HookKeyboard()

    pythoncom.PumpMessages()

class StreamGatherer():
    streamname = "keypresses"
    streamschema = {"type": "integer"}
    description = "Gathers the number of keystrokes made on the keyboard"

    def __init__(self):
        self.keypress_number = Value('i',0)
        self.keylogger_process = None

    def start(self,cache):
        # Starts the background processes and stuff. The cache is passed, so that
        # if the gatherer catches events, they can be logged as they come in
        if self.keylogger_process is None:
            self.keylogger_process = Process(target=log_key_count,args=(self.keypress_number,))
            self.keylogger_process.daemon = True
            self.keylogger_process.start()

    def stop(self):
        if self.keylogger_process is not None:
            self.keylogger_process.terminate()
            self.keylogger_process = None
            self.keypress_number.value = 0

    def run(self,cache):
        kp = self.keypresses()
        if kp > 0:
            cache.insert(self.streamname,kp)


    #Gets the number of keypresses that are logged, and reset the counter
    def keypresses(self):
        v = self.keypress_number.value
        self.keypress_number.value = 0
        return v
