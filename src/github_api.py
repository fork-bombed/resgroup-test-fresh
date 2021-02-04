from datetime import datetime, timedelta
import commit
import github
import release
import repository
import os, sys

def get_lead_time(release: release.Release, repository: repository.Repository) -> timedelta:
    # If there's only one release then get all the commits and compare 
    # to the creation of the repository.
    if len(repository.get_releases()) == 1:
        commits = [
            datetime.timestamp(commit.get_date()) - datetime.timestamp(repository.get_creation_time())
            for commit in repository.get_commits()
        ]
    else:
        previous_release = repository.get_releases()[1]
        previous_created = previous_release.get_creation_time()

        commits = [
            datetime.timestamp(commit.get_date()) - datetime.timestamp(previous_created)
            for commit in repository.get_commits() if commit.get_date() >= previous_created
        ]

    return timedelta(seconds=sum(commits)/len(commits))


def get_release_template(release: release.Release, repo: repository.Repository) -> str:
    with open('src/template.md') as file:
        template = file.read()

    return template.format(
        version=release.get_tag_name(),
        lead_time=get_lead_time(release, repo)
    )


if __name__ == "__main__":
    token = os.environ.get('GITHUB_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    if not token:
        print('Token not found')
        sys.exit(1)
    print('repo:',repo)
    if not repo:
    #     repo = repo.split('/')[-1]
        print('Repo not found')
        sys.exit(1)
    client = github.Github(token)
    repository = client.get_repository(repo)
    release = repository.get_latest_release()
    release.update(
        message=get_release_template(
            release=release, repo=repository
        )
    )
