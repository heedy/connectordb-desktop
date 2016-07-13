import sys

QtGui = None
try:
    from PyQt5 import QtWidgets
    QtGui = QtWidgets
except:
    print("Couldn't find QT5 - falling back to Qt4")
    from PyQt4 import QtGui

import webbrowser
from connectordb import ConnectorDB

#Import the necessary GUI elements
from guitray import MainTray
from guilogin import LoginWindow

#Import the laptop logger
from laptoplogger import LaptopLogger

#Returns whether the given api key is valid
def canLogin(apikey):
    try:
        ConnectorDB(apikey)
        return True
    except:
        return False

def runapp():
    app = QtGui.QApplication(sys.argv)

    # Now set up the laptop logger
    l = LaptopLogger()

    tray = MainTray(l,app)

    def loginCallback():
        tray.show()
        tray.start()
        tray.startsync()

        #Open the browser to start off.
        webbrowser.open(l.cache.serverurl)



    lw = None
    if l.cache.apikey == "":
        lw = LoginWindow(l,loginCallback)
        lw.show()
    else:
        tray.show()

    sys.exit(app.exec_())

if __name__=="__main__":
    runapp()
