# The manager handles management of a local ConnectorDB database. It creates, sets up,
# and handles everything needed to run ConnectorDB

import os
import sys
import logging
import files
import shutil
import platform

# Python 2 requires subprocess32
try:
    import subprocess32 as subprocess
except:
    import subprocess


class Manager(object):

    def __init__(self, location, cdb_executable=None):
        self.cdb_executable = cdb_executable
        if self.cdb_executable is None:
            self.cdb_executable = files.getConnectorDB()
            if self.cdb_executable is None:
                raise Exception("Could not find ConnectorDB executable")
        self.location = os.path.abspath(location)

    def createAndImport(self, username, password, folder, out=sys.stdout):
        """
            Creates and imports the database. Leaves ConnectorDB running. Run stop to
            shut down the resulting database
        """

        # Make sure the user exists in the folder to import
        if not os.path.isdir(os.path.join(folder, username)):
            raise Exception("User " + username + " not found in " + folder)

        # We can't create the database if the folder already exists
        if os.path.exists(self.location):
            raise Exception(
                "A ConnectorDB database already exists at " + self.location)

        # Try to create the database
        logging.info("Creating new ConnectorDB database at " + self.location)
        cmd = [self.cdb_executable, "create",
               self.location, "--sqlbackend=sqlite3"]
        retcode = self.runproc_window(cmd, out)
        if retcode != 0:
            shutil.rmtree(self.location)
            raise Exception("Failed to create database")

        # Start the database and import the data
        self.start(out)

        ret = self.importDatabase(folder, out)
        if ret != 0:
            self.stop()
            shutil.rmtree(self.location)
            raise Exception("Could not import the database")

        # Change the user's password to the one given.
        if self.runproc([self.cdb_executable, "shell",
                         self.location, "passwd", username, password], out) != 0:
            self.stop()
            shutil.rmtree(self.location)
            raise Exception("Failed to set up user's password")
        logging.info("Database import complete.")

    def create(self, username, password, out=sys.stdout):
        logging.info("Creating new ConnectorDB database at " + self.location)
        # We can't create the database if the folder already exists
        if os.path.exists(self.location):
            raise Exception(
                "A ConnectorDB database already exists at " + self.location)
        cmd = [self.cdb_executable, "create", self.location,
               "--user=" + username + ":" + password, "--sqlbackend=sqlite3"]
        retcode = self.runproc_window(cmd, out)
        if retcode != 0:
            shutil.rmtree(self.location)
        return retcode

    def importDatabase(self, location, out=sys.stdout):
        logging.info("Importing from " + self.location)
        return self.runproc_window([self.cdb_executable, "import", self.location, location], out)

    def exportDatabase(self, location, out=sys.stdout):
        logging.info("Exporting to " + self.location)
        return self.runproc_window([self.cdb_executable, "export", self.location, location], out)

    def start(self, out=sys.stdout):
        logging.info("Starting database at " + self.location)
        # Unfortunately, we need to use --force, since oftentimes the database is not shut down correctly
        # on OS exit
        return self.runproc([self.cdb_executable, "start", self.location, "--force"], out)

    def stop(self, out=sys.stdout):
        logging.info("Stopping database at " + self.location)
        return self.runproc([self.cdb_executable, "stop", self.location], out)

    def remove(self):
        shutil.rmtree(self.location)

    def version(self):
        return version(cdb_executable=self.cdb_executable)

    def runproc(self, cmd, out):
        retcode = None
        # There are issues in Windows with pyinstaller that make console windows pop up. We disallow the console
        # window here
        if platform.system() == "Windows":
            # https://code.activestate.com/recipes/578300-python-subprocess-hide-console-on-windows/
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            retcode = subprocess.call(cmd, startupinfo=startupinfo)
        else:
            retcode = subprocess.call(
                cmd, stdout=out, stderr=out, start_new_session=True)
        return retcode

    def runproc_window(self, cmd, out):
        retcode = None
        # There are issues in Windows with pyinstaller that make console windows pop up. We allow this console window
        # but don't redirect output
        if platform.system() == "Windows":
            retcode = subprocess.call(cmd)
        else:
            retcode = subprocess.call(cmd, stdout=out, stderr=out)
        return retcode


def version(cdb_executable=None):
    if cdb_executable is None:
        cdb_executable = files.getConnectorDB()
        if cdb_executable is None:
            return ""
    cmd = [cdb_executable, "--semver"]
    p = None
    if platform.system() == "Windows":
        # https://code.activestate.com/recipes/578300-python-subprocess-hide-console-on-windows/
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, startupinfo=startupinfo)
    else:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE)
    out, err = p.communicate()
    return out.decode("utf-8").strip()

if (__name__ == "__main__"):
    import webbrowser
    logging.basicConfig(level=logging.DEBUG)
    m = Manager("./db", "../bin/connectordb")
    if (m.create("test", "test") != 0):
        print("CREATE FAILED")
    else:
        if (m.start() != 0):
            print("START FAILED")
        else:
            webbrowser.open("http://localhost:8000")
            input()
            m.stop()
