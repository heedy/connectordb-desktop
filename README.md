The Laptop Logger
==================

This is the [ConnectorDB](https://connectordb.github.io) frontend for logging the things you do on your PC. The LaptopLogger includes a headless version for running on servers, and a cross-platform QT GUI for use on your primary machine.

The laptoplogger has a simple plugin system, such that anyone can track the system stats they want with only a few lines of code.

## Logging
The built-in plugins log several things, but the logged quantities depend on the operating system.
By default, we try to have plugins be consistent across OS, but it is not a requirement.

Our goal is to support at the very least:
- number of keypresses - allows to measure how much you are typing
	- [x] windows
	- [x] linux
	- [ ] osx
- Number of mouse clicks - another measure of activity
	- [x] windows
	- [x] linux
	- [ ] osx
- Active application - titlebar text
	- [x] windows
	- [x] linux
	- [ ] osx


<img src="https://raw.githubusercontent.com/connectordb/connectordb-laptoplogger/master/laptoplogger.png" width="300"/>


## Issues
- In some cases, login window has misaligned fonts.

## Installing

### Windows
Use the release installer (go to releases tab in github). If the installer fails, you can get it running
by installing Python on your machine, installing the following packages from [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/):
```
apsw
pyqt4
pywin32
pyhook
```

running this in CMD:
```
pip install connectordb
```

...and double clicking on `guilaptoplogger.py`.

With a manual install, you will have to figure out how to auto-run on start.

### Linux

```bash
sudo apt-get install python-xlib python-qt5 python-apsw python-pip
sudo pip install connectordb

git clone https://github.com/connectordb/connectordb-laptoplogger
cd ./connectordb-laptoplogger/src
python guilaptoplogger.py #If running headless, use python laptoplogger.py
```

If you don't have PyQT5, it automatically falls back to using PyQT4.

It is up to you to set it up to run on login right now - use your desktop environment's startup manager.

### Mac

Mac version is not ready yet: [see what still needs to be done](https://github.com/connectordb/connectordb-laptoplogger/issues/2)

## Plugins

The following is the plugin content for gathering the titlebar text on windows machines:

```python
# Gathers the currently active window's titlebar text on run
import win32gui

def windowtext():
	# Returns the foreground window's titlebar text
	return unicode(win32gui.GetWindowText(win32gui.GetForegroundWindow()),errors="ignore")

# The plugin class must be called StreamGatherer
class StreamGatherer():
	# All of the fields defined below are required.
	streamname = "activewindow"         # This is the name to use for the stream
	streamschema = {"type": "string"}   # This is the stream schema

	# A description to use when showing this gatherer's info in options
	description = "Gathers the currently active window's titlebar text"
	nickname = "Active Window"

	def start(self,logger):
		# start is called when the logger has begun acquisition of data.
		# Here you can initialize asynchronous gathering and callbacks
		# logger is a connectordb.logger.Logger object
		# (http://connectordb-python.readthedocs.org/en/latest/logger.html)
		pass

	def stop(self):
		# stop is called when the user no longer wants to acquire data from your plugin.
		# it is used for cleanup.
		pass

	def run(self,logger):
		# run is called each user-defined time period. The default is once a minute.
		# this is the perfect place to insert data into the logger. Running logger.insert is
		# the expected way to insert data. It will be synced with the
		# ConnectorDB server automatically.
		logger.insert(self.streamname,windowtext())

```

Create a new file with your plugin's code, and put it in the `src/{windows,linux,osx,all}` directory depending on which operating systems your code works on. Upon restarting LaptopLogger, your plugin will be detected and set up automatically.

We will happily accept pull requests for useful plugins!
