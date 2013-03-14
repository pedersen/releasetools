# commands to write:
# jenkins checker
# basketbuilder
# change log generator

# check out tg2, tg2devtools, tgdocs, website
# for each repository, checkout next, and then merge development
# run nosetests for tg2
# if bad, abort

# make a basketweaver location for this milestone
# get all the previous packages from previous milestone over to here
# upgrade all packages as high as possible, noting which ones got upgraded
# run nosetests
# if pass, continue to 'ALL IS GOOD'
# failure? Work this out TODO!!!

# ALL IS GOOD
# make all packages into symlinks where this needs to happen
# finalize changes for dependency_links in all three repositories
# merge to master
# generate changelog
# tag all three repositories, using changelog as tag annotation
# in tg2 and tg2devtools: python setup.py sdist
# copy sdist files to basket

# commit website updates (packages/basket)
# push each repository
# push each repository's tags
# push website
# ssh to website and rebuild
# in tg2 and tg2devtools: python setup.py sdist upload

# cleanup all checked out repositories

import argparse
import logging
import sys

import requests

from .tracker import checkMilestone
from .travis import checkLatestBuild

tgrepositories = [
    ('TurboGears', 'tg2'),
    ('TurboGears', 'tg2devtools'),
    ('TurboGears', 'tg2docs'),
    ]

def checkOpenMilestones(username, password, milestone):
    log = logging.getLogger(__name__ + '.checkOpenMilestones')
    ready = True
    for owner, repo in tgrepositories:
        state, msg = checkMilestone(owner, repo, username, password, milestone)
        if not state:
            ready = False
            log.error('Owner: %s, Repository: %s, %s' % (owner, repo, msg))
    return ready

def checkLatestTravis():
    log = logging.getLogger(__name__ = '.checkLatestTravis')
    ready = True
    for owner, repo in tgrepositories:
        state, msg = checkLatestBuild(owner, repo, 'development')
        if not state:
            ready = False
            log.error('Owner: %s, Repository: %s, Branch: development, %s' % (owner, repo, msg))
    return ready
    
def main():
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__ + '.main')
    
    parser = argparse.ArgumentParser(description="Check the status of a project's issue tracker")
    parser.add_argument('--username', help='Your username on GitHub')
    parser.add_argument('--password', help='Your password on GitHub')
    parser.add_argument('--milestone', help='The milestone you are working with')
    args = parser.parse_args()

    if not checkOpenMilestones(args.username, args.password, args.milestone):
        log.error('Not all milestones are closed. Aborting')
        sys.exit(1)

    if not checkLatestTravis():
        log.error('The latest Travis builds have had at least failure. Aborting.')
        sys.exit(2)

if __name__ == '__main__':
    main()
    
