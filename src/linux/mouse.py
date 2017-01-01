
from multiprocessing import Process, Value

from Xlib import X, display
from Xlib.ext import record
from Xlib.protocol import rq
disp = display.Display()

if not disp.has_extension("RECORD"):
    raise Exception("RECORD extension not found")

# This function is run in its own process to allow it to gather keypresses


def log_click_count(val):
    # https://stackoverflow.com/questions/6609078/selective-record-using-python-xlib
    def callback(reply):
        if reply.category != record.FromServer or reply.client_swapped or not len(reply.data):
            return
        data = reply.data
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(
                data, disp.display, None, None)

            if event.type == X.ButtonPress:
                if event.detail in [1, 3]:
                    val.value += 1

    context = disp.record_create_context(
        0,
        [record.AllClients],
        [{
            'core_requests': (0, 0),
            'core_replies': (0, 0),
            'ext_requests': (0, 0, 0, 0),
            'ext_replies': (0, 0, 0, 0),
            'delivered_events': (0, 0),
            # TODO: Why does this not allow only keypress/button?
            'device_events': (X.KeyPress, X.ButtonPress),
            'errors': (0, 0),
            'client_started': False,
            'client_died': False,
        }])
    disp.record_enable_context(context, callback)
    disp.record_free_context(context)


class StreamGatherer():
    streamname = "mouseclicks"
    streamschema = {"type": "integer"}
    description = "Gathers the number of clicks made with the mouse"
    datatype = "action.count"
    icon = "material:mouse"

    def __init__(self):
        self.click_number = Value('i', 0)
        # For some reason, starting then stopping this process crashes the program. The workaround
        # is to just keep the process running in the background, even when not
        # gathering data
        self.clicklogger_process = Process(
            target=log_click_count, args=(self.click_number,))
        self.clicklogger_process.daemon = True
        self.clicklogger_process.start()

    def start(self, cache):
        self.click_number.value = 0

    def stop(self):
        pass

    def run(self, cache):
        clk = self.clicks()
        if clk > 0:
            cache.insert(self.streamname, clk)

    # Gets the number of keypresses that are logged, and reset the counter
    def clicks(self):
        v = self.click_number.value
        self.click_number.value = 0
        return v
