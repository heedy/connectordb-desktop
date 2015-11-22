import importlib
import logging
import platform
import os
import sys
import glob

def getpluginsfromdirectory(directory):
    fullpath = os.path.join(os.path.dirname(__file__),directory)

    #Make sure the directory exists
    if not os.path.isdir(fullpath):
        raise Exception("Could not find plugin directory %s"%(fullpath,))

    logging.info("Loading modules from "+ fullpath)
    #sys.path.append(directory)

    plugins = []

    # Now load ALL the plugins
    # Originally based on this: https://lextoumbourou.com/blog/posts/dynamically-loading-modules-and-classes-in-python/
    pluginmodules = map(os.path.splitext,map(os.path.basename,glob.glob(fullpath + "/[a-zA-Z]*.py")))
    for mod_name,ext in pluginmodules:
        logging.info("Loading: " + mod_name)
        loaded_mod = importlib.import_module(directory + "." + mod_name)
        loaded_class = loaded_mod.StreamGatherer
        logging.debug("Loaded stream: "+ loaded_class.streamname)
        plugins.append(loaded_class)
    return plugins

def getplugins():
    plugins = getpluginsfromdirectory("all")

    # Next load the OS-specific plugins
    my_os = platform.system()
    if my_os == "Windows":
        plugins += getpluginsfromdirectory("windows")
    elif my_os == "Linux":
        plugins += getpluginsfromdirectory("linux")
    elif my_os == "Darwin":
        plugins += getpluginsfromdirectory("osx")
    else:
        logging.warn("Could not recognize operating system. Not loading OS-specific modules.")

    return plugins
