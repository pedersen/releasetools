import sys

from ..common import getConfig, saveConfig, optionsbase

progname = 'tracker'

def main():
    config = getConfig(progname)
    if 'type' not in config:
        print "Error: missing tracker type in " + config['config'] + ". Aborting."
        sys.exit(1)

    modname = 'releasetools.tracker.'+config['type']
    trackertop = __import__(modname, globals(), locals(), [], -1)
    tracker = sys.modules[modname]
    try:
        tracker.init(config)
    except Exception as e:
        print str(e)
        print "Tracker initialization failed. Aborting."
        sys.exit(2)

    tickets = tracker.getOpenTickets(config)
    print tickets

    saveConfig(config, progname)
