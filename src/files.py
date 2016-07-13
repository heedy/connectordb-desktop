import os
import platform

# https://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
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

def getFileFolder():
    #Open the cache file
    filedir = os.path.join(os.path.expanduser("~"),".local/share/connectordb/laptoplogger")
    # If on windows we save it in the appdata folder
    appdata = os.getenv("APPDATA")
    if appdata!="" and appdata is not None:
        filedir = os.path.join(appdata,"ConnectorDB/laptoplogger")
    if not os.path.exists(filedir):
        os.makedirs(filedir)
    return filedir


def getConnectorDB():
    # It returns the path to ConnectorDB's executable. Wherever it is
    exename = "connectordb"
    if platform.system() == "Windows":
        exename += ".exe"

    # First, try bin/connectordb.exe
    fullpath = os.path.join(os.path.dirname(__file__),"bin",exename)
    if os.path.isfile(fullpath) and os.access(fullpath, os.X_OK):
        return fullpath

    return which(exename)
