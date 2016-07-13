# The manager handles management of a local ConnectorDB database. It creates, sets up,
# and handles everything needed to run ConnectorDB

import os
import sys
import subprocess
import logging
import files
import shutil
print("MANAGER")
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
        retcode = subprocess.call([self.cdb_executable,"create",self.location,"--user="+username+":"+password],stdout=out,stderr=out)
        # If failed, remove the directory
        if retcode != 0:
            shutil.rmtree(self.location)
        return retcode
    def start(self,out=sys.stdout):
        logging.info("Starting database at "+self.location)
        # Unfortunately, we need to use --force, since oftentimes the database is not shut down correctly
        # on OS exit
        return subprocess.call([self.cdb_executable,"start",self.location,"--force"],stdout=out,stderr=out)
    def stop(self,out=sys.stdout):
        logging.info("Stopping database at "+self.location)
        return subprocess.call([self.cdb_executable,"stop",self.location],stdout=out,stderr=out)

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
