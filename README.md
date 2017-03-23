ConnectorDB Desktop
==================

This is the [ConnectorDB](https://connectordb.io) frontend for logging the things you do on your PC. 
The desktop app includes a headless version for running on servers, and a cross-platform QT GUI for use on your primary machine.

The app has a simple plugin system, such that anyone can track the system stats they want with only a few lines of code.

It can also manage a ConnectorDB database for simple use. It is the default interface for the desktop version of ConnectorDB.

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


<img src="https://raw.githubusercontent.com/connectordb/connectordb-laptoplogger/master/laptoplogger.png" width="500"/>


## Installing

To get a working release, [Download from website](https://connectordb.io/download).

If you would like to stay recent, you can also get a bleeding-edge development build [here](https://keybase.pub/dkumor/connectordb)

### Linux

```bash
sudo apt-get install python-xlib python-qt5 python-apsw python-pip
sudo pip install connectordb

# Instead of git clone, it is recommended that you download the desktop release
# from https://connectordb.io/downloads - the desktop release will include precompiled
# ConnectorDB binaries.
git clone https://github.com/connectordb/connectordb-desktop
cd ./connectordb-laptoplogger
./connectordb-desktop
```

If you don't have PyQT5, it automatically falls back to using PyQT4.

If using python 2, you will also need `subprocess32`.

It is up to you to set it up to run on login right now - use your desktop environment's startup manager.


### Windows

**On Windows, you can run the installer from [here](https://connectordb.io/download), which will take care of everything.**

If the installer fails, you can get LaptopLogger running
by installing Python 2 on your machine, installing the following packages from [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/):
```
apsw
pyqt4
pywin32
pyhook
```
You will need to run the setup scripts for pywin32: `python.exe Scripts\pywin32_postinstall.py -install`

Finally, run the following in shell:
```
pip install connectordb
pip install subprocess32
```

...and you are done. You can check if it is working by double clicking on `laptoplogger.py`, which is the main startup file.

With a manual install, you will have to figure out how to auto-run on start.

Note: Python 3 is not supported on windows due to issues in libraries used to gather data.


### Mac

The Mac version is functional, but does not yet have any data-gathering. See [issue #4](https://github.com/connectordb/connectordb-laptoplogger/issues/2) for details on progress in data-gathering for mac.

For the mac version, you can download the archive from [here](https://connectordb.io/download). You will then need to set up a couple dependencies:

```bash
brew install redis # required for bundled ConnectorDB server
brew install pyqt5
pip3 install apsw connectordb
```

You can then run ConnectorDB Desktop by double-clicking on `connectordb-desktop`. 

You will want to run the script on login, which can be done using [these instructions](http://stackoverflow.com/questions/6442364/running-script-upon-login-mac/13372744#13372744).

## Headless

The Laptop Logger includes a headless version that can be run on servers. Instead of running `laptoplogger.py`,
you can start the headless version by running:

```
python datamanager.py
```

Note that the plugins are set up to run in GUI environments, so you would have to remove the plugins that depend on a GUI
before running. The headless version makes it very easy to keep track of your servers with minimal setup.

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
	icon = "material:laptop"

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
		# run is called each user-defined time period. The default is once every 4 seconds.
		# this is the perfect place to insert data into the logger. Running logger.insert is
		# the expected way to insert data. It will be synced with the
		# ConnectorDB server automatically.
		logger.insert(self.streamname,windowtext())

```

Create a new file with your plugin's code, and put it in the `src/{windows,linux,osx,all}` directory depending on which operating systems your code works on. Upon restarting LaptopLogger, your plugin will be detected and set up automatically.

We will happily accept pull requests for useful plugins!

## Releases

To make a new release, you will need to first run `makerelease` for connectordb 
in `../connectordb`, after which you can run `makerelease` for laptoplogger in this directory.

To build the windows installer, follow the windows instructions. After installing all dependencies,
go to the windows folder in `./release` (which should have been created when running makerelease), and run:
```
pip install pyinstaller
./windowsbuild.bat
```

Finally, install [NSIS](http://nsis.sourceforge.net/Main_Page), right click on `wininstaller.nsi`,
and click on Compile NSIS Script.