"""
    The LaptopLogger gathers computer usage data in the background, and optionally manages
    a local ConnectorDB database. 

    The LaptopLogger creates an icon in the system tray, which upon right click offers up several
    options. A left-click opens up the connected ConnectorDB instance in the browser.


    Internals:
        The GUI uses the underlying DataManager to handle all functionality. You can directly use 
        DataManager by running 
            python datamanager.py
        which will run headless.

        The LaptopLogger simply adds a GUI. The main issue with GUI in general is that it is callback-based,
        which means that when initially running laptoplogger, we don't actually know if DataManager will initialize,
        or whether it will need new information. The LaptopLogger therefore checks if the DataManager is set up itself
        before running it, so that it can perform initialization asynchronously if necessary.
"""

import logging
import argparse
import sys
import signal
import os

import files
from datamanager import DataManager
from guilogin import LoginForm
from guimaintray import MainTray


def runapp():

    # Run the entire program in a big try catch block, so that we can log any
    # error that shows up
    try:

        # This variable is used to hold the main DataManager instance. It will be initialized manually
        # based on the state to allow simple setup without complex code in the
        # DataManager itself
        dm = None

        # Allow catching ctrl + c when running in terminal
        def signalHandler(a, b):
            global dm
            logging.warning("Caught Ctrl+c. Exiting application.")
            if dm is not None:
                logging.info("Shutting down DataManager")
                dm.exit()
                dm = None
            sys.exit(0)
        signal.signal(signal.SIGINT, signalHandler)

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

        try:
            from PyQt5 import QtWidgets, QtCore
            QtGui = QtWidgets
        except:
            logging.warning("Couldn't find QT5 - falling back to Qt4")
            from PyQt4 import QtGui, QtCore

        app = QtGui.QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        # We need to run this timer to allow the app to correctly catch ctrl c
        # because QT takes over python.
        # http://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co
        timer = QtCore.QTimer()
        timer.start(500)
        # Let the interpreter run each 500 ms.
        timer.timeout.connect(lambda: None)

        # This variable will hold the main tray icon that is used to control the LaptopLogger. it is initialized in the function
        # shown below. This callback-based setup is because we need to know several pieces of information from the login screen
        # before we can initialize the DataManager which is needed for the
        # MainTray to work
        maintray = None

        def initializeMainTray(dataManager):
            logging.info("Setting up tray icon")
            global dm, maintray
            dm = dataManager
            maintray = MainTray(dm)
            maintray.show()

        # We can't use DataManager directly here, since QT must run in its event loop. This means that we must initialize
        # the setup (login) dialog and main tray so that they do not block. This means that we need to perform a bit of gymnastics
        # so that the DataManager is initialized without ever blocking. We do this
        # by manually checking if the version file exists.
        loginForm = None
        if os.path.exists(os.path.join(args.folder, "laptoplogger.json")):
            # Everything is assumed to exist. We can therefore set dm directly, since it is initialized
            # The create callback is assumed to be unnecessary
            initializeMainTray(DataManager(args.folder, lambda x: None))

        else:
            logging.info(
                "Could not find connectordb.json. Showing login options")
            # The LaptopLogger is assumed not to be set up. We show the setup
            # options, and after the login completes successfully, we set the main DataManager
            # and show the main tray icon through a callback

            loginForm = LoginForm(args.folder, initializeMainTray)
            loginForm.show()

        sys.exit(app.exec_())

    except Exception as e:
        logging.critical(str(e))

if __name__ == "__main__":
    runapp()
