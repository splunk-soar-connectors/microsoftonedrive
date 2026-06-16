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
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from soar_sdk.app import App
from soar_sdk.shims.phantom.encryption_helper import encryption_helper

from src.app import create_ms_onedrive_soar_connector_app


ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
REQUIRED_ASSET_CONFIG_KEYS = (
    "tenant_id",
    "client_id",
    "client_secret",
    "target_user_id",
)


@pytest.fixture(scope="session", autouse=True)
def load_dotenv() -> None:
    if not ENV_FILE.exists():
        return

    for raw_line in ENV_FILE.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


@pytest.fixture(scope="session")
def live_asset_config(load_dotenv: None) -> dict[str, str]:
    missing = [name for name in REQUIRED_ASSET_CONFIG_KEYS if not os.environ.get(name)]
    if missing:
        raise AssertionError(
            "Missing required live test environment variables: " + ", ".join(missing)
        )

    return {name: os.environ[name] for name in REQUIRED_ASSET_CONFIG_KEYS}


@pytest.fixture
def connector_app() -> App:
    return create_ms_onedrive_soar_connector_app()


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
