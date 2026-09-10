#!/usr/bin/env python3

"""
LogicMonitor Dashboard Synchronizer

Source of truth:
    GitHub repository

Behavior:
    - Dashboard doesn't exist in LogicMonitor -> CREATE
    - GitHub dashboard is newer -> UPDATE
    - LogicMonitor dashboard is newer/equal -> SKIP
    - --dry-run -> make no changes

Environment variables:

    LM_COMPANY
    LM_ACCESS_ID
    LM_ACCESS_KEY

    GITHUB_TOKEN
    GITHUB_REPO
        Example:
        mycompany/lm-dashboards

    GITHUB_BRANCH
        Default: main

    GITHUB_DASHBOARD_PATH
        Default: dashboards

    LM_DASHBOARD_GROUP_ID
        Default: 1

Usage:

    python3 sync_lm_dashboards.py --dry-run

    python3 sync_lm_dashboards.py

"""

import argparse
import base64
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LM_COMPANY = os.environ.get("LM_COMPANY")
LM_ACCESS_ID = os.environ.get("LM_ACCESS_ID")
LM_ACCESS_KEY = os.environ.get("LM_ACCESS_KEY")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")

GITHUB_DASHBOARD_PATH = os.environ.get(
    "GITHUB_DASHBOARD_PATH",
    "dashboards"
)

LM_DASHBOARD_GROUP_ID = int(
    os.environ.get("LM_DASHBOARD_GROUP_ID", "1")
)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

log = logging.getLogger("lm-dashboard-sync")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_config():

    required = {
        "LM_COMPANY": LM_COMPANY,
        "LM_ACCESS_ID": LM_ACCESS_ID,
        "LM_ACCESS_KEY": LM_ACCESS_KEY,
        "GITHUB_TOKEN": GITHUB_TOKEN,
        "GITHUB_REPO": GITHUB_REPO,
    }

    missing = [
        name for name, value in required.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            "Missing environment variables: "
            + ", ".join(missing)
        )


# ---------------------------------------------------------------------------
# GitHub API
# ---------------------------------------------------------------------------

GITHUB_API = "https://api.github.com"


