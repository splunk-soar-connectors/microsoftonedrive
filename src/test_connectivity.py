# Copyright (c) 2026 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import time

import httpx
from soar_sdk import logging
from soar_sdk.abstract import SOARClient
from soar_sdk.auth import StaticTokenAuth

from .asset import Asset
from .auth import (
    get_auth_code_flow,
    get_client_credentials_flow,
    is_client_credentials_auth,
)
from .consts import (
    AUTHORIZATION_ERROR_STATE_KEY,
    AUTHORIZATION_URL_STATE_KEY,
    MICROSOFT_GRAPH_BASE_URL,
    REDIRECT_URI_STATE_KEY,
)


AUTHORIZE_WAIT_TIME = 15
AUTHORIZATION_POLL_ATTEMPTS = 35
AUTHORIZATION_POLL_INTERVAL = 3
TARGET_USER_ID_REQUIRED_MESSAGE = (
    "Target User ID is required for Client Credentials authentication"
)


def run_test_connectivity(
    soar: SOARClient,
    asset: Asset,
    *,
    oauth_callback_url: str,
    oauth_start_url: str,
) -> None:
    """test connectivity"""
    if is_client_credentials_auth(asset):
        run_client_credentials_test_connectivity(asset)
    else:
        run_delegated_test_connectivity(
            soar,
            asset,
            oauth_callback_url=oauth_callback_url,
            oauth_start_url=oauth_start_url,
        )


def run_delegated_test_connectivity(
    soar: SOARClient,
    asset: Asset,
    *,
    oauth_callback_url: str,
    oauth_start_url: str,
) -> None:
    asset.auth_state.pop(AUTHORIZATION_ERROR_STATE_KEY, None)
    flow = get_auth_code_flow(
        asset,
        str(soar.get_asset_id()),
        redirect_uri=oauth_callback_url,
    )

    phantom_base_url = soar.get("rest/system_info").json()["base_url"].rstrip("/")

    logging.info("Testing connectivity. Connecting...")
    logging.info(f"Using Phantom base URL as: {phantom_base_url}")
    logging.info("Using OAuth URL:")
    logging.info(oauth_callback_url)
    asset.auth_state[REDIRECT_URI_STATE_KEY] = oauth_callback_url
    asset.auth_state[AUTHORIZATION_URL_STATE_KEY] = flow.get_authorization_url()
    url_for_authorize_request = f"{oauth_start_url}?asset_id={soar.get_asset_id()}&"

    logging.info("Please authorize user in a separate tab using URL")
    logging.info(url_for_authorize_request)  # nosemgrep

    time.sleep(AUTHORIZE_WAIT_TIME)
    authorization_code = None
    for _ in range(AUTHORIZATION_POLL_ATTEMPTS):
        logging.progress("Waiting...")
        if authorization_error := asset.auth_state.get(AUTHORIZATION_ERROR_STATE_KEY):
            raise ValueError(authorization_error)
        authorization_code = flow.client.get_authorization_code(force_reload=True)
        if authorization_code:
            logging.info("Authenticated")
            break
        time.sleep(AUTHORIZATION_POLL_INTERVAL)

    if not authorization_code:
        raise TimeoutError("Timeout. Please try again later.")

    logging.info("")
    logging.info("Code Received")
    logging.info("Generating access token")
    token = flow.exchange_code_for_token(authorization_code)
    flow.client._store_token(token)

    logging.info("Getting info about the current user to verify token")
    with httpx.Client(
        base_url=MICROSOFT_GRAPH_BASE_URL,
        auth=StaticTokenAuth(token),
        timeout=30.0,
    ) as graph_client:
        response = graph_client.get("/me")
        response.raise_for_status()

    logging.info("Got current user info successfully")
    logging.info("Test Connectivity Passed")


def run_client_credentials_test_connectivity(asset: Asset) -> None:
    target_user_id = (asset.target_user_id or "").strip()
    if not target_user_id:
        raise ValueError(TARGET_USER_ID_REQUIRED_MESSAGE)

    logging.info("Testing connectivity. Connecting...")
    logging.info("Using Client Credentials authentication")
    logging.info("Generating access token")
    token = get_client_credentials_flow(asset).authenticate()

    logging.info("Getting root drive item for configured target user to verify token")
    with httpx.Client(
        base_url=MICROSOFT_GRAPH_BASE_URL,
        auth=StaticTokenAuth(token),
        timeout=30.0,
    ) as graph_client:
        response = graph_client.get(f"/users/{target_user_id}/drive/root")
        response.raise_for_status()

    logging.info("Got target user root drive item successfully")
    logging.info("Test Connectivity Passed")
