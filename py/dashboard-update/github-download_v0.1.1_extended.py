#!/usr/bin/env python3

"""
Download LogicMonitor dashboards from the public GitHub repository.

Repository:
    https://github.com/logicmonitor/dashboards

No GitHub authentication is required.

The repository directory structure is preserved locally.
"""

import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import requests


# ============================================================
# Configuration
# ============================================================

GITHUB_OWNER = "logicmonitor"
GITHUB_REPO = "dashboards"

# Check the repository and use the appropriate branch.
GITHUB_BRANCH = "master"

# Local destination
LOCAL_ROOT = Path("./lm-dashboards")


# ============================================================
# Download repository
# ============================================================

def download_repository():

    url = (
        f"https://github.com/{GITHUB_OWNER}/"
        f"{GITHUB_REPO}/archive/refs/heads/"
        f"{GITHUB_BRANCH}.zip"
    )

    print(f"Downloading:")
    print(f"  {url}")
    print()

    response = requests.get(
        url,
        timeout=120,
    )

    response.raise_for_status()

    return response.content


# ============================================================
# Extract repository
# ============================================================

def extract_repository(zip_data, destination):

    with tempfile.TemporaryDirectory() as temp_dir:

        zip_path = Path(temp_dir) / "repository.zip"

        zip_path.write_bytes(zip_data)

        print("Extracting repository...")

        with zipfile.ZipFile(zip_path, "r") as archive:

            archive.extractall(temp_dir)

        # GitHub creates a directory such as:
        #
        # dashboards-master/
        #
        # We want the contents of that directory directly
        # under LOCAL_ROOT.

        extracted_dirs = [
            p for p in Path(temp_dir).iterdir()
            if p.is_dir()
        ]

        if len(extracted_dirs) != 1:

            raise RuntimeError(
                "Could not determine GitHub repository "
                "root directory."
            )

        repository_root = extracted_dirs[0]

        destination.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(
            f"Copying repository to: {destination}"
        )

        for item in repository_root.iterdir():

            target = destination / item.name

            if item.is_dir():

                shutil.copytree(
                    item,
                    target,
                    dirs_exist_ok=True,
                )

            else:

                shutil.copy2(
                    item,
                    target,
                )


# ============================================================
# Main
# ============================================================

def main():

    print()
    print("=" * 60)
    print("LogicMonitor GitHub Dashboard Downloader")
    print("=" * 60)

    print(
        f"Repository : "
        f"{GITHUB_OWNER}/{GITHUB_REPO}"
    )

    print(
        f"Branch     : {GITHUB_BRANCH}"
    )

    print(
        f"Destination: {LOCAL_ROOT}"
    )

    print("=" * 60)
    print()

    try:

        zip_data = download_repository()

        extract_repository(
            zip_data,
            LOCAL_ROOT,
        )

    except requests.RequestException as exc:

        print(
            f"ERROR downloading repository: {exc}"
        )

        sys.exit(1)

    except zipfile.BadZipFile:

        print(
            "ERROR: GitHub did not return a valid ZIP archive."
        )

        sys.exit(1)

    except Exception as exc:

        print(
            f"ERROR: {exc}"
        )

        sys.exit(1)

    print()
    print("=" * 60)
    print("Download complete")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()