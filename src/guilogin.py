
import logging
import os
import sys
import files
import cdbmanager
import datamanager
import connectordb
import webbrowser

try:
    from PyQt5 import QtWidgets, QtCore, uic
    from PyQt5.QtGui import QPixmap, QIcon
    QtGui = QtWidgets

except:
    from PyQt4 import QtGui, QtCore, uic
    QPixmap = QtGui.QPixmap
    QIcon = QtGui.QIcon


class LoginForm(QtGui.QDialog):

    def __init__(self, folder, callback, parent=None):
        super(LoginForm, self).__init__(parent=parent)
        self.folder = folder
        self.callback = callback
        mydir = os.path.dirname(__file__)
        uic.loadUi(os.path.join(mydir, "resources/login.ui"), self)

        logofile = os.path.join(mydir, "resources/logo.png")
        self.logo.setPixmap(QPixmap(logofile))
        self.setWindowIcon(QIcon(logofile))

        # The default device text
        self.connect_devicename.setText("laptop")
        self.create_devicename.setText("laptop")
        self.import_devicename.setText("laptop")

        # The ConnectorDB database url
        self.connect_server.setText(connectordb.CONNECTORDB_URL)

        # Set the login button callback
        self.login_button.clicked.connect(self.login)
        self.create_button.clicked.connect(self.create)
        self.import_button.clicked.connect(self.importDatabase)

        self.choose_folder_button.clicked.connect(self.chooseFolder)

        # Set the connectordb version number if there is a version
        self.versionNumber = cdbmanager.version()
        self.version.setText(self.versionNumber)

        self.setWindowTitle("ConnectorDB Setup")

        # Only enable the "create" and "import" tabs if the executable is found
        if files.getConnectorDB() is None:
            logging.warning(
                "Couldn't find ConnectorDB executable. Not showing create/import tabs")
            self.tabWidget.removeTab(2)
            self.tabWidget.removeTab(0)

    def runCallback(self, dm):
        # Open the server location in browser, so that user can log in
        webbrowser.open(dm.logger.serverurl)
        self.callback(dm)

    def closeEvent(self, event):
        logging.warn("Exiting")
        sys.exit(1)

    def disableButtons(self):
        self.login_button.setEnabled(False)
        self.create_button.setEnabled(False)
        self.import_button.setEnabled(False)

    def enableButtons(self):
        self.login_button.setEnabled(True)
        self.create_button.setEnabled(True)
        self.import_button.setEnabled(True)

    def chooseFolder(self):
        logging.info("Find Folder")
        file = str(QtGui.QFileDialog.getExistingDirectory(
            self, "Select Import Directory"))
        logging.debug("Using folder " + file)
        self.import_location.setText(file)

    def validateUserDevice(self, usrname, passwd, device):
        if usrname == "":
            QtGui.QMessageBox.critical(
                self.sender(), "Blank Username", "Please type in your ConnectorDB username!")
            return False
        if passwd == "":
            QtGui.QMessageBox.critical(self.sender(
            ), "Blank Password", "Please type in your ConnectorDB user's password!")
            return False
        if device == "":
            QtGui.QMessageBox.critical(
                self.sender(), "Blank Device", "No name was given to your device!")
            self.login_button.setEnabled(True)
            return False
        return True

    def deviceOverwriteCallback(self, devicename):
        self.show()
        reply = QtGui.QMessageBox.question(self.sender(
        ), "Device Exists", "This device already exists. Continue?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        self.hide()
        return reply == QtGui.QMessageBox.Yes

    def login(self):
        logging.info("Running Login")
        self.disableButtons()
        usrname = str(self.connect_username.text())
        passwd = str(self.connect_password.text())
        server = str(self.connect_server.text())
        device = str(self.connect_devicename.text())
        isprivate = self.connect_deviceprivate.isChecked()

        if not server.startswith("http://") and not server.startswith("https://"):
            logging.warn("Invalid server")
            QtGui.QMessageBox.critical(
                self.sender(), "Invalid Server", "The given server name is not valid!")
            self.enableButtons()
            return
        if not self.validateUserDevice(usrname, passwd, device):
            logging.warn("Username/password/devicename validation failed")
            self.enableButtons()
            return

        logging.debug("Basic validation complete")

        # Now create the DataManager

        def loginCallback(dm):
            dm.login(usrname, passwd, device, server,
                     isprivate, self.deviceOverwriteCallback)

        dm = None
        self.hide()

        try:
            dm = datamanager.DataManager(self.folder, loginCallback)
        except Exception as e:
            self.show()
            logging.error(str(e))
            QtGui.QMessageBox.critical(
                self.sender(), "Login Failed", str(e))
            self.enableButtons()
            return
        self.enableButtons()
        # Run the callback, signalling that setup is finished :D
        self.runCallback(dm)

    def create(self):
        logging.info("Running Create")

        self.disableButtons()
        usrname = str(self.create_username.text())
        passwd = str(self.create_password.text())
        passwd2 = str(self.create_password2.text())
        device = str(self.create_devicename.text())
        isprivate = self.create_deviceprivate.isChecked()

        if not self.validateUserDevice(usrname, passwd, device):
            logging.warn("Username/password/devicename validation failed")
            self.enableButtons()
            return
        if passwd == "" or passwd != passwd2:
            logging.warn("Invalid or blank password given")
            QtGui.QMessageBox.critical(
                self.sender(), "Invalid Password", "Passwords either blank or don't match.")
            self.enableButtons()
            return

        logging.debug("Basic validation complete")

        # Now create the DataManager

        def createCallback(dm):
            dm.create(usrname, passwd, device, isprivate)

        dm = None
        self.hide()

        try:
            dm = datamanager.DataManager(self.folder, createCallback)
        except Exception as e:
            self.show()
            logging.error(str(e))
            QtGui.QMessageBox.critical(
                self.sender(), "Create Failed", str(e))
            self.enableButtons()
            return
        self.enableButtons()
        # Run the callback, signalling that setup is finished :D
        self.runCallback(dm)

    def importDatabase(self):
        logging.info("Running Import")

        self.disableButtons()
        usrname = str(self.import_username.text())
        passwd = str(self.import_password.text())
        passwd2 = str(self.import_password2.text())
        device = str(self.import_devicename.text())
        folder = str(self.import_location.text())
        isprivate = self.import_deviceprivate.isChecked()

        if not os.path.isdir(folder):
            logging.warn("Could not find the given folder")
            QtGui.QMessageBox.critical(
                self.sender(), "Invalid Import Location", "The given path does not exist")
            self.enableButtons()
            return

        if not self.validateUserDevice(usrname, passwd, device):
            logging.warn("Username/password/devicename validation failed")
            self.enableButtons()
            return
        if passwd == "" or passwd != passwd2:
            logging.warn("Invalid or blank password given")
            QtGui.QMessageBox.critical(
                self.sender(), "Invalid Password", "Passwords either blank or don't match.")
            self.enableButtons()
            return

        logging.debug("Basic validation complete")

        # Now create the DataManager

        def importCallback(dm):
            dm.createAndImport(folder, usrname, passwd, device,
                               isprivate, self.deviceOverwriteCallback)

        dm = None
        self.hide()

        try:
            dm = datamanager.DataManager(self.folder, importCallback)
        except Exception as e:
            self.show()
            logging.error(str(e))
            QtGui.QMessageBox.critical(
                self.sender(), "Import Failed", str(e))
            self.enableButtons()
            return
        self.enableButtons()
        # Run the callback, signalling that setup is finished :D
        self.runCallback(dm)
