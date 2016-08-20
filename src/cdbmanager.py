# The manager handles management of a local ConnectorDB database. It creates, sets up,
# and handles everything needed to run ConnectorDB

import os
import sys
import subprocess
import logging
import files
import shutil
import platform

class Manager(object):
    def __init__(self,location,cdb_executable=None):
        self.cdb_executable = cdb_executable
        if self.cdb_executable is None:
            self.cdb_executable = files.getConnectorDB()
            if self.cdb_executable is None:
                raise Exception("Could not find ConnectorDB executable")
        self.location = os.path.abspath(location)
    def create(self,username,password,out=sys.stdout):
        logging.info("Creating new ConnectorDB database at "+self.location)
        cmd = [self.cdb_executable,"create",self.location,"--user="+username+":"+password,"--sqlbackend=sqlite3"]
        retcode = None
        # There are issues in Windows with pyinstaller that make console windows pop up. We allow this console window
        # but don't redirect output
        if platform.system()=="Windows":
            retcode = subprocess.call(cmd)
        else:
            retcode = subprocess.call(cmd,stdout=out,stderr=out)
        # If failed, remove the directory
        if retcode != 0:
            shutil.rmtree(self.location)
        return retcode
    def start(self,out=sys.stdout):
        logging.info("Starting database at "+self.location)
        # Unfortunately, we need to use --force, since oftentimes the database is not shut down correctly
        # on OS exit
        return self.runproc([self.cdb_executable,"start",self.location,"--force"],out)
    def stop(self,out=sys.stdout):
        logging.info("Stopping database at "+self.location)
        return self.runproc([self.cdb_executable,"stop",self.location],out)
    def runproc(self,cmd,out):
        retcode = None
        # There are issues in Windows with pyinstaller that make console windows pop up. We disallow the console
        # window here
        if platform.system()=="Windows":
            # https://code.activestate.com/recipes/578300-python-subprocess-hide-console-on-windows/
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            retcode = subprocess.call(cmd,startupinfo=startupinfo)
        else:
            retcode = subprocess.call(cmd,stdout=out,stderr=out)
        return retcode

if (__name__=="__main__"):
    import webbrowser
    logging.basicConfig(level=logging.DEBUG)
    m = Manager("./db","../bin/connectordb")
    if (m.create("test","test")!=0):
        print("CREATE FAILED")
    else:
        if (m.start()!=0):
            print("START FAILED")
        else:
            webbrowser.open("http://localhost:8000")
            input()
            m.stop()
