#!/usr/bin/env python3

"""
Download LogicMonitor dashboards from the public GitHub repository.

The repository structure is preserved under LOCAL_ROOT.
"""

import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import requests


GITHUB_REPO = "logicmonitor/dashboards"
GITHUB_BRANCH = "master"
LOCAL_ROOT = Path("./lm-dashboards")


def download_repository():
    url = (
        f"https://github.com/{GITHUB_REPO}/archive/"
        f"refs/heads/{GITHUB_BRANCH}.zip"
    )

    print(f"Downloading {GITHUB_REPO} ({GITHUB_BRANCH})...")

    response = requests.get(url, timeout=120)
    response.raise_for_status()

    return response.content


def extract_repository(zip_data, destination):
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "repository.zip"
        zip_path.write_bytes(zip_data)

        print("Extracting repository...")

        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(temp_dir)

        repository_dirs = [
            path for path in Path(temp_dir).iterdir()
            if path.is_dir()
        ]

        if len(repository_dirs) != 1:
            raise RuntimeError(
                "Unable to determine the repository directory."
            )

        repository_root = repository_dirs[0]

        destination.mkdir(parents=True, exist_ok=True)

        for item in repository_root.iterdir():
            target = destination / item.name

            if item.is_dir():
                shutil.copytree(
                    item,
                    target,
                    dirs_exist_ok=True,
                )
            else:
                shutil.copy2(item, target)


def main():
    print(f"Repository: {GITHUB_REPO}")
    print(f"Branch:     {GITHUB_BRANCH}")
    print(f"Destination: {LOCAL_ROOT}")
    print()

    try:
        zip_data = download_repository()
        extract_repository(zip_data, LOCAL_ROOT)

        print()
        print(f"Dashboard files downloaded to {LOCAL_ROOT}")

    except requests.RequestException as exc:
        print(f"ERROR: Failed to download repository: {exc}")
        sys.exit(1)

    except zipfile.BadZipFile:
        print("ERROR: The downloaded file is not a valid ZIP archive.")
        sys.exit(1)

    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()