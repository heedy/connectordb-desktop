from PyQt4 import QtGui,QtCore
import sys
import os
import logging
import threading
import time
import datetime

# https://gist.github.com/thatalextaylor/7408395
def pretty_time_delta(seconds):
    sign_string = '-' if seconds < 0 else ''
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%s%dd%dh%dm%ds' % (sign_string, days, hours, minutes, seconds)
    elif hours > 0:
        return '%s%dh%dm%ds' % (sign_string, hours, minutes, seconds)
    elif minutes > 0:
        return '%s%dm%ds' % (sign_string, minutes, seconds)
    else:
        return '%s%ds' % (sign_string, seconds)

class MainTray(QtGui.QSystemTrayIcon):
    def __init__(self,logger,parent=None):
        self.logger = logger

        self.logger.cache.onsyncfail = self.onsyncfail
        self.logger.cache.onsync = self.onsyncsuccess

        #Load the icons
        mydir = os.path.dirname(__file__)
        self.idleicon = QtGui.QIcon(os.path.join(mydir, 'resources/logo.png'))
        self.gathericon = QtGui.QIcon(os.path.join(mydir, 'resources/gatheringicon.png'))
        self.failicon = QtGui.QIcon(os.path.join(mydir,"resources/failicon.png"))

        self.curicon = self.idleicon
        if self.logger.cache.syncthread is not None:
            self.curicon = self.gathericon
        super(MainTray,self).__init__(self.curicon,parent)

        self.menu = QtGui.QMenu()

        gatherAction = self.menu.addAction("Gather Data")
        gatherAction.setCheckable(True)
        gatherAction.triggered.connect(self.gathertoggled)
        if self.logger.cache.syncthread is not None:
            gatherAction.setChecked(True)
        self.gatherAction = gatherAction

        syncAction = self.menu.addAction("Sync Now")
        syncAction.triggered.connect(self.syncnow)

        exitAction = self.menu.addAction("Exit")
        exitAction.triggered.connect(self.exitButtonPressed)

        self.setContextMenu(self.menu)

        #Now set up the icon updating timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timeraction)
        self.timer.start(1000)
    def timeraction(self):
        self.setIcon(self.curicon)
        self.setToolTip("ConnectorDB last sync " + pretty_time_delta(time.time()-self.logger.cache.lastsynctime)+" ago.")


    def exitButtonPressed(self):
        sys.exit(0)

    def gathertoggled(self):
        if self.gatherAction.isChecked():
            self.start()
        else:
            self.stop()

    def syncnow(self):
        logging.info("started sync")
        thr = threading.Thread(target=self.logger.cache.sync)
        thr.start()

    def onsyncfail(self,c):
        # Set the icon to red
        self.curicon = self.failicon
        logging.info("SYNC FAIL: "+str(c))
    def onsyncsuccess(self):
        logging.info("SYNC SUCCESS")
        # Set the icon to the correct value upon synchronization
        if self.gatherAction.isChecked():
            self.curicon = self.gathericon
        else:
            self.curicon = self.idleicon

    def start(self):
        logging.info("Start logging")
        self.curicon = self.gathericon
        # Set the icon to green
        self.setIcon(self.curicon)

        # Start the actual logger
        self.logger.start()

        # set the check box correctly
        self.gatherAction.setChecked(True)

        if self.supportsMessages():
            self.showMessage("LaptopLogger","Started Gathering Data")

    def stop(self):
        logging.info("Stop logging")
        # Set the icon to idle
        self.curicon = self.idleicon
        self.setIcon(self.curicon)

        # set the check box correctly
        self.gatherAction.setChecked(False)

        self.logger.stop()
        if self.supportsMessages():
            self.showMessage("LaptopLogger","Data gathering stopped")
