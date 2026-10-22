#!/usr/bin/env python3

"""Download recently modified LogicMonitor dashboards from GitHub."""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

GITHUB_REPO = "logicmonitor/dashboards"
GITHUB_BRANCH = "master"
GITHUB_API = "https://api.github.com"


def get_required_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Required environment variable {name} is not set.")
    return value


def main():
    try:
        token = get_required_env("GITHUB_TOKEN")

        try:
            days = int(get_required_env("DASHBOARD_DAYS"))
        except ValueError as exc:
            raise ValueError("DASHBOARD_DAYS must be a positive integer.") from exc

        if days <= 0:
            raise ValueError("DASHBOARD_DAYS must be greater than zero.")

        output_dir = Path(
            os.getenv("OUTPUT_DIR", "./artifacts")
        ).resolve()

        output_root = output_dir / f"lm-dashboards_{days}"
        output_root.mkdir(parents=True, exist_ok=True)

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        print(f"Repository: {GITHUB_REPO}")
        print(f"Branch: {GITHUB_BRANCH}")
        print(f"Lookback: {days} days")
        print(f"Destination: {output_root}")
        print()

        # Find JSON files in the repository.
        url = f"{GITHUB_API}/repos/{GITHUB_REPO}/git/trees/{GITHUB_BRANCH}"
        response = requests.get(
            url, headers=headers, params={"recursive": "1"}, timeout=30
        )
        response.raise_for_status()

        files = [
            item["path"]
            for item in response.json()["tree"]
            if item["type"] == "blob"
            and item["path"].lower().endswith(".json")
            and not item["path"].startswith(("Archive/", "Packages/"))
        ]

        print(f"Found {len(files)} JSON files.")

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        downloaded = 0

        # Check each file's most recent commit date.
        for path in files:
            response = requests.get(
                f"{GITHUB_API}/repos/{GITHUB_REPO}/commits",
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
                continue

            date_string = commits[0]["commit"]["committer"]["date"]
            last_modified = datetime.fromisoformat(
                date_string.replace("Z", "+00:00")
            )

            if last_modified < cutoff_date:
                continue

            # Download and preserve the repository folder structure.
            print(f"Downloading: {path} (modified {last_modified.date()})")

            response = requests.get(
                f"https://raw.githubusercontent.com/"
                f"{GITHUB_REPO}/{GITHUB_BRANCH}/{path}",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            destination = output_root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(response.content)
            downloaded += 1

        print(f"\nDownloaded {downloaded} dashboards to {output_root}")

    except (requests.RequestException, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()