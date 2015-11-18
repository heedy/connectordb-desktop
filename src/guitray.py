from PyQt4 import QtGui
import sys
import os
import logging
import threading
class MainTray(QtGui.QSystemTrayIcon):
    def __init__(self,logger,parent=None):
        self.logger = logger

        self.logger.cache.onsyncfail = self.onsyncfail

        #Load the icons
        mydir = os.path.dirname(__file__)
        self.idleicon = QtGui.QIcon(os.path.join(mydir, 'resources/logo.png'))
        self.gathericon = QtGui.QIcon(os.path.join(mydir, 'resources/gatheringicon.png'))
        self.failicon = QtGui.QIcon(os.path.join(mydir,"resources/failicon.png"))

        curicon = self.idleicon
        if self.logger.cache.syncthread is not None:
            curicon = self.gathericon
        super(MainTray,self).__init__(curicon,parent)

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
    def exitButtonPressed(self):
        sys,exit(0)

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
        self.setIcon(self.failicon)

    def start(self):
        logging.info("Start logging")
        # Set the icon to green
        self.setIcon(self.gathericon)

        # Start the actual logger
        self.logger.start()

        # set the check box correctly
        self.gatherAction.setChecked(True)

        if self.supportsMessages():
            self.showMessage("LaptopLogger","Started Gathering Data")

    def stop(self):
        logging.info("Stop logging")
        # Set the icon to idle
        self.setIcon(self.idleicon)

        # set the check box correctly
        self.gatherAction.setChecked(False)

        self.logger.stop()
        if self.supportsMessages():
            self.showMessage("LaptopLogger","Data gathering stopped")
