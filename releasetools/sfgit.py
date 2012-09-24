"""
This is not an easy program to use. It was mostly meant as a one-off
tool, but there may be value in having it around, so I'm including
it. Since it *is* meant as a one-off, I'm not going to actually do
much else with it beyond including it, some URLS, and the config file
I used to drive it. With that, it should be possible to use this tool
to migrate other projects from SF to Github.

To run the program, use this for the command line:

sfgit --project 'project name in config file' --user 'github username' --pass 'github password'

Links:
This page at SourceForge contained all the documentation I could
find. It's not nearly enough, but it's all I can offer. It did tell
how to get the values for the config file (below).

https://sourceforge.net/p/forge/documentation/API%20-%20Beta/

Config File:

[tracker:turbogears2]
type = sf_allura
consumer_key = <consumer key>
consumer_secret = <consumer secret>
oauth_token_secret = <oauth token secret>
oauth_token = <oauth token>
release = 2.2.0

"""
import base64
import json
import logging
import sys
import urllib
import urllib2

from pprint import pprint

from releasetools.common import getConfig, saveConfig, optionsbase
from releasetools.tracker import sf_allura as sf

from pygithub3 import Github

progname = 'tracker'

class Request(urllib2.Request):
    def __init__(self, *args, **kwargs):
        self._method = kwargs.pop('method', None)
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        return self._method if self._method else urllib2.Request.get_method(self)

def sendReq(url, authstr, method='GET', data=None):
    l = logging.getLogger(__name__ + ':sendReq')
    
    baseurl = 'https://api.github.com'

    encdata = None
    if data:
        encdata = json.dumps(data)
        method = 'POST'
        l.debug("encoded data: " + encdata)

    requrl = '%s%s' %( baseurl, url)
    l.debug(requrl)
    req = Request(requrl, method=method, data=encdata)
    req.add_header('Authorization', 'Basic %s' % (authstr))
    req.add_header('Content-Type', 'application/json')
    if encdata:
        req.add_header('Accept', '*/*')
        #opener = urllib2.build_opener(urllib2.HTTPSHandler(debuglevel=1))
        #resp = opener.open(req)
        #return resp.read()

    return urllib2.urlopen(req).read()

#---------------------------------------
# Fix up milestones
#---------------------------------------
def getRepoMilestones(repourl, authstr):
    retval = json.loads(sendReq('/repos/%s/milestones' % (repourl), authstr))
    retval.extend(json.loads(sendReq('/repos/%s/milestones?state=closed' % (repourl), authstr)))
    return retval

def deleteMilestone(url, hubmilestones, ms, authstr):
    msids = filter(lambda x: x['id'] if x['title'] == ms else None, hubmilestones)
    msid = filter(lambda x: x is not None, msids)[0]['number']
    return sendReq('/repos/%s/milestones/%d' % (url, msid), authstr, method='DELETE')

def createMilestone(url, milestones, ms, authstr):
    url = '/repos/%s/milestones' % (url)
    data = {
        'title': ms,
        'state': milestones[ms]['state'],
        }
    if 'due_on' in milestones[ms]:
        data['due_on'] = milestones[ms]['due_on']
    return json.loads(sendReq(url, authstr, data=data))

def createMilestones(repolist, milestones, authstr):
    for urltitle in repolist:
        url = repolist[urltitle]
        hubmilestones = getRepoMilestones(url, authstr)
        msnames = [x['title'] for x in hubmilestones]

        for ms in milestones:
            if ms in msnames:
                print "Deleting pre-existing milestone '%s'" % (ms)
                deleteMilestone(url, hubmilestones, ms, authstr)
            print "Creating Milestone '%s'" % (ms)
            res = createMilestone(url, milestones, ms, authstr)
            milestones[ms]['number'] = res['number']
    
#---------------------------------------
# Fix up labels
#---------------------------------------
def getRepoLabels(repourl, authstr):
    results = json.loads(sendReq('/repos/%s/labels' % (repourl), authstr))
    return [x['name'] for x in results]

def createRepoLabel(repourl, authstr, labelname):
    return json.loads(sendReq('/repos/%s/labels' % (repourl), authstr, data={'name': labelname, 'color': '000000'}))

def createRepoLabels(repolist, authstr, labels):
    for urltitle in repolist:
        repourl = repolist[urltitle]
        existinglabels = getRepoLabels(repourl, authstr)
        for label in labels:
            if label not in existinglabels:
                print "Creating label %s" % (label)
                createRepoLabel(repourl, authstr, label)

#---------------------------------------
# Issues
#---------------------------------------
def forceAscii(s):
    return ''.join(filter(lambda x: ord(x)<=127, s))

def makeCommentText(author, timestamp, body):
    c = 'Original Author: %s, Original Timestamp: %s\n\nOriginal Body: %s' % (author, timestamp, forceAscii(body))
    return c

def createIssue(config, reponame, authstr, issue, comments):
    issue_data=json.loads(sendReq('/repos/%s/issues' % (reponame), authstr, data=issue))
    curl = '/repos/%s/issues/%d/comments' % (reponame, issue_data['number'])

    for c in comments:
        sendReq(curl, authstr, data={'body': c})

