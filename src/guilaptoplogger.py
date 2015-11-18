import sys
from PyQt4 import QtGui

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

if __name__=="__main__":
	app = QtGui.QApplication(sys.argv)

	# Now set up the laptop logger
	l = LaptopLogger()
	
	tray = MainTray(l,app)

	def loginCallback():
		tray.show()
		tray.start()



	lw = None
	if l.cache.apikey == "":
		lw = LoginWindow(l,loginCallback)
		lw.show()
	else:
		tray.show()

	sys.exit(app.exec_())
