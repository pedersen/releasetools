import os
import sys

from ..common import getConfig, saveConfig, optionsbase

progname = 'mkbasket'

def noVenvCmd(runcmd):
    evars = ['PATH', 'VIRTUAL_ENV', 'VIRTUALENVWRAPPER_HOOK_DIR',
             'VIRTUALENVWRAPPER_LOG_DIR', 'VIRTUALENVWRAPPER_PROJECT_FILENAME']
    saved = {}
    for vname in evars:
        saved[vname] = os.environ[vname]
        del(os.environ[vname])

    venv = saved['VIRTUAL_ENV']
    path = saved['PATH'].split(':')
    novenvpath = filter(lambda x: not x.startswith(venv), path)
    spath = ":".join(novenvpath)
    os.environ['PATH'] = spath
    
    sysret = os.system(runcmd)

    for vname in evars:
        os.environ[vname] = saved[vname]

    return sysret

def initBasket(config):
    if 'initiliaze_eggbasket' in config:
        ret = os.system(config['initiliaze_eggbasket'])
        if ret != 0:
            print "Error initializing eggbasket. Aborting!"
            sys.exit(3)

def makeBaselineBasket(config):
    if 'copy_base_eggbasket' in config:
        cp = config['copy_base_eggbasket']
        cp = cp.replace('{prev_version}', config['prev_version'])
        cp = cp.replace('{new_version}',  config['new_version'])
        os.system(cp)
            
def main():
    optionsbase.add_option('-o', '--output', dest='output',
                           action='store', type='string',
                           help='Use this directory for output', metavar='OUTPUT_DIRECTORY')
    optionsbase.add_option('-v', '--version', dest='prev_version',
                           action='store', type='string',
                           help='Use this as the old version for the eggbasket', metavar='PREVIOUS_VERSION')
    optionsbase.add_option('-n', '--newversion', dest='new_version',
                           action='store', type='string',
                           help='Use this as the new version for the eggbasket', metavar='NEW_VERSION')
    
    config = getConfig(progname)
    if 'project' not in config or not config['project']:
        print "Error: missing mkbasket projectname in " + config['config'] + ". Aborting."
        sys.exit(1)

    if 'output' not in config or not config['output']:
        print "Error: missing --output. Aborting."
        sys.exit(1)

    if 'prev_version' not in config or not config['prev_version']:
        print "Error: missing --previousversion. Aborting."
        sys.exit(1)
        
    if 'new_version' not in config or not config['new_version']:
        print "Error: missing --newversion. Aborting."
        sys.exit(1)
        
    config['output'] = os.path.expanduser(config['output'])
    config['workspace'] = os.path.expanduser(config['workspace'])

    initBasket(config)
    makeBaselineBasket(config)
    #print "make new virtualenv"
    #print "perform installation process"
    #print "perform application pre-test"
    #print "perform application test"
    #print "use yolk to find eggs that can be upgraded"
    #for egg in []:
    #    print "list egg versions in order, including local eggbasket, excluding packages from list"
    #    versions = []
    #    print "current version from virtualenv"
    #    successful = False
        #while !successful and len(versions) > 0:
        #    print "upgrade egg to highest version in list"
        #    print "perform application test"
        #    if !"successful":
        #        print "delete last version in list"
        #if !successful:
        #    print "Unable to find a compatible version of: %s" % (egg)
        #    sys.exit(3)

    saveConfig(config, progname)