def createIssues(config, repolist, milestones, authstr, tickets):
    for ticket in tickets:
        issue = {}
        issue['title'] = ticket['summary']
        issue['labels'] = []
        
        fields = ticket['custom_fields']
        if '_repository' in fields and fields['_repository'] in repolist:
            reponame = repolist[fields['_repository']]
        else:
            reponame = 'tg2'
            
        if '_milestone' in fields and fields['_milestone'] in milestones:
            issue['milestone'] = milestones[fields['_milestone']]['number']

        for label in ['_severity', '_component', '_type', '_version']:
            if label in fields:
                issue['labels'].append(fields[label])

        body = ''
        if ticket['labels']:
            body = '%sThis issue existed in Trac. The original can be viewed at %s\n\n' % (body, ','.join(ticket['labels']))
        body = '%sThis issue existed on SourceForge. The original can be viewed at https://sourceforge.net/p/turbogears2/tickets/%d' % (body, ticket['ticket_num'])
        issue['body'] = body
        comments = [makeCommentText(ticket['reported_by'], ticket['created_date'], ticket['description'])]
        for comment in ticket['comments']:
            comments.append(makeCommentText(comment['author'], comment['timestamp'], comment['text'] ))
        print 'Re-Creating ticket %d' % (ticket['ticket_num'])
        createIssue(config, reponame, authstr, issue, comments)
                
#---------------------------------------
# Comments
#---------------------------------------                
#---------------------------------------
# Main
#---------------------------------------
def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)-15s %(name)s:%(levelname)s:%(message)s')
    optionsbase.add_option('-u', '--user', dest='user',
                           action='store', type='string',
                           help='Use this username on github', metavar='USERNAME')
    optionsbase.add_option('-a', '--pass', dest='pass',
                           action='store', type='string',
                           help='Use this password on github', metavar='PASSWORD')

    config = getConfig(progname)

    if 'user' not in config or not config['user']:
        print "Error: no username for github supplied. Aborting."
        sys.exit(1)

    if 'pass' not in config or not config['pass']:
        print "Error: No password for github supplied. Aborting."
        sys.exit(2)
        
    milestones = {
        '2.0.3': {'state': 'closed', 'due_on': '8/24/2009'},
        '2.0.4': {'state': 'closed', 'due_on': '6/5/2011'},
        '2.1.0': {'state': 'closed', 'due_on': '10/16/2010'},
        '2.1.1': {'state': 'closed', 'due_on': '6/15/2011'},
        '2.1.2': {'state': 'closed', 'due_on': '8/24/2011'},
        '2.1.3': {'state': 'closed', 'due_on': '9/28/2011'},
        '2.1.4': {'state': 'closed', 'due_on': '12/12/2011'},
        '2.1.5': {'state': 'closed', 'due_on': '4/7/2012'},
        '2.2.0': {'state': 'closed', 'due_on': '8/23/2012'},
        '2.3.0': {'state': 'open'},
        'Undetermined': {'state': 'open'},
        }

    labels = 'defect enhancement task trivial minor normal major critical blocker core documentation genshi i18n auth installation mako quickstart sqlalchemy tgext.admin toscawidgets everything.else 2.1.5 2.1.4 2.1.3 2.1.2 2.1.1 2.0.4 2.1.0 2.0.3'.split()
    
    repolist = {
        'core': 'pedersen/tg2', #tg2
        'devtools': 'pedersen/tg2devtools', #tg2devtools
        'docs': 'pedersen/tg2docs', #tg2docs
        'tutorials': 'pedersen/tg2tut' #tg2tut (needs to be made)
        }

    sf.init(config)
    # need to manually list tickets from 1 to max (currently 161), and get each one
    #pprint(sf.getOpenTickets(config))
    #pprint(sf.getTicketList(config, 'p/turbogears2'))
    #pprint(sf.getTicket(config, 'p/turbogears2', '91', True))
    #pprint(sf.getSfRestResult(config, 'p/turbogears2/tickets/_discuss'))
    #pprint(sf.getSfRestResult(config, 'p/turbogears2/tickets/_discuss/thread/3012ce6e/'))
    #pprint(sf.getSfRestResult(config, 'p/turbogears2/tickets/_discuss/thread/3012ce6e/d4e0'))

    #pprint(sf.getTickets(config))
    
    authstr = base64.encodestring('%s:%s' % (config['user'], config['pass'])).strip()
    
    createMilestones(repolist, milestones, authstr)

    createRepoLabels(repolist, authstr, labels)

    tickets = []
    for idx in range(1, 162):
        print 'Retrieving Ticket %d' % (idx)
        ticket = sf.getTicket(config, 'p/' + config['project'], idx, True)
        if ticket['status'] not in ['closed', 'wont-fix', 'duplicate']:
            tickets.append(ticket)
    createIssues(config, repolist, milestones, authstr, tickets)
    
    
