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
import uuid
from collections.abc import Callable, Generator
from typing import Any

import httpx
import pytest
from soar_sdk.app import App

from src.consts import AUTH_METHOD_CLIENT_CREDENTIALS


INVALID_UNICODE_VALUE = "⛰⛱⛲⛳⛵"
TEST_FILE_NAME = "list-items-live-test.txt"
TEST_FILE_CONTENT = b"list items live test\n"


@pytest.fixture
def list_items_test_folder(
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
) -> Generator[dict[str, Any]]:
    target_user_id = live_asset_config["target_user_id"]
    folder_name = f"sdkfied-list-items-{uuid.uuid4().hex}"

    folder_response = microsoft_graph_client.post(
        f"/users/{target_user_id}/drive/root/children",
        json={
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail",
        },
    )
    folder_response.raise_for_status()
    folder = folder_response.json()

    file_response = microsoft_graph_client.put(
        f"/users/{target_user_id}/drive/root:/{folder_name}/{TEST_FILE_NAME}:/content",
        content=TEST_FILE_CONTENT,
    )
    file_response.raise_for_status()
    uploaded_file = file_response.json()

    try:
        yield {
            "folder_path": folder_name,
            "expected_item_id": uploaded_file["id"],
            "expected_drive_id": uploaded_file["parentReference"]["driveId"],
        }
    finally:
        delete_response = microsoft_graph_client.delete(
            f"/users/{target_user_id}/drive/items/{folder['id']}"
        )
        delete_response.raise_for_status()


def test_list_items_live_lists_configured_folder(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    list_items_test_folder: dict[str, Any],
) -> None:
    input_data = build_soar_action_input(
        action="list_items",
        asset_config={
            "auth_method": AUTH_METHOD_CLIENT_CREDENTIALS,
        },
        parameters=[
            {
                "drive_id": "",
                "folder_id": "",
                "folder_path": list_items_test_folder["folder_path"],
            }
        ],
    )

    connector_app.handle(json.dumps(input_data))

    result = connector_app.actions_manager.get_action_results()[-1]
    assert result.get_status() is True, result.get_message()
    assert result.get_summary()["total_items"] > 0

    data = result.get_data()
    expected_item_id = list_items_test_folder["expected_item_id"]
    expected_drive_id = list_items_test_folder["expected_drive_id"]

    assert any(item.get("id") == expected_item_id for item in data)
    assert any(
        item.get("parentReference", {}).get("driveId") == expected_drive_id
        for item in data
    )


@pytest.mark.parametrize(
    "parameters",
    [
        {"drive_id": "test123", "folder_id": "test123", "folder_path": "test123"},
        {"drive_id": "@$@#$#@$#@", "folder_id": "test", "folder_path": ""},
        {"drive_id": "", "folder_id": "#@$@#$$#@", "folder_path": ""},
        {"drive_id": "", "folder_id": "", "folder_path": "#$#@$@$@$@"},
        {
            "drive_id": INVALID_UNICODE_VALUE,
            "folder_id": INVALID_UNICODE_VALUE,
            "folder_path": "",
        },
    ],
)
def test_list_items_live_fails_for_invalid_identifiers(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    parameters: dict[str, str],
) -> None:
    input_data = build_soar_action_input(
        action="list_items",
        asset_config={
            "auth_method": AUTH_METHOD_CLIENT_CREDENTIALS,
        },
        parameters=[parameters],
    )

    connector_app.handle(json.dumps(input_data))

    result = connector_app.actions_manager.get_action_results()[-1]
    assert result.get_status() is False
