# git-neko

CLI for downloading all repositories from a specified user.

## Installation

### Via PyPI (Recommended)

#### With pip (Basic)

```sh
pip install git-neko
```

#### With pipx (Isolated)

```sh
pipx install git-neko
```

#### With uv (Best)

The most efficient way to install or run the uploader.

```sh
# Permanent isolated installation
uv tool install git-neko

# Run once without installing
uvx git-neko -u <username>

# Run in scripts or ad-hoc environments
uv run --with git-neko git-neko -u <username> -t <token>
```

### From Source (Development)

```sh
# Clone the repository and navigate to it
git clone git@github.com:NecRaul/git-neko.git
cd git-neko

# Install environment and all development dependencies (mandatory and optional)
uv sync --dev

# Install pre-commit hook
uv run pre-commit install

# Optional: Run all linters and type checkers manually
uv run pre-commit run --all-files

# Run the local version
uv run git-neko -e -g
```

## Usage

`git-neko` acts as a sync tool. If a repo folder doesn't exist, it clones it, if it does, it updates it.

```sh
# Download/Sync public repositories with `requests`
git-neko -u <github-username>

# Download/Sync public and private repositories with `requests` (using a token)
git-neko -u <github-username> -t <github-personal-access-token>

# Use 'git clone/pull' instead of 'requests' (preserves history, branches and submodules)
git-neko -u <github-username> -g

# Use 'git' with a token for private repository syncing
git-neko -u <github-username> -t <github-personal-access-token> -g
```

### Environment Variables

You can save your credentials to environment variables to avoid passing them manually in every command.

For persistence, add these exports to your shell configuration file (e.g., `~/.bashrc`, `~/.zshrc`, or `~/.bash_profile`).

```sh
# Set your credentials as environment variables
export GITHUB_USERNAME="NecRaul"
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_necraul"

# Run using the stored environment variables
git-neko -e

# Run using environment variables with the git engine
git-neko -e -g

# Pass environment variables directly within the command
GITHUB_USERNAME="NecRaul" GITHUB_PERSONAL_ACCESS_TOKEN="ghp_necraul" git-neko -e
```

### Options

```sh
-u, --username      USERNAME    GitHub username to download repositories from
-t, --token         TOKEN       GitHub personal access token (required for private repositories)
-e, --environment   -           Use stored environment variables for username and token
-g, --git           -           Use git engine instead of requests (handles history/branches/submodules)
```

> [!TIP]
> The `-e` and `-g` flags are a boolean toggle.

## Dependencies

* [requests](https://github.com/psf/requests): fetch data from the GitHub API and handle downloads.

## How it works

The tool determines the appropriate GitHub API endpoint based on your input: it queries `https://api.github.com/users/{username}/repos` for public profiles or `https://api.github.com/user/repos` when a token is provided to include private data.

Once the repo list is retrieved, `git-neko` automates the synchronization process using one of two engines:

* Requests Engine (Default): Fetches the repo as a compressed snapshot. This is fast but does not include **history**, **branches** or **submodules**.
* Git Engine (via `-g` or `--git` flag): Uses your local **git** installation to perform a full **clone** or **pull** This preserves the complete **history**, **branches** and **submodules**.

### The Manual Way

Without this tool, you would need to manually parse JSON responses, manage authentication headers, and write logic to differentiate between new clones and existing updates:

```sh
# A simplified version of the logic git-neko automates
# It fetches the name and ssh_url, then loops through them
curl -s -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" https://api.github.com/user/repos |
    jq -r '.[] | "\(.name) \(.ssh_url)"' | while read -r name ssh_url; do
    if [ ! -d "$name" ]; then
        git clone --recursive "$ssh_url" "$name"
    else
        echo "Pulling '$name'..."
        git -C "$name" pull --recurse-submodules
    fi
done
```

### The git-neko way

* Dynamic API Routing: Automatically identifies the correct GitHub endpoint. It uses `/users/{username}/repos` for public browsing or the authenticated `/user/repos` for private access, ensuring you get the full list of repos you have permission to view.
* State-Aware Syncing: Instead of a simple download, it checks your local file system. If a repo already exists, it intelligently switches to an "update" mode (using `git pull` or overwriting via `requests`) to keep your local mirror current.
* Hybrid Engine Support:
  * Lightweight Mode: Uses `requests` to pull repo snapshots quickly without needing `git` installed or **SSH keys** configured.
  * Developer Mode (`-g`): Interfaces directly with your local `git` binary to handle **full history**, **branch tracking**, and **submodule recursion**.
* Subprocess Management: Uses `Python`'s `subprocess` and `os` modules to provide a robust bridge between the `GitHub API` and your local shell, handling directory navigation and command execution automatically.`
