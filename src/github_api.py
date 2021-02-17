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


def format_time(td: timedelta) -> str:
    out = []
    hours = td.seconds//3600
    minutes = (td.seconds//60)%60
    if td.days > 0:
        out.append(f'{td.days}d')
    if hours > 0:
        out.append(f'{td.hours}h')
    if minutes > 0:
        out.append(f'{td.minutes}m')
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
        previous_release = repository.get_releases()[1]
        # commits = [
        #     datetime.timestamp(c.get_date()) - datetime.timestamp(previous_created)
        #     for c in repository.get_commits() if c.get_date() >= previous_created
        # ]
        commits = get_commits_between_releases(release, previous_release, repository)
        commit_times = [
            datetime.timestamp(c.get_date()) - datetime.timestamp(previous_release.get_creation_time())
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

    return template.format(
        version=release.get_tag_name(),
        lead_time=format_time(get_lead_time(release, repo)),
        lead_time_colour='blue',
        prev_version=prev_release.get_tag_name()
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
        )
    )
