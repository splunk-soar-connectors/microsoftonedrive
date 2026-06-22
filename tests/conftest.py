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
import os
from collections.abc import Callable, Generator
from typing import Any

import httpx
import pytest
from soar_sdk.app import App
from soar_sdk.shims.phantom.encryption_helper import encryption_helper

from src.app import create_ms_onedrive_soar_connector_app

from . import config as test_config

MICROSOFT_GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
MICROSOFT_GRAPH_SCOPE = "https://graph.microsoft.com/.default"
MICROSOFT_LOGIN_BASE_URL = "https://login.microsoftonline.com"


@pytest.fixture(scope="session", autouse=True)
def load_dotenv() -> None:
    test_config.load_dotenv_file()


@pytest.fixture(scope="session")
def live_asset_config(load_dotenv: None) -> dict[str, str]:
    config: dict[str, str] = {}
    missing: list[str] = []
    for name in test_config.ASSET_CONFIG_ENV_KEYS:
        value = test_config.get_asset_config_value(name)
        if not value:
            missing.append(name)
        else:
            config[name] = value

    if missing:
        raise AssertionError(
            "Missing required live test environment variables: " + ", ".join(missing)
        )

    return config


@pytest.fixture
def connector_app() -> App:
    return create_ms_onedrive_soar_connector_app()


@pytest.fixture
def microsoft_graph_client(
    live_asset_config: dict[str, str],
) -> Generator[httpx.Client]:
    response = httpx.post(
        f"{MICROSOFT_LOGIN_BASE_URL}/{live_asset_config['tenant_id']}/oauth2/v2.0/token",
        data={
            "client_id": live_asset_config["client_id"],
            "client_secret": live_asset_config["client_secret"],
            "grant_type": "client_credentials",
            "scope": MICROSOFT_GRAPH_SCOPE,
        },
        timeout=30.0,
    )
    response.raise_for_status()
    token = response.json()["access_token"]

    with httpx.Client(
        base_url=MICROSOFT_GRAPH_BASE_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    ) as client:
        yield client


@pytest.fixture
def build_soar_action_input(
    live_asset_config: dict[str, str],
) -> Callable[..., dict[str, Any]]:
    def _build_soar_action_input(
        *,
        action: str,
        asset_config: dict[str, Any] | None = None,
        parameters: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        asset_id = os.environ.get("SOAR_ASSET_ID", "123")
        config = {
            "app_version": "2.4.1-beta",
            "directory": ".",
            "main_module": "src.app:app",
            "client_id": live_asset_config["client_id"],
            "client_secret": encryption_helper.encrypt(
                live_asset_config["client_secret"],
                salt=asset_id,
            ),
            "tenant_id": live_asset_config["tenant_id"],
            "target_user_id": live_asset_config["target_user_id"],
        }
        if asset_config:
            config.update(asset_config)

        return {
            "identifier": action,
            "action": action,
            "asset_id": asset_id,
            "container_id": int(os.environ.get("SOAR_CONTAINER_ID", "456")),
            "config": config,
            "parameters": parameters or [{}],
        }

    return _build_soar_action_input
