import pkgutil
import logging
import platform
import os
import sys

def getpluginsfromdirectory(directory):
    logging.info("Loading modules from "+ directory)
    sys.path.append(directory)

    plugins = []

    # Now load ALL the plugins
    # Based on this: https://lextoumbourou.com/blog/posts/dynamically-loading-modules-and-classes-in-python/
    modules = pkgutil.iter_modules(path=[directory])
    for loader, mod_name, ispkg in modules:
        # Ensure that module isn't already loaded
        if mod_name not in sys.modules:
            logging.info("Loading: "+ mod_name)
            loaded_mod = __import__(mod_name)
            loaded_class = loaded_mod.StreamGatherer
            logging.debug("Loaded stream: "+ loaded_class.streamname)
            plugins.append(loaded_class)
    return plugins

def getplugins(directory = os.path.dirname(__file__)):
    # First load the cross-platform plugins

    directory_all = os.path.join(directory,"all")
    # Make sure the directory exists
    if not os.path.isdir(directory):
        raise Exception("Could not find plugin directory %s"%(directory,))

    # Next load the OS-specific plugins
    my_os = platform.system()

    if my_os == "Windows":
        directory = os.path.join(directory,"windows")
    elif my_os == "Linux":
        directory = os.path.join(directory,"linux")
    elif my_os == "Darwin":
        directory = os.path.join(directory,"osx")
    else:
        raise Exception("Could not identify operating system!")

    #Make sure the directory exists
    if not os.path.isdir(directory):
        raise Exception("Could not find plugin directory %s"%(directory,))

    plugins = getpluginsfromdirectory(directory_all)
    plugins += getpluginsfromdirectory(directory)

    return plugins