def github_headers():

    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def github_get(url, params=None):

    response = requests.get(
        url,
        headers=github_headers(),
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def get_github_dashboard_files():

    url = (
        f"{GITHUB_API}/repos/"
        f"{GITHUB_REPO}/contents/"
        f"{GITHUB_DASHBOARD_PATH}"
    )

    items = github_get(
        url,
        params={"ref": GITHUB_BRANCH},
    )

    dashboards = []

    for item in items:

        if item["type"] != "file":
            continue

        if not item["name"].lower().endswith(".json"):
            continue

        dashboards.append(item)

    return dashboards


def get_github_file(path):

    url = (
        f"{GITHUB_API}/repos/"
        f"{GITHUB_REPO}/contents/{path}"
    )

    result = github_get(
        url,
        params={"ref": GITHUB_BRANCH},
    )

    content = base64.b64decode(
        result["content"]
    ).decode("utf-8")

    return json.loads(content)


def get_github_last_update(path):

    url = (
        f"{GITHUB_API}/repos/"
        f"{GITHUB_REPO}/commits"
    )

    commits = github_get(
        url,
        params={
            "path": path,
            "sha": GITHUB_BRANCH,
            "per_page": 1,
        },
    )

    if not commits:
        return None

    commit_date = commits[0]["commit"]["committer"]["date"]

    return datetime.fromisoformat(
        commit_date.replace("Z", "+00:00")
    )


# ---------------------------------------------------------------------------
# LogicMonitor REST v3
#
# Using the REST interface here makes the dashboard payload explicit.
# The same endpoints are available through the LM v3 SDK.
# ---------------------------------------------------------------------------

LM_BASE = None


def lm_headers():

    return {
        "Content-Type": "application/json",
        "X-Version": "3",
    }


def lm_get(path, params=None):

    url = LM_BASE + path

    response = requests.get(
        url,
        headers=lm_headers(),
        auth=(LM_ACCESS_ID, LM_ACCESS_KEY),
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


def lm_post(path, payload):

    url = LM_BASE + path

    response = requests.post(
        url,
        headers=lm_headers(),
        auth=(LM_ACCESS_ID, LM_ACCESS_KEY),
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


def lm_put(path, payload):

    url = LM_BASE + path

    response = requests.put(
        url,
        headers=lm_headers(),
        auth=(LM_ACCESS_ID, LM_ACCESS_KEY),
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


# ---------------------------------------------------------------------------
# LogicMonitor dashboards
# ---------------------------------------------------------------------------

def get_lm_dashboards():

    dashboards = []

    offset = 0
    size = 100

    while True:

        result = lm_get(
            "/dashboard/dashboards",
            params={
                "size": size,
                "offset": offset,
            },
        )

        data = result.get("data", {})

        batch = data.get("items", [])

        if not batch:
            break

        dashboards.extend(batch)

        if len(batch) < size:
            break

        offset += size

    return dashboards


def dashboard_name_from_file(path):

    filename = os.path.basename(path)

    if filename.lower().endswith(".json"):
        filename = filename[:-5]

    return filename


# ---------------------------------------------------------------------------
# Dashboard payload handling
# ---------------------------------------------------------------------------

def build_create_payload(dashboard):

    payload = dict(dashboard)

    payload.pop("id", None)
    payload.pop("lastUpdatedOn", None)

    payload.setdefault(
        "groupId",
        LM_DASHBOARD_GROUP_ID
    )

    return payload


def build_update_payload(dashboard):

    payload = dict(dashboard)

    # These are read-only LM properties.
    payload.pop("id", None)
    payload.pop("lastUpdatedOn", None)
    payload.pop("userPermission", None)

    return payload


# ---------------------------------------------------------------------------
# Synchronization
# ---------------------------------------------------------------------------

def sync_dashboard(
    github_file,
    github_dashboard,
    github_updated,
    lm_dashboard_map,
    dry_run,
):

    filename = github_file["name"]

    dashboard_name = dashboard_name_from_file(
        github_file["path"]
    )

    existing = lm_dashboard_map.get(
        dashboard_name.lower()
    )

    if not existing:

        log.info(
            "CREATE: %s | GitHub updated %s",
            dashboard_name,
            github_updated,
        )

        if not dry_run:

            payload = build_create_payload(
                github_dashboard
            )

            lm_post(
                "/dashboard/dashboards",
                payload,
            )

        return "created"

    lm_updated_raw = existing.get("lastUpdatedOn")

    if lm_updated_raw:

        # LogicMonitor normally returns epoch milliseconds.
        if lm_updated_raw > 10_000_000_000:
            lm_updated = datetime.fromtimestamp(
                lm_updated_raw / 1000,
                tz=timezone.utc,
            )
        else:
            lm_updated = datetime.fromtimestamp(
                lm_updated_raw,
                tz=timezone.utc,
            )

    else:
        lm_updated = None

    if not lm_updated:

        log.info(
            "UPDATE: %s | LM has no update timestamp",
            dashboard_name,
        )

        should_update = True

    else:

        should_update = (
            github_updated > lm_updated
        )

    if not should_update:

        log.info(
            "SKIP: %s | GitHub=%s LM=%s",
            dashboard_name,
            github_updated,
            lm_updated,
        )

        return "skipped"

    log.info(
        "UPDATE: %s | GitHub=%s LM=%s",
        dashboard_name,
        github_updated,
        lm_updated,
    )

    if not dry_run:

        payload = build_update_payload(
            github_dashboard
        )

        lm_put(
            f"/dashboard/dashboards/{existing['id']}",
            payload,
        )

    return "updated"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description="Synchronize LogicMonitor dashboards from GitHub"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without modifying LogicMonitor",
    )

    args = parser.parse_args()

    validate_config()

    global LM_BASE

    LM_BASE = (
        f"https://{LM_COMPANY}.logicmonitor.com"
        f"/santaba/rest"
    )

    log.info(
        "LogicMonitor account: %s",
        LM_COMPANY,
    )

    log.info(
        "GitHub repository: %s",
        GITHUB_REPO,
    )

    log.info(
        "GitHub branch: %s",
        GITHUB_BRANCH,
    )

    if args.dry_run:
        log.warning(
            "DRY RUN ENABLED - no changes will be made"
        )

    # -------------------------------------------------------
    # Get LogicMonitor dashboards
    # -------------------------------------------------------

    log.info("Loading LogicMonitor dashboards...")

    lm_dashboards = get_lm_dashboards()

    lm_dashboard_map = {}

    for dashboard in lm_dashboards:

        name = dashboard.get("name")

        if not name:
            continue

        lm_dashboard_map[
            name.lower()
        ] = dashboard

    log.info(
        "Found %d LogicMonitor dashboards",
        len(lm_dashboards),
    )

    # -------------------------------------------------------
    # Get GitHub dashboards
    # -------------------------------------------------------

    log.info(
        "Loading dashboards from GitHub..."
    )

    github_files = get_github_dashboard_files()

    log.info(
        "Found %d dashboard files",
        len(github_files),
    )

    counts = {
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
    }

    # -------------------------------------------------------
    # Synchronize
    # -------------------------------------------------------

    for github_file in github_files:

        path = github_file["path"]

        try:

            log.info(
                "Processing %s",
                path,
            )

            github_updated = (
                get_github_last_update(path)
            )

            if not github_updated:

                log.warning(
                    "Unable to determine GitHub update time: %s",
                    path,
                )

                continue

            github_dashboard = get_github_file(
                path
            )

            result = sync_dashboard(
                github_file=github_file,
                github_dashboard=github_dashboard,
                github_updated=github_updated,
                lm_dashboard_map=lm_dashboard_map,
                dry_run=args.dry_run,
            )

            counts[result] += 1

        except Exception as exc:

            counts["errors"] += 1

            log.exception(
                "ERROR processing %s: %s",
                path,
                exc,
            )

    # -------------------------------------------------------
    # Summary
    # -------------------------------------------------------

    print()
    print("=" * 60)
    print("LogicMonitor Dashboard Synchronization")
    print("=" * 60)

    print(
        f"Created : {counts['created']}"
    )

    print(
        f"Updated : {counts['updated']}"
    )

    print(
        f"Skipped : {counts['skipped']}"
    )

    print(
        f"Errors  : {counts['errors']}"
    )

    print("=" * 60)


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:

        log.warning(
            "Interrupted by user"
        )

        sys.exit(130)

    except Exception as exc:

        log.exception(
            "Fatal error: %s",
            exc,
        )

        sys.exit(1)
