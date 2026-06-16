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
import json
import os
from pathlib import Path

from soar_sdk.shims.phantom.encryption_helper import encryption_helper

from src.app import create_ms_onedrive_soar_connector_app
from src.consts import AUTH_METHOD_CLIENT_CREDENTIALS


ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
REQUIRED_ASSET_CONFIG_KEYS = (
    "tenant_id",
    "client_id",
    "client_secret",
    "target_user_id",
)


def load_dotenv() -> None:
    if not ENV_FILE.exists():
        return

    for raw_line in ENV_FILE.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def required_live_config() -> dict[str, str]:
    load_dotenv()
    missing = [name for name in REQUIRED_ASSET_CONFIG_KEYS if not os.environ.get(name)]
    if missing:
        raise AssertionError(
            "Missing required live test environment variables: " + ", ".join(missing)
        )

    return {name: os.environ[name] for name in REQUIRED_ASSET_CONFIG_KEYS}


def test_client_credentials_test_connectivity_live() -> None:
    config = required_live_config()
    asset_id = os.environ.get("SOAR_ASSET_ID", "123")
    container_id = int(os.environ.get("SOAR_CONTAINER_ID", "456"))

    app = create_ms_onedrive_soar_connector_app()
    input_data = {
        "identifier": "test_connectivity",
        "action": "test_connectivity",
        "asset_id": asset_id,
        "container_id": container_id,
        "config": {
            "app_version": "2.4.1-beta",
            "directory": ".",
            "main_module": "src.app:app",
            "client_id": config["client_id"],
            "client_secret": encryption_helper.encrypt(
                config["client_secret"],
                salt=asset_id,
            ),
            "tenant_id": config["tenant_id"],
            "auth_method": AUTH_METHOD_CLIENT_CREDENTIALS,
            "target_user_id": config["target_user_id"],
        },
        "parameters": [{}],
    }

    app.handle(json.dumps(input_data))

    result = app.actions_manager.get_action_results()[-1]
    assert result.get_status() is True, result.get_message()
