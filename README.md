The Laptop Logger
==================

This is the ConnectorDB frontend for logging the things you do on your PC. The LaptopLogger includes a headless version for running on servers, and a cross-platform QT4 GUI for use on your primary machine.

The laptoplogger intentionally has a simple plugin system, such that anyone can track the system stats they want with only a few lines of code.

## Logging
The built-in plugins log several things, but the logged quantities depend on the operating system.
By default, we try to have plugins be consistent across OS, but it is not a requirement.

Our goal is to support at the very least:
- number of keypresses - allows to measure how much you are typing
	- [x] windows
	- [ ] linux
	- [ ] osx
- Active application - shows which program is currently being run
	- [x] windows (done by gathering window titlebar text)
	- [ ] linux
	- [ ] osx
- cpu - gets the CPU utilization
	- [ ] windows
	- [ ] linux
	- [ ] osx

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
