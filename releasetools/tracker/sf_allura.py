"""
Following the documentation here: http://sourceforge.net/p/forge/documentation/API%20-%20Beta/
"""
import json
import logging
import urlparse
import webbrowser

import certifi
import oauth2

from pprint import pprint

def init(config):
    if 'consumer_key' not in config and 'consumer_secret' not in config:
        raise Exception("""consumer_key and consumer secret must be set in %s
Read http://sourceforge.net/p/forge/documentation/API%%20-%%20Beta/ for
details on obtaining them.""" % (config['config']))

    if 'oauth_token' not in config or 'oauth_token_secret' not in config:
        getOauthToken(config)

def getOauthToken(config):
    CONSUMER_KEY = config['consumer_key']
    CONSUMER_SECRET = config['consumer_secret']
    REQUEST_TOKEN_URL = 'https://sourceforge.net/rest/oauth/request_token'
    AUTHORIZE_URL = 'https://sourceforge.net/rest/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://sourceforge.net/rest/oauth/access_token'

    consumer = oauth2.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
    client = oauth2.Client(consumer)
    client.ca_certs = certifi.where()

    resp, content = client.request(REQUEST_TOKEN_URL, 'GET')
    if resp['status'] != '200':
        raise Exception("Invalid response %s." % resp['status'])

    request_token = dict(urlparse.parse_qsl(content))
    
    webbrowser.open("%s?oauth_token=%s" % (
            AUTHORIZE_URL, request_token['oauth_token']))
    
    oauth_verifier = raw_input('What is the PIN? ')
    
    token = oauth2.Token(request_token['oauth_token'],
                         request_token['oauth_token_secret'])
    token.set_verifier(oauth_verifier)
    client = oauth2.Client(consumer, token)
    client.ca_certs = certifi.where()
    
    resp, content = client.request(ACCESS_TOKEN_URL, "GET")
    access_token = dict(urlparse.parse_qsl(content))

    config['oauth_token'] = access_token['oauth_token']
    config['oauth_token_secret'] = access_token['oauth_token_secret']

def getSfRestResult(config, url):
    l = logging.getLogger(__name__ + ".getSfRestResult")
    URL_BASE='http://sourceforge.net/rest/'

    l.debug('configuring')
    consumer = oauth2.Consumer(config['consumer_key'], config['consumer_secret'])
    access_token = oauth2.Token(config['oauth_token'], config['oauth_token_secret'])
    client = oauth2.Client(consumer, access_token)
    client.ca_certs = certifi.where()

    url = URL_BASE + url
    l.debug('requesting %s' % (url))
    resp, content = client.request(url)
    l.debug('content: %s' % (content))
    l.debug('returning')
    return json.loads(str(content))

def getTicket(config, project, ticket_num, get_comments=False):
    turl = project + '/tickets/'
    ticket = getSfRestResult(config, turl + str(ticket_num))['ticket']

    comments = []
    if get_comments:
        durl = project + '/tickets/_discuss/thread/%s/%s'
        threadid = ticket['discussion_thread']['_id']
        for post in ticket['discussion_thread']['posts']:
            comments.append(getSfRestResult(config, durl % (threadid, post['slug']))['post'])
    ticket['comments'] = comments

    return ticket

def getTicketList(config, project):
    return getSfRestResult(config, project + '/tickets')

def getTickets(config):
    project = 'p/' + config['project']
    tickets = getTicketList(config, project)
    
    ret_tickets = []
    for ticket in tickets['tickets']:
        ret_tickets.append(getTicket(config, project, ticket['ticket_num']))

    return ret_tickets

def getOpenTickets(config):

    ret_tickets = []
    for ticket in getTickets(config):
        if ('custom_fields' in ticket and '_milestone' in ticket['custom_fields']
            and ticket['custom_fields']['_milestone'] == config['release']
            and ticket['status'] not in ['closed', 'wont-fix', 'duplicate']):
            ret_tickets.append(ticket)

    return ret_tickets
