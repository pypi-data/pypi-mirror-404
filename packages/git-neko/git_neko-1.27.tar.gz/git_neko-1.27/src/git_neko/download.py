import os
import shutil
import subprocess
import tarfile

import requests


def download_with_requests(repos, headers):
    repo_count = len(repos)
    count_digit = len((str(repo_count)))
    for i, repo in enumerate(repos, start=1):
        repo_name = repo["name"]
        tarball_url = f"{repo['html_url']}/tarball/{repo['default_branch']}"
        if not os.path.exists(repo_name):
            os.mkdir(repo_name)
            print(f"[{i:>{count_digit}}/{repo_count}] Downloading '{repo_name}'...")
        else:
            shutil.rmtree(repo_name)
            os.mkdir(repo_name)
            print(f"[{i:>{count_digit}}/{repo_count}] Updating '{repo_name}'...")
        response = requests.get(tarball_url, headers=headers)
        with open(f"{repo_name}.tar.gz", "wb") as file:
            file.write(response.content)
        with tarfile.open(f"{repo_name}.tar.gz", "r:gz") as tar_ref:
            tar_info = tar_ref.getmembers()[1:]
            for member in tar_info:
                member.name = f"{repo_name}/{member.name.split('/', 1)[-1]}"
                tar_ref.extract(member)
        os.remove(f"{repo_name}.tar.gz")


def download_with_git(repos):
    repo_count = len(repos)
    count_digit = len(str(repo_count))
    for i, repo in enumerate(repos, start=1):
        repo_name = repo["name"]
        repo_pull_url = repo["ssh_url"]
        if not os.path.exists(repo_name):
            print(f"[{i:>{count_digit}}/{repo_count}]", end=" ", flush=True)
            subprocess.call(["git", "clone", "--recursive", repo_pull_url])
        else:
            print(f"[{i:>{count_digit}}/{repo_count}] Pulling '{repo_name}'...")
            subprocess.call(["git", "-C", repo_name, "pull", "--recurse-submodules"])


def get_all_repos(username, token, headers):
    repos = []
    page = 1

    while True:
        page_query = f"?per_page=100&page={page}"
        if not token:
            API_ENDPOINT = f"https://api.github.com/users/{username}/repos{page_query}"
        else:
            API_ENDPOINT = f"https://api.github.com/user/repos{page_query}"

        response = requests.get(API_ENDPOINT, headers=headers)

        if response.status_code != 200:
            print(response.status_code, response.text)
            break

        page_repos = response.json()

        if not page_repos:
            break

        repos.extend(page_repos)
        page += 1

    return [repo for repo in repos if username in repo["full_name"]]


def download_repositories(username, token, git_check):
    headers = {"Authorization": f"token {token}"} if token else None
    repos = get_all_repos(username, token, headers)

    if git_check:
        download_with_git(repos)
    else:
        download_with_requests(repos, headers)
