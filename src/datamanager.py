
from connectordb.logger import Logger
import connectordb

import threading
import logging
import os
import shutil

import files
from plugins import getplugins
import cdbmanager


class DataManager():

    def __init__(self, folder, createCallback):
        """
        The DataManager is the main handler of LaptopLogger. It is the console
        version of LaptopLogger. Note that this file can be run independently,
        without the QT dependence. 

        The DataManager takes the folder in which to look for existing data,
        and a callback that is used for creation. The DataManager alls this when
        the loggers are not set up. The create callbacks are to use DataManager's 
        functions:
            - create 
            - login
            - createAndImport
        The functions will perform the necessary preparation and importing of data. 
        After giving DataManager this information, it will handle everything else itself. 
        """

        # The following are the files used by the DataManager
        self.versionfile = os.path.join(folder, "laptoplogger.json")
        self.cachefile = os.path.join(folder, "cache.db")
        # The database folder if it is auto-managed
        self.dbdir = os.path.join(folder, "cdb")

        # Try setting up the ConnectorDB database manager. Set it to none if
        # we can't find the ConnectorDB executable
        try:
            self.manager = cdbmanager.Manager(self.dbdir)
            self.cdbversion = self.manager.version()
            logging.info("Local ConnectorDB found: " + self.cdbversion)
        except:
            logging.warning(
                "Could not find ConnectorDB executable. Can't manage local database.")
            self.manager = None
            self.cdbversion = ""

        # This is true when the DataManager is currently managing a running ConnectorDB
        # instance
        self.ismanaging = False
        self.isgathering = False  # True when the data is being gathered
        self.issyncing = False  # True when sync is on

        # The timer that is used to run gathering every couple seconds
        # It is enabled in startgathering
        self.syncer = None

        # If the file doesn't exist, we know that the database has not been set
        # up.
        if not os.path.isfile(self.versionfile):
            logging.debug(
                "DataManager: Could not find existing instance. Running create callbacks")
            self.remove()  # Clean up any vestiges of failed installations
            if not os.path.isdir(folder):
                os.makedirs(folder)
            # Set up the cache file so that we can use it when running create
            self.logger = Logger(self.cachefile, on_create=self.onCacheCreate)
            createCallback(self)
        else:
            # OK, we load the cache file, since we assume stuff already exsits
            self.logger = Logger(self.cachefile, on_create=self.onCacheCreate)

        # Now the create callback should have been run. Let's check to see if
        # the necessary files now exist
        if not os.path.isfile(self.versionfile):
            raise Exception(
                self.versionfile + " was not found, and is required. Starting LaptopLogger must have somehow failed.")

        # Load the version file
        self.info = files.readJSON(self.versionfile)
        if self.info["version"] != 1:
            raise Exception("An incompatible version already exists at " +
                            folder + ". Delete the folder if you don't need the existing data.")

        if self.info["managed"] and not self.ismanaging:
            # The database is managed. Start the database
            if self.cdbversion != self.info["connectordb"]:
                logging.warning("ConnectorDB version used to make managed logger (%s) does not match current version (%s)" % (
                    self.info["connectordb"], self.cdbversion))
            logging.info("Starting ConnectorDB server")
            self.manager.start()
            self.ismanaging = True

        # Load the plugins. plugins is the dict of ALL plugins. currentplugins is the
        # dict of plugins that are currently enabled.
        self.currentplugins = {}
        self.plugins = {}
        logging.info("Setting up data gathering plugins")
        for p in getplugins():
            g = p()
            logging.info("Initialized plugin " + g.streamname)
            self.currentplugins[g.streamname] = g
            self.plugins[g.streamname] = g

        logging.debug(str(self.logger.data))

        # Disable the plugins that have been disabled by user
        for g in self.logger.data["disabled_plugins"]:
            logging.info("Disabling plugin " + g)
            if g in self.currentplugins:
                del self.currentplugins[g]

        # Start running the logger if it is supposed to be running
        if self.logger.data["isgathering"]:
            self.startgathering()
        if self.logger.data["issyncing"]:
            self.startsync()

    def remove(self):
        """
            Given a folder with possibly an existing LaptopLogger installation,
            removes all relevant files.
        """
        if self.ismanaging:
            self.manager.stop()
            self.ismanaging = False
        # Remove the local ConnectorDB database
        if os.path.exists(self.dbdir):
            shutil.rmtree(self.dbdir)
        # Remove the version file
        if os.path.exists(self.versionfile):
            os.remove(self.versionfile)
        # Remove the cache file if it exists
        if os.path.exists(self.cachefile):
            # TODO: Clean up running logger before removing the file
            os.remove(self.cachefile)

    def onCacheCreate(self, c):
        logging.info("Creating new cache file...")

        c.data = {
            # Whether or not the logger is currently gathering data.
            "isgathering": True,
            # Whether or not the logger automatically syncs with ConnectorDB.
            "issyncing": True,
            "gathertime": 4.0,     # The logger gathers datapoints every this number of seconds
            "disabled_plugins": [],  # The names of disabled plugins
        }
        c.syncperiod = 30 * 60    # Sync once every half hour

    def disablePlugin(self, p):
        logging.info("Disabling plugin " + p)
        if p in self.currentplugins:
            del self.currentplugins[p]
            if self.isgathering:
                self.plugins[p].stop()
        # Save the setting
        d = self.logger.data
        if not p in d["disabled_plugins"]:
            d["disabled_plugins"].append(p)
            self.logger.data = d

    def enablePlugin(self, p):
        logging.info("Enabling plugin " + p)
        if not p in self.currentplugins:
            if self.isgathering:
                self.plugins[p].start(self.logger)
        d = self.logger.data
        if p in d["disabled_plugins"]:
            d["disabled_plugins"].remove(p)
            self.logger.data = d

    def startgathering(self):
        if not self.isgathering:
            logging.info("Start gathering data")
            d = self.logger.data
            d["isgathering"] = True
            self.logger.data = d

            # Make sure that all streams are ready to go in the Logger
            # We make sure that the logger has the streams set up
            for p in self.plugins:
                if not p in self.logger:
                    plugin = self.plugins[p]
                    logging.info("Adding {} stream ({})".format(
                        p, self.plugins[p].streamschema))
                    nickname = ""
                    if hasattr(plugin, "nickname"):
                        nickname = plugin.nickname
                    datatype = ""
                    if hasattr(plugin, "datatype"):
                        datatype = plugin.datatype
                    icon = ""
                    if hasattr(plugin, "icon"):
                        icon = plugin.icon
                    description = ""
                    if hasattr(plugin, "description"):
                        description = plugin.description
                    self.logger.addStream(p, plugin.streamschema,
                                          description=description, nickname=nickname, datatype=datatype, icon=icon)

            # Enable the gatherers that are currently being set up
            for p in self.currentplugins:
                self.currentplugins[p].start(self.logger)

            self.isgathering = True

            # Start the actual gathering
            self.gather()

    def stopgathering(self, save=True):
        if self.isgathering:
            logging.info("Stopping data acquisition")

            if save:
                d = self.logger.data
                d["isgathering"] = False
                self.logger.data = d

            if self.syncer is not None:
                self.syncer.cancel()
                self.syncer = None

            for p in self.currentplugins:
                self.currentplugins[p].stop()

            self.isgathering = False

    def startsync(self):
        if not self.issyncing:
            logging.info("Starting background sync")
            d = self.logger.data
            d["issyncing"] = True
            self.logger.data = d

            self.logger.start()
            self.issyncing = True

    def stopsync(self):
        if self.issyncing:
            logging.info("Stopping background sync")
            d = self.logger.data
            d["issyncing"] = False
            self.logger.data = d
            self.logger.stop()
            self.issyncing = False

    def exit(self):
        if self.isgathering:
            self.stopgathering(False)
        if self.ismanaging:
            self.ismanaging = False
            self.manager.stop()
        # Finally, stop the logger itself. This sometimes gives a threadingViolationError
        # that is a bug at time of writing, so we do it at the end in case it
        # crashes
        self.logger.close()
        self.logger = None

    def gather(self):
        for p in self.currentplugins:
            self.currentplugins[p].run(self.logger)

        # Call this function in repeatedly in the timer
        self.syncer = threading.Timer(
            self.logger.data["gathertime"], self.gather)
        self.syncer.daemon = True
        self.syncer.start()

    # The following 3 functions are used to initialize the laptoplogger
    # from the create callback
    def login(self, username, password, devicename, serverurl, isprivate, deviceOverwriteCallback):
        logging.info("Logging in as " + username + " to " + serverurl)
        cdb = connectordb.ConnectorDB(username, password, serverurl)
        cdb.ping()
        dev = cdb.user[devicename]
        if not dev.exists():
            logging.info("Creating device " + devicename + " at " + serverurl)
            dev.create(public=not isprivate, description="Logs data from your computer",
                       icon="material:laptop")
        else:
            logging.warning("Device " + devicename +
                            " already exists! Overwrite?")
            # The device already exists. We chick deviceOverwriteCallback to see if we can
            # safely overwrite the device
            if not deviceOverwriteCallback(devicename):
                raise Exception(
                    "Device already exists. Choose another device name")

        # Set up the logger's credentials
        self.logger.apikey = dev.apikey
        self.logger.serverurl = serverurl

        # Finally, write the compatibility file.
        files.writeJSON(self.versionfile, {
            "connectordb": self.cdbversion,  # The version of ConnectorDB
            "version": 1,   # The laptoplogger version
            "managed": self.ismanaging,  # Whether or not we are managing a local database
        })

    def create(self, username, password, devicename, isprivate):
        self.manager.create(username, password)
        self.manager.start()
        self.ismanaging = True

        try:
            # On create, we don't overwrite - the only existing names are
            # really invalid
            def deviceOverwriteCallback(dname):
                return False
            self.login(username, password, devicename, "http://localhost:8000",
                       isprivate, deviceOverwriteCallback)
        except:
            self.manager.stop()
            self.ismanaging = False
            self.manager.remove()
            raise

    def createAndImport(self, importfolder, username, password, devicename, isprivate, deviceOverwriteCallback):
        self.manager.createAndImport(username, password, importfolder)
        self.ismanaging = True  # createAndImport leaves the database running

        try:
            self.login(username, password, devicename, "http://localhost:8000",
                       isprivate, deviceOverwriteCallback)
        except:
            self.manager.stop()
            self.ismanaging = False
            self.manager.remove()
            raise

