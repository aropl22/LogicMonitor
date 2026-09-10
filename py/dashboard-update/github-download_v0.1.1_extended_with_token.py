#!/usr/bin/env python3

"""
Download LogicMonitor dashboards from the public GitHub repository.

Only dashboards modified within the last 3 months are downloaded.
The original GitHub folder structure is preserved locally.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


GITHUB_REPO = "logicmonitor/dashboards"
GITHUB_BRANCH = "master"
LOCAL_ROOT = Path("./lm-dashboards")
TOKEN_FILE = Path("/home/u22/git_tokens/lm-dashboards.tk")

GITHUB_API = "https://api.github.com"


def get_github_token():
    if not TOKEN_FILE.exists():
        raise FileNotFoundError(
            f"GitHub token file not found: {TOKEN_FILE}"
        )

    token = TOKEN_FILE.read_text().strip()

    if not token:
        raise RuntimeError("GitHub token file is empty.")

    return token


def get_repository_files(headers):
    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/git/trees/{GITHUB_BRANCH}"

    response = requests.get(
        url,
        headers=headers,
        params={"recursive": "1"},
        timeout=30,
    )
    response.raise_for_status()

    tree = response.json()["tree"]

    return [
        item["path"]
        for item in tree
        if item["type"] == "blob"
        and item["path"].lower().endswith(".json")
        and not item["path"].startswith("Archive/")
        and not item["path"].startswith("Packages/")
    ]


def get_last_modified(path, headers):
    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/commits"

    response = requests.get(
        url,
        headers=headers,
        params={
            "path": path,
            "sha": GITHUB_BRANCH,
            "per_page": 1,
        },
        timeout=30,
    )
    response.raise_for_status()

    commits = response.json()

    if not commits:
        return None

    date = commits[0]["commit"]["committer"]["date"]

    return datetime.fromisoformat(
        date.replace("Z", "+00:00")
    )


def download_dashboard(path, headers):
    url = (
        f"https://raw.githubusercontent.com/"
        f"{GITHUB_REPO}/{GITHUB_BRANCH}/{path}"
    )

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()

    destination = LOCAL_ROOT / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)


def main():
    print(f"Repository:  {GITHUB_REPO}")
    print(f"Branch:      {GITHUB_BRANCH}")
    print(f"Destination: {LOCAL_ROOT}")
    print()

    try:
        token = get_github_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        print("Finding dashboard files...")
        files = get_repository_files(headers)

        print(f"Found {len(files)} dashboard files.")
        print()

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)

        recent_files = []

        for path in files:
            last_modified = get_last_modified(path, headers)

            if last_modified and last_modified >= cutoff_date:
                recent_files.append((path, last_modified))

        print(
            f"Found {len(recent_files)} dashboards "
            f"modified within the last 3 months."
        )
        print()

        for path, last_modified in recent_files:
            print(
                f"Downloading: {path} "
                f"(modified {last_modified.date()})"
            )
            download_dashboard(path, headers)

        print()
        print(
            f"Downloaded {len(recent_files)} dashboards "
            f"to {LOCAL_ROOT}"
        )

    except requests.RequestException as exc:
        print(f"ERROR: GitHub request failed: {exc}")
        sys.exit(1)

    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()