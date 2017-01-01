
try:
    from PyQt5 import QtCore, QtWidgets
    from PyQt5.QtGui import QIcon, QCursor
    QtGui = QtWidgets
except:
    from PyQt4 import QtGui, QtCore
    QIcon = QtGui.QIcon
    QCursor = QtGui.QCursor

import sys
import os
import logging
import threading
import time
import datetime
import webbrowser


def pretty_time_delta(seconds):
    # https://gist.github.com/thatalextaylor/7408395
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

    def __init__(self, dm, parent=None):
        self.dm = dm

        self.dm.logger.onsyncfail = self.onsyncfail
        self.dm.logger.onsync = self.onsyncsuccess

        # We need a widget to do shit. So make a widget...
        self.w = QtGui.QWidget()

        # Load the icons
        mydir = os.path.dirname(__file__)
        self.idleicon = QIcon(os.path.join(mydir, 'resources/logo.png'))
        self.gathericon = QIcon(os.path.join(
            mydir, 'resources/gatheringicon.png'))
        self.failicon = QIcon(os.path.join(mydir, "resources/failicon.png"))

        # This tells us whether to update the icon
        self.previcon = None

        self.curicon = self.idleicon    # TODO: fix this
        if self.dm.isgathering:
            self.curicon = self.gathericon
        super(MainTray, self).__init__(self.curicon, parent)

        # This sets up the handler for when the icon is clicked
        self.activated.connect(self.onclick)

        self.menu = QtGui.QMenu()

        # Set up the list of plugins
        for p in self.dm.plugins:
            gAction = self.menu.addAction(p)
            gAction.setCheckable(True)
            gAction.setToolTip(self.dm.plugins[p].description)
            gAction.triggered.connect(
                lambda a=None, p=p, gA=gAction: self.toggleplugin(p, gA))
            gAction.hovered.connect(
                lambda a=None, p=p, gA=gAction: self.togglepluginhover(p, gA))
            if p in self.dm.currentplugins:
                gAction.setChecked(True)

        self.menu.addSeparator()

        gatherAction = self.menu.addAction("Gather Data")
        gatherAction.setCheckable(True)
        gatherAction.setToolTip(
            "Whether or not laptoplogger should gather data")
        gatherAction.triggered.connect(self.gathertoggled)
        if self.dm.isgathering:
            gatherAction.setChecked(True)
        self.gatherAction = gatherAction

        syncAction = self.menu.addAction("Auto Sync")
        syncAction.setCheckable(True)
        syncAction.setToolTip(
            "Whether or not laptoplogger should automatically sync to server")
        syncAction.triggered.connect(self.synctoggled)
        if self.dm.issyncing:
            syncAction.setChecked(True)
        self.syncAction = syncAction

        self.menu.addSeparator()

        syncNowAction = self.menu.addAction("Sync Now")
        syncNowAction.setToolTip("Sync with the ConnectorDB server right now.")
        syncNowAction.triggered.connect(self.syncnow)

        self.menu.addSeparator()

        stop1h = self.menu.addAction("Stop for 1 hour")
        stop1h.setToolTip("Stop gathering data for 1 hour")
        stop1h.triggered.connect(self.stop1h)

        stop15 = self.menu.addAction("Stop for 15 minutes")
        stop15.setToolTip("Stop gathering data for 15 minutes")
        stop15.triggered.connect(self.stop15)

        if self.dm.ismanaging:
            # If we are using a managed database, add an export option
            self.menu.addSeparator()
            exportAction = self.menu.addAction("Export")
            exportAction.triggered.connect(self.exportButtonPressed)

        self.menu.addSeparator()

        exitAction = self.menu.addAction("Exit")
        exitAction.triggered.connect(self.exitButtonPressed)

        self.setContextMenu(self.menu)

        # Number of seconds to wait before toggling gather.
        # Used to allow the "Stop for 15 minutes" and like buttons
        self.waitgather = 0

        # Now set up the main timer (has to tick once a second, since it is
        # used for multiple things)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timeraction)
        self.timer.start(1000)

    def onclick(self, reason):
        """Called when the user clicks on the tray icon"""
        if reason == self.Trigger:
            webbrowser.open(self.dm.logger.serverurl)
            # Sync too, so user has most recent data
            self.dm.logger.sync()

    def toggleplugin(self, name, action):
        """ Enables or disables the given gatherer """
        if action.isChecked():
            self.dm.enablePlugin(name)
        else:
            self.dm.disablePlugin(name)

    def togglepluginhover(self, name, action):
        QtGui.QToolTip.showText(QCursor.pos(), action.toolTip())

    def exportButtonPressed(self):
        logging.info("Choose export folder")
        file = str(QtGui.QFileDialog.getExistingDirectory(
            self.w, "Select Export Directory"))
        logging.debug("Using folder " + file)

        # Now the messed up part: we need to delete the folder, since the
        # export creates an export directory
        if file != "":
            try:
                os.rmdir(file)
            except:
                logging.error("Could not remove directory in prep for export")
                QtGui.QMessageBox.critical(
                    self.w, "Nonempty Directory", "Export folder must be empty!")
                return
            try:
                self.dm.manager.exportDatabase(file)
            except Exception as e:
                logging.error(str(e))
                QtGui.QMessageBox.critical(self.w, "Export Failed", str(e))
                return
        logging.info("Export Complete")
        QtGui.QMessageBox.information(
            self.w, "Export Complete", "Export Finished!")

    def exitButtonPressed(self):
        logging.info("Exiting...")
        self.hide()
        self.dm.exit()
        sys.exit(0)

    def gathertoggled(self):
        if self.gatherAction.isChecked():
            self.waitgather = 0
            self.start()
        else:
            self.stop()

    def synctoggled(self):
        if self.syncAction.isChecked():
            self.startsync()
        else:
            self.stopsync()

    def syncnow(self):
        logging.info("started sync")
        thr = threading.Thread(target=self.dm.logger.sync)
        thr.start()

    def timeraction(self):
        """Called periodically to update the tooltip"""
        if self.previcon != self.curicon:
            self.setIcon(self.curicon)
            self.previcon = self.curicon

        tooltiptext = "ConnectorDB - "

        if self.waitgather > 0:
            self.waitgather -= 1
            if self.waitgather == 0:
                # Start gathering data
                self.gatherAction.setChecked(True)
                self.gathertoggled()
            else:
                tooltiptext += "Stopped for " + \
                    pretty_time_delta(self.waitgather) + ", "

        if self.dm.logger.lastsynctime > 0.0:
            tooltiptext += "synced " + \
                pretty_time_delta(
                    time.time() - self.dm.logger.lastsynctime) + " ago, "
        tooltiptext += str(len(self.dm.logger)) + " in cache."

        self.setToolTip(tooltiptext)

    def gathertoggled(self):
        if self.gatherAction.isChecked():
            self.waitgather = 0
            self.start()
        else:
            self.stop()

    def synctoggled(self):
        if self.syncAction.isChecked():
            self.startsync()
        else:
            self.stopsync()

    def syncnow(self):
        logging.info("started sync")
        thr = threading.Thread(target=self.dm.logger.sync)
        thr.start()

    def stop15(self):
        logging.info("Stop for 15 minutes")
        self.gatherAction.setChecked(False)
        self.waitgather = 15 * 60
        self.gathertoggled()

    def stop1h(self):
        logging.info("Stop for 1 hour")
        self.gatherAction.setChecked(False)
        self.waitgather = 60 * 60
        self.gathertoggled()

    def onsyncfail(self, c):
        # Set the icon to red
        self.curicon = self.failicon
        logging.info("SYNC FAIL: " + str(c))

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
        self.dm.startgathering()

        # set the check box correctly
        self.gatherAction.setChecked(True)

        if self.supportsMessages():
            self.showMessage("LaptopLogger", "Started Gathering Data")

    def startsync(self):
        logging.info("Start sync")

        # Start the actual logger
        self.dm.startsync()

        # set the check box correctly
        self.syncAction.setChecked(True)

    def stop(self):
        logging.info("Stop logging")
        # Set the icon to idle
        self.curicon = self.idleicon
        self.setIcon(self.curicon)

        # set the check box correctly
        self.gatherAction.setChecked(False)

        self.dm.stopgathering(self.waitgather == 0)
        if self.supportsMessages():
            self.showMessage("LaptopLogger", "Data gathering stopped")

    def stopsync(self):
        logging.info("Stop sync")
        self.syncAction.setChecked(False)

        self.dm.stopsync()