if __name__ == "__main__":
    # https://stackoverflow.com/questions/954834/how-do-i-use-raw-input-in-python-3-1
    try:
        input = raw_input
    except NameError:
        pass

    import getpass
    import argparse
    import sys
    import time
    import signal

    arg_parser = argparse.ArgumentParser(
        description="Gathers usage data from computer, and optionally manages a ConnectorDB database.")
    arg_parser.add_argument("-l", "--loglevel", default="INFO",
                            help="The level at which to print debug statements to log")
    arg_parser.add_argument("-o", "--logfile", default="",
                            help="File to use to write logs")

    arg_parser.add_argument("-f", "--folder", default=files.getDefaultFolderLocation(),
                            help="Location in which to put all of LaptopLogger's data")

    args = arg_parser.parse_args()
    # Set up logging, so that we don't have to worry about it later
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=numeric_level, filename=args.logfile)

    def createCallback(dm):
        # This callback is run if the DataManager is not set up yet.
        c = "nope"
        if dm.manager is not None:
            print("""
ConnectorDB Logging is not set up. Please choose:

    1) Log into existing ConnectorDB server
    2) Create a locally managed ConnectorDB instance 
    3) Import a ConnectorDB instance from folder
    q) Quit
""")
            while c not in ["", "1", "2", "3", "q"]:
                c = input("Choice [DEFAULT: 2]: ").strip()

            if c == "q":
                sys.exit(1)
            if c == "":
                c = "2"
        else:
            print("Log into existing ConnectorDB instance")
            c = "1"
        folder = ""
        server = ""

        if c == "3":
            folder = input("Import folder: ")
            if not os.path.isdir(folder):
                print("This folder does not exist.")
                sys.exit(1)
        if c == "1":
            server = input("Server [DEFAULT: %s]:" %
                           (connectordb.CONNECTORDB_URL,)).strip()
            if server == "":
                server = connectordb.CONNECTORDB_URL

        username = input("ConnectorDB Username: ").strip()
        password = getpass.getpass()
        if c != "1":
            if password != getpass.getpass("Repeat Password: "):
                print("Passwords do not match!")
                sys.exit(2)
        device = input("Device Name [DEFAULT: laptop]: ").strip()
        if device == "":
            device = "laptop"

        def deviceOverwriteCallback(device):
            print("The device already exists. Overwrite?")
            return input("y/n [n]: ") == "y"

        if c == "1":
            dm.login(username, password, device, server,
                     True, deviceOverwriteCallback)
        elif c == "2":
            dm.create(username, password, device, True)
        else:
            dm.createAndImport(folder, username, password,
                               device, True, deviceOverwriteCallback)

    dm = DataManager(args.folder, createCallback)

    def signalHandler(a, b):
        logging.warn("Caught Ctrl+c. Exiting application.")
        dm.exit()
        sys.exit(1)
    signal.signal(signal.SIGINT, signalHandler)

    while True:
        time.sleep(1)
