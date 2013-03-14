import argparse

import requests

def checkMilestone(owner, repo, username, password, milestone):
    milestones = requests.get('https://api.github.com/repos/%s/%s/milestones' % (owner, repo), auth=(username, password)).json
    for m in milestones:
        if m['title'] == milestone:
            if m['state'] != 'closed':
                return False, 'Milestone %s is not closed, and has %d open issues' % (m['title'], m['open_issues'])
            else:
                return True, 'Milestone %s is closed.' % (m['title'])
    return False, 'Milestone %s does not exist.' % (milestone)
    
    
def main():
    parser = argparse.ArgumentParser(description="Check the status of a project's issue tracker")
    parser.add_argument('--owner', help='The owner of the project')
    parser.add_argument('--repo', help='The repository name of the project')
    parser.add_argument('--username', help='Your username on GitHub')
    parser.add_argument('--password', help='Your password on GitHub')
    parser.add_argument('--milestone', help='The milestone you are working with')
    parser.add_argument('--check', help='Check to see the state of the milestone',
                        action='store_true')
    args = parser.parse_args()

    if args.check:
        print checkMilestone(args.owner, args.repo, args.username, args.password, args.milestone)
