from connectordb.logger import Logger

import platform
import threading
import logging
import os
from plugins import getplugins


class LaptopLogger():
    def __init__(self,firstrun_callback=None):
        self.firstrun_callback = firstrun_callback

        self.syncer = None
        self.isrunning = False
        self.issyncing = False

        #Get the data gatherers. currentgatherers is the ones that are set to ON
        # gatherers is ALL of them
        self.currentgatherers = {}
        self.gatherers = {}
        for p in getplugins():
            g = p()
            self.currentgatherers[g.streamname] = g
            self.gatherers[g.streamname] = g

        #Open the cache file
        filedir = os.path.join(os.path.expanduser("~"),".local/share/connectordb/laptoplogger")
        # If on windows we save it in the appdata folder
        appdata = os.getenv("APPDATA")
        if appdata!="" and appdata is not None:
            filedir = os.path.join(appdata,"ConnectorDB/laptoplogger")
        if not os.path.exists(filedir):
            os.makedirs(filedir)
        cachefile = os.path.join(filedir,"cache.db")
        logging.info("Opening database " + cachefile)
        self.cache = Logger(cachefile,on_create=self.create_callback)

        # Disable the relevant gatherers
        for g in self.cache.data["disabled_gatherers"]:
            if g in self.currentgatherers:
                del self.currentgatherers[g]

        #Start running the logger if it is supposed to be running
        if self.cache.data["isrunning"]:
            self.start()
        if self.cache.data["isbgsync"]:
            self.startsync()

    def create_callback(self,c):
        logging.info("Creating new cache file...")

        c.data = {
            "isrunning": False,    # Whether or not the logger is currently gathering data. This NEEDS to be false - it is set to true later
            "isbgsync": False,      # Whether or not the logger automatically syncs with ConnectorDB. Needs to be false - automatically set to True later
            "gathertime": 4.0,     # The logger gathers datapoints every this number of seconds
            "disabled_gatherers": [], # The names of disabled gatherers
        }
        c.syncperiod = 60*60    # Sync once an hour

        #We now need to set the API key
        if self.firstrun_callback is not None:
            self.firstrun_callback(c)

    def removegatherer(self,g):
        logging.info("Removing gatherer " + g)
        if g in self.currentgatherers:
            del self.currentgatherers[g]
            if self.isrunning:
                self.gatherers[g].stop()
        # Save the setting
        d = self.cache.data
        if not g in d["disabled_gatherers"]:
            d["disabled_gatherers"].append(g)
            self.cache.data = d

    def addgatherer(self,g):
        logging.info("Adding gatherer " + g)
        if not g in self.currentgatherers:
            if self.isrunning:
                self.gatherers[g].start(self.cache)
            self.currentgatherers[g] = self.gatherers[g]
        # Save the setting
        d = self.cache.data
        if g in d["disabled_gatherers"]:
            d["disabled_gatherers"].remove(g)
            self.cache.data = d



    def gather(self):
        for g in self.currentgatherers:
            self.currentgatherers[g].run(self.cache)

        self.syncer = threading.Timer(self.cache.data["gathertime"],self.gather)
        self.syncer.daemon = True
        self.syncer.start()

    # Whether or not to run data gathering
    def start(self):
        if not self.isrunning:
            logging.info("Start acquisition")
            d = self.cache.data
            d["isrunning"] = True
            self.cache.data = d

            #First, make sure all streams are ready to go in the cache
            for g in self.gatherers:
                if not g in self.cache:
                    gatherer = self.gatherers[g]
                    logging.info("Adding {} stream ({})".format(g,self.gatherers[g].streamschema))
                    nickname = ""
                    if hasattr(gatherer,"nickname"):
                        nickname = gatherer.nickname
                    datatype = ""
                    if hasattr(gatherer,"datatype"):
                        datatype = gatherer.datatype
                    self.cache.addStream(g,gatherer.streamschema,description=gatherer.description,nickname=nickname,datatype=datatype)

            for g in self.currentgatherers:
                self.currentgatherers[g].start(self.cache)

            self.isrunning = True

            self.gather()

    # Whether or not to run background syncer
    def startsync(self):
        if not self.issyncing:
            logging.info("Start background sync")
            d = self.cache.data
            d["isbgsync"] = True
            self.cache.data = d
            self.cache.start()
            self.issyncing = True


    def stop(self,temporary=False):
        logging.info("Stop acquisition")

        if self.syncer is not None:
            self.syncer.cancel()
            self.syncer = None

        for g in self.currentgatherers:
            self.currentgatherers[g].stop()

        if not temporary:
            d = self.cache.data
            d["isrunning"] = False
            self.cache.data = d

        self.isrunning = False

    def stopsync(self):
        self.cache.stop()
        d = self.cache.data
        d["isbgsync"] = False
        self.cache.data = d
        self.issyncing= False

# This code here allows running the app without a GUI - it runs the logger directly
# from the underlying data-gathering plugins.
if __name__=="__main__":
    # https://stackoverflow.com/questions/954834/how-do-i-use-raw-input-in-python-3-1
    try: input = raw_input
    except NameError: pass

    import time
    import getpass
    import platform
    from connectordb import ConnectorDB,CONNECTORDB_URL

    logging.basicConfig(level=logging.DEBUG)

    def apikey_callback(c):
        #Allow the user to choose a custom server
        s = input("Server [DEFAULT: %s]:"%(CONNECTORDB_URL,))
        print(c.serverurl)
        if s!="":
            logging.info("Setting Server URL to "+ s)
            c.serverurl = s

        u = input("Username: ")
        p = getpass.getpass()

        cdb = ConnectorDB(u,p,c.serverurl)

        dev = cdb.user[platform.node()]
        if not dev.exists():
            logging.info("Creating device "+platform.node())
            dev.create()
        c.apikey = dev.apikey


    c = LaptopLogger(apikey_callback)
    c.start()

    # background sync is not enabled by default, since the gui has issues.
    # enable it right now in headless mode, since headless does not have a sync option
    c.startsync()

    while True:
        time.sleep(1)
