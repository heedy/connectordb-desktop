import os
import platform
import json


def getDefaultFolderLocation():
    """ 
    By default, laptoplogger saves its data in ~/.local/share/connectordb on linux,
    and in %APPDATA%/ConnectorDB on windows
    """
    filedir = os.path.join(os.path.expanduser("~"), ".local/share/connectordb")
    # If on windows we save it in the appdata folder
    appdata = os.getenv("APPDATA")
    if appdata != "" and appdata is not None:
        filedir = os.path.join(appdata, "ConnectorDB")

    return filedir


def readJSON(filename):
    """
        Given a filename, reads its contents into a python dict
    """
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def writeJSON(filename, data):
    """
        Given a filename and json data, writes it to file
    """
    with open(filename, "w") as f:
        json.dump(data, f)


def which(program):
    # https://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def getConnectorDB():
    # It returns the path to ConnectorDB's executable. Wherever it is
    exename = "connectordb"
    if platform.system() == "Windows":
        exename += ".exe"

    # First, try bin/connectordb.exe
    fullpath = os.path.join(os.path.dirname(__file__), "bin", exename)
    if os.path.isfile(fullpath) and os.access(fullpath, os.X_OK):
        return fullpath

    return which(exename)
