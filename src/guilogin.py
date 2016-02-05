from PyQt4 import QtGui, QtCore, uic
import os
import sys

import logging
import platform
import connectordb

#logging.basicConfig(level=logging.DEBUG,filename="cache.log")
logging.basicConfig(level=logging.DEBUG)

class LoginWindow(QtGui.QDialog):
    def __init__(self,logger, logincallback, parent=None):
        self.logincallback = logincallback #We call this on successful login
        self.logger = logger
        super(LoginWindow,self).__init__(parent = parent)
        mydir = os.path.dirname(__file__)
        uic.loadUi(os.path.join(mydir,"resources/login.ui"),self)


        logofile = os.path.join(mydir,"resources/logo.png")
        self.logopicture.setPixmap(QtGui.QPixmap(logofile))
        self.setWindowIcon(QtGui.QIcon(logofile))

        #The default device text
        self.device.setText(platform.node())

        #The ConnectorDB database url
        self.server.setText(connectordb.CONNECTORDB_URL)

        #Set the login button callback
        self.okbutton.clicked.connect(self.login)

    def closeEvent(self,event):
        sys.exit(1)

    def login(self):
        # The login button was clicked
        self.okbutton.setEnabled(False)

        # First we make sure that there is a username given
        usrname = str(self.username.text())
        if usrname == "":
            QtGui.QMessageBox.critical(self.sender(),"Blank Username","Please type in your ConnectorDB username!")
            self.okbutton.setEnabled(True)
            return
        passwd = str(self.password.text())
        if passwd == "":
            QtGui.QMessageBox.critical(self.sender(),"Blank Password","Please type in your ConnectorDB user's password!")
            self.okbutton.setEnabled(True)
            return

        device = str(self.device.text())
        if device == "":
            QtGui.QMessageBox.critical(self.sender(),"Blank Device","No name was given to your device!")
            self.okbutton.setEnabled(True)
            return

        server = str(self.server.text())
        if not server.startswith("http://") and not server.startswith("https://"):
            QtGui.QMessageBox.critical(self.sender(),"Invalid Server","The given server name is not valid!")
            self.okbutton.setEnabled(True)
            return

        self.okbutton.setEnabled(False)

        try:
            cdb = connectordb.ConnectorDB(usrname.strip(),passwd,server)
            dev = cdb.user[device]
            if not dev.exists():
                dev.create(self.ispublic.isChecked())
            self.logger.cache.apikey = dev.apikey
            self.logger.cache.serverurl = server
        except Exception as e:
            self.okbutton.setEnabled(True)
            QtGui.QMessageBox.critical(self.sender(),"Could not Log in!",str(e))
            return
        self.logincallback()
        self.okbutton.setEnabled(True)
        self.hide()
