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
from collections.abc import Callable
from typing import Any

import httpx
from soar_sdk.app import App

from src.consts import AUTH_METHOD_CLIENT_CREDENTIALS


def test_list_drive_live_lists_target_user_drives(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
) -> None:
    target_user_id = live_asset_config["target_user_id"]
    expected_response = microsoft_graph_client.get(f"/users/{target_user_id}/drives")
    expected_response.raise_for_status()
    expected_drives = expected_response.json()["value"]
    expected_by_id = {drive["id"]: drive for drive in expected_drives}

    input_data = build_soar_action_input(
        action="list_drive",
        asset_config={
            "auth_method": AUTH_METHOD_CLIENT_CREDENTIALS,
        },
    )

    connector_app.handle(json.dumps(input_data))

    result = connector_app.actions_manager.get_action_results()[-1]
    assert result.get_status() is True, result.get_message()
    assert result.get_summary()["total_drives"] > 0
    assert result.get_summary()["total_drives"] == len(expected_drives)
    assert result.get_message() == f"Total drives: {len(expected_drives)}"

    actual_drives = result.get_data()
    actual_by_id = {drive["id"]: drive for drive in actual_drives}
    assert actual_by_id.keys() == expected_by_id.keys()

    for drive_id, expected_drive in expected_by_id.items():
        actual_drive = actual_by_id[drive_id]
        assert actual_drive["name"] == expected_drive["name"]
        assert actual_drive["driveType"] == expected_drive["driveType"]
