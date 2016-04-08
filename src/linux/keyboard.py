
from multiprocessing import Process, Value

from Xlib import X,display
from Xlib.ext import record
from Xlib.protocol import rq
disp = display.Display()

if not disp.has_extension("RECORD"):
    raise Exception("RECORD extension not found")

#This function is run in its own process to allow it to gather keypresses
def log_key_count(val):
    # https://stackoverflow.com/questions/6609078/selective-record-using-python-xlib
    def callback(reply):
        if reply.category != record.FromServer or reply.client_swapped or not len(reply.data):
            return
        data = reply.data
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(data, disp.display, None, None)
            if event.type == X.KeyPress:
                val.value +=1

    context = disp.record_create_context(
                0,
                [record.AllClients],
                [{
                        'core_requests': (0, 0),
                        'core_replies': (0, 0),
                        'ext_requests': (0, 0, 0, 0),
                        'ext_replies': (0, 0, 0, 0),
                        'delivered_events': (0, 0),
                        'device_events': (X.KeyPress,X.ButtonPress),
                        'errors': (0, 0),
                        'client_started': False,
                        'client_died': False,
                }])
    disp.record_enable_context(context,callback)
    disp.record_free_context(context)

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
