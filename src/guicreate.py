
try:
    from PyQt5 import QtWidgets, QtCore, uic
    QtGui = QtWidgets
except:
    print("Couldn't find QT5 - falling back to Qt4")
    from PyQt4 import QtGui, QtCore, uic
import os
import cdbmanager
import logging

class CreateWindow(QtGui.QDialog):
    def __init__(self,parent=None):
        super(CreateWindow,self).__init__(parent = parent)
        mydir = os.path.dirname(__file__)
        uic.loadUi(os.path.join(mydir,"resources/create.ui"),self)


class CreateThread(QtCore.QThread):
    finished = QtCore.pyqtSignal(bool)
    def run(self):
        result = False
        try:
            result = (cdbmanager.Manager(self.folder).create(self.username,self.password)==0)
        except:
            pass
        self.finished.emit(result)
# Make sure the thread or window are not destroyed
t=None
l=None
def create(folder,username,password,callback):
    global t
    global l
    logging.info("Creating database at "+folder + " with user "+username)

    l = CreateWindow()

    l.show()

    def create_signal(result):
        global l
        logging.info("Create completed")
        l.hide()
        callback(result)

    t = CreateThread()
    t.username = username
    t.folder = folder
    t.password = password
    t.finished.connect(create_signal)
    t.start()
