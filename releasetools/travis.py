import argparse
import logging

import requests

def checkLatestBuild(owner, repo, branch):
    builds = requests.get('https://api.travis-ci.org/repos/%s/%s/builds' % (owner, repo)).json
    onbranch = filter(lambda x: x['branch'] == branch, builds)
    finished = filter(lambda x: x['state'] == 'finished', onbranch)

    if len(finished) == 0:
        return False, 'Branch has not been built yet'

    if finished[0]['result'] == 0:
        return True, 'Last build was successful'
    else:
        return False, 'Last build failed'
    
    
def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description="Check the status of a project's issue tracker")
    parser.add_argument('--owner', help='The owner of the project')
    parser.add_argument('--repo', help='The repository name of the project')
    parser.add_argument('--branch', help='The branch you are working with')
    parser.add_argument('--check', help='Check to see the state of the branch',
                        action='store_true')
    args = parser.parse_args()

    if args.check:
        print checkLatestBuild(args.owner, args.repo, args.branch)
