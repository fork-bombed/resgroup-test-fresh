from datetime import datetime, timedelta
import commit
import github
import release
import repository
import os
import sys

def get_commits_between_releases(
        release: release.Release, 
        last_release: release.Release, 
        repository: repository.Repository
    ) -> [commit.Commit]:

    commits = []
    for c in repository.get_commits():
        if (c.get_date() >= last_release.get_creation_time() and
                c.get_date() <= release.get_creation_time()):
            commits.append(c)
    return commits


def format_urlsafe_time(td: timedelta) -> str:
    out = []
    seconds = td.seconds
    minutes = (seconds//60)%60
    hours = (seconds//3600)%24
    days = td.days
    if days > 0:
        out.append(f'{days}d')
    if hours > 0:
        out.append(f'{hours}h')
    if minutes > 0:
        out.append(f'{minutes}m')
    return '%20'.join(out)


def get_lead_time(
        release: release.Release, 
        repository: repository.Repository
    ) -> timedelta:

    if len(repository.get_releases()) == 1:
        commit_times = [
            datetime.timestamp(c.get_date()) - datetime.timestamp(repository.get_creation_time())
            for c in repository.get_commits()
        ]
    else:
        releases = repository.get_releases()
        release_index = None
        for index,r in enumerate(releases):
            if r.get_id() == release.get_id():
                release_index = index
                break
        if release_index != None:
            if release_index < len(releases)-1:
                prev_release = releases[release_index+1]
            else:
                return timedelta(seconds=0)
        else:
            return timedelta(seconds=0)
        commits = get_commits_between_releases(release, prev_release, repository)
        commit_times = [
            datetime.timestamp(c.get_date()) - datetime.timestamp(prev_release.get_creation_time())
            for c in commits
        ]
    return timedelta(seconds=sum(commit_times)/len(commit_times))


def get_release_template(
        release: release.Release, 
        prev_release: release.Release, 
        repo: repository.Repository
    ) -> str:

    with open('src/templates/default.md') as file:
        template = file.read()
    lead_time = get_lead_time(release, repo)
    if lead_time.days >= 30:
        lead_time_colour = 'critical'
    elif lead_time.days >= 10 and lead_time.days < 30:
        lead_time_colour = 'important'
    else:
        lead_time_colour = 'success'
    prev_lead_time = get_lead_time(prev_release, repo)
    if lead_time > prev_lead_time:
        lead_time_difference = format_urlsafe_time(lead_time - prev_lead_time)
        lead_time_difference_colour = 'critical'
    else:
        lead_time_difference = ''.join(['--',format_urlsafe_time(prev_lead_time - lead_time)])
        lead_time_difference_colour = 'success'

    return template.format(
        version=release.get_tag_name(),
        lead_time=format_urlsafe_time(lead_time),
        lead_time_colour=lead_time_colour,
        prev_version=prev_release.get_tag_name(),
        repository=repo.get_full_name(),
        lead_time_difference=lead_time_difference,
        lead_time_difference_colour=lead_time_difference_colour
    )


if __name__ == "__main__":
    token = os.environ.get('GITHUB_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    if not token:
        print('Token not found')
        sys.exit(1)
    if not repo:
        print('Repo not found')
        sys.exit(1)
    client = github.Github(token)
    repository = client.get_repository(repo)
    release = repository.get_latest_release()
    prev_release = repository.get_releases()[1]
    release.update(
        message=get_release_template(
            release=release, 
            repo=repository,
            prev_release=prev_release
        ) + f'\n{release.get_body_text()}'
    )
