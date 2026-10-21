
#!/usr/bin/env python3

import os
import logicmonitor_sdk


def api_auth_from_env():
    """
    Connect to the LogicMonitor REST API using environment variables.

    Required environment variables:
        LM_ACCESS_ID
        LM_ACCESS_KEY
        LM_ACCOUNT
    """

    # Read credentials from environment variables
    access_id = os.getenv("LM_ACCESS_ID")
    access_key = os.getenv("LM_ACCESS_KEY")
    account = os.getenv("LM_ACCOUNT")

    # Validate required credentials
    missing = [
        name
        for name, value in [
            ("LM_ACCESS_ID", access_id),
            ("LM_ACCESS_KEY", access_key),
            ("LM_ACCOUNT", account),
        ]
        if not value
    ]

    if missing:
        raise ValueError(
            "Missing required environment variables: "
            + ", ".join(missing)
        )

    # Configure API credentials
    configuration = logicmonitor_sdk.Configuration()
    configuration.access_id = access_id
    configuration.access_key = access_key
    configuration.company = account

    # Create API client
    api_client = logicmonitor_sdk.LMApi(
        logicmonitor_sdk.ApiClient(configuration)
    )

    return api_client
