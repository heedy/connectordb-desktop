
try:
    from PyQt5 import QtWidgets, QtCore, uic
    from PyQt5.QtGui import QPixmap, QIcon
    QtGui = QtWidgets
except:
    print("Couldn't find QT5 - falling back to Qt4")
    from PyQt4 import QtGui, QtCore, uic
    QPixmap = QtGui.QPixmap
    QIcon = QtGui.QIcon

import os
import sys

import logging
import platform
import connectordb
import files
import logging
import guicreate

# The version to show in the login window
version = "0.3.0a2"

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
        self.logo.setPixmap(QPixmap(logofile))
        self.setWindowIcon(QIcon(logofile))

        #The default device text
        self.connect_devicename.setText("laptop")
        self.create_devicename.setText("laptop")

        #The ConnectorDB database url
        self.connect_server.setText(connectordb.CONNECTORDB_URL)

        #Set the login button callback
        self.login_button.clicked.connect(self.login)
        self.create_button.clicked.connect(self.create)

        # Set the connectordb version
        self.version.setText(version)

        # Only enable the "create" tab if the executable is found
        if files.getConnectorDB() is None:
            logging.info("Couldn't find ConnectorDB executable. Not showing create tab.")
            self.tabWidget.removeTab(1)

    def closeEvent(self,event):
        sys.exit(1)

    def login(self):
        # The login button was clicked
        self.login_button.setEnabled(False)

        # First we make sure that there is a username given
        usrname = str(self.connect_username.text())
        if usrname == "":
            QtGui.QMessageBox.critical(self.sender(),"Blank Username","Please type in your ConnectorDB username!")
            self.login_button.setEnabled(True)
            return
        passwd = str(self.connect_password.text())
        if passwd == "":
            QtGui.QMessageBox.critical(self.sender(),"Blank Password","Please type in your ConnectorDB user's password!")
            self.login_button.setEnabled(True)
            return

        device = str(self.connect_devicename.text())
        if device == "":
            QtGui.QMessageBox.critical(self.sender(),"Blank Device","No name was given to your device!")
            self.login_button.setEnabled(True)
            return

        server = str(self.connect_server.text())
        if not server.startswith("http://") and not server.startswith("https://"):
            QtGui.QMessageBox.critical(self.sender(),"Invalid Server","The given server name is not valid!")
            self.login_button.setEnabled(True)
            return

        self.login_button.setEnabled(True)
        self.hide()

        self.runsetup(usrname,passwd,device,server,self.connect_deviceprivate.isChecked())

    def create(self):
        self.create_button.setEnabled(False)

        # First we make sure that there is a username given
        usrname = str(self.create_username.text())
        if usrname == "":
            QtGui.QMessageBox.critical(self.sender(),"Blank Username","Please type in your ConnectorDB username!")
            self.create_button.setEnabled(True)
            return
        passwd = str(self.create_password.text())
        passwd2 = str(self.create_password2.text())
        if passwd == "" or passwd!=passwd2:
            QtGui.QMessageBox.critical(self.sender(),"Invalid Password","Passwords either blank or don't match.")
            self.create_button.setEnabled(True)
            return

        device = str(self.create_devicename.text())
        if device == "":
            QtGui.QMessageBox.critical(self.sender(),"Blank Device","No name was given to your device!")
            self.create_button.setEnabled(True)
            return

        self.create_button.setEnabled(True)
        self.hide()

        self.usrname = usrname
        self.passwd = passwd
        self.device = device

        # Now create the database
        guicreate.create(self.logger.localdir,usrname.strip(),passwd,self.create_callback)

    def create_callback(self,success):
        if not success:
            self.show()
            QtGui.QMessageBox.critical(self,"Create Failed","Failed to create ConnectorDB database. Try running the laptoplogger in command line to see log messages.")
        else:
            # runlocal must be true for the database to start
            d = self.logger.cache.data
            d["runlocal"] = True
            self.logger.cache.data = d
            # Since we manage the database, notify the logger to start ConnectorDB
            if not self.logger.runLocal():
                QtGui.QMessageBox.critical(self,"Could not start ConnectorDB","Failed to start ConnectorDB database after creating. Try running in terminal to see log messages")
                d = self.logger.cache.data
                d["runlocal"] = False
                self.logger.cache.data = d
            else:
                self.runsetup(self.usrname,self.passwd,self.device,"http://localhost:8000",self.create_deviceprivate.isChecked())
                

    def runsetup(self,usrname,passwd,device,server,isprivate):
        try:
            cdb = connectordb.ConnectorDB(usrname.strip(),passwd,server)
            dev = cdb.user[device]
            if not dev.exists():
                dev.create(public=not isprivate,description="LaptopLogger")
            else:
                self.show()
                reply = QtGui.QMessageBox.question(self.sender(),"Device Exists","This device already exists. Continue?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                if reply == QtGui.QMessageBox.No:
                    raise Exception("Device Exists")
                self.hide()

            self.logger.cache.apikey = dev.apikey
            self.logger.cache.serverurl = server
        except Exception as e:
            self.show()
            QtGui.QMessageBox.critical(self.sender(),"Could not Log in!",str(e))
            return False
        # Run the callback that initializes the streams
        self.logincallback()
        return True
