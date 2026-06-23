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
INVALID_PATH_VALUE = "invalid|path"
SCRIPT_LIKE_VALUE = "phantom.debug('on_start() called')"
CHILD_FOLDER_NAME = "child-folder"
ROOT_FILE_NAME = "list-items-live-test.txt"
CHILD_FILE_NAME = "list-items-child-live-test.txt"
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
    drive_id = folder["parentReference"]["driveId"]

    file_response = microsoft_graph_client.put(
        f"/users/{target_user_id}/drive/root:/{folder_name}/{ROOT_FILE_NAME}:/content",
        content=TEST_FILE_CONTENT,
    )
    file_response.raise_for_status()
    uploaded_root_file = file_response.json()

    child_folder_response = microsoft_graph_client.post(
        f"/drives/{drive_id}/items/{folder['id']}/children",
        json={
            "name": CHILD_FOLDER_NAME,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail",
        },
    )
    child_folder_response.raise_for_status()
    child_folder = child_folder_response.json()

    child_file_response = microsoft_graph_client.put(
        f"/drives/{drive_id}/items/{child_folder['id']}:/{CHILD_FILE_NAME}:/content",
        content=TEST_FILE_CONTENT,
    )
    child_file_response.raise_for_status()
    uploaded_child_file = child_file_response.json()

    try:
        yield {
            "folder_path": folder_name,
            "folder_id": folder["id"],
            "drive_id": drive_id,
            "root_file_id": uploaded_root_file["id"],
            "child_folder_id": child_folder["id"],
            "child_file_id": uploaded_child_file["id"],
            "expected_item_ids": {
                uploaded_root_file["id"],
                child_folder["id"],
                uploaded_child_file["id"],
            },
            "expected_drive_id": drive_id,
        }
    finally:
        delete_response = microsoft_graph_client.delete(
            f"/users/{target_user_id}/drive/items/{folder['id']}"
        )
        delete_response.raise_for_status()


def run_list_items_action(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    parameters: dict[str, str],
) -> Any:
    input_data = build_soar_action_input(
        action="list_items",
        asset_config={
            "auth_method": AUTH_METHOD_CLIENT_CREDENTIALS,
        },
        parameters=[parameters],
    )

    connector_app.handle(json.dumps(input_data))
    return connector_app.actions_manager.get_action_results()[-1]


def assert_expected_items_returned(
    result: Any,
    list_items_test_folder: dict[str, Any],
    *,
    exact: bool,
) -> None:
    data = result.get_data()
    actual_ids = {item.get("id") for item in data}
    expected_ids = list_items_test_folder["expected_item_ids"]
    expected_drive_id = list_items_test_folder["expected_drive_id"]

    if exact:
        assert actual_ids == expected_ids
    else:
        assert expected_ids <= actual_ids

    assert any(
        item.get("parentReference", {}).get("driveId") == expected_drive_id
        for item in data
    )
    assert list_items_test_folder["child_file_id"] in actual_ids


def test_list_items_live_lists_configured_folder(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    list_items_test_folder: dict[str, Any],
) -> None:
    result = run_list_items_action(
        connector_app,
        build_soar_action_input,
        {
            "drive_id": "",
            "folder_id": "",
            "folder_path": list_items_test_folder["folder_path"],
        },
    )

    assert result.get_status() is True, result.get_message()
    assert result.get_summary()["total_items"] == len(
        list_items_test_folder["expected_item_ids"]
    )
    assert_expected_items_returned(result, list_items_test_folder, exact=True)


@pytest.mark.parametrize(
    "case_name",
    [
        "folder_id",
        "drive_id_folder_id",
        "drive_id_folder_path",
        "drive_id_root",
        "default_root",
    ],
)
def test_list_items_live_lists_items_by_supported_identifiers(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    list_items_test_folder: dict[str, Any],
    case_name: str,
) -> None:
    parameters_by_case = {
        "folder_id": {
            "drive_id": "",
            "folder_id": list_items_test_folder["folder_id"],
            "folder_path": "",
        },
        "drive_id_folder_id": {
            "drive_id": list_items_test_folder["drive_id"],
            "folder_id": list_items_test_folder["folder_id"],
            "folder_path": "",
        },
        "drive_id_folder_path": {
            "drive_id": list_items_test_folder["drive_id"],
            "folder_id": "",
            "folder_path": list_items_test_folder["folder_path"],
        },
        "drive_id_root": {
            "drive_id": list_items_test_folder["drive_id"],
            "folder_id": "",
            "folder_path": "",
        },
        "default_root": {
            "drive_id": "",
            "folder_id": "",
            "folder_path": "",
        },
    }

    result = run_list_items_action(
        connector_app,
        build_soar_action_input,
        parameters_by_case[case_name],
    )

    assert result.get_status() is True, result.get_message()
    assert result.get_summary()["total_items"] >= len(
        list_items_test_folder["expected_item_ids"]
    )
    assert_expected_items_returned(
        result,
        list_items_test_folder,
        exact=case_name not in {"drive_id_root", "default_root"},
    )


@pytest.mark.parametrize(
    "parameters",
    [
        {"drive_id": "test123", "folder_id": "test123", "folder_path": "test123"},
        {"drive_id": "@$@#$#@$#@", "folder_id": "test", "folder_path": ""},
        {"drive_id": "", "folder_id": "#@$@#$$#@", "folder_path": ""},
        {"drive_id": "", "folder_id": "", "folder_path": "#$#@$@$@$@"},
        {"drive_id": "", "folder_id": "", "folder_path": INVALID_PATH_VALUE},
        {
            "drive_id": INVALID_UNICODE_VALUE,
            "folder_id": INVALID_UNICODE_VALUE,
            "folder_path": "",
        },
        {
            "drive_id": SCRIPT_LIKE_VALUE,
            "folder_id": "test",
            "folder_path": "",
        },
        {
            "drive_id": "",
            "folder_id": SCRIPT_LIKE_VALUE,
            "folder_path": "",
        },
        {
            "drive_id": "",
            "folder_id": "",
            "folder_path": SCRIPT_LIKE_VALUE,
        },
    ],
)
def test_list_items_live_fails_for_invalid_identifiers(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    parameters: dict[str, str],
) -> None:
    result = run_list_items_action(connector_app, build_soar_action_input, parameters)
    assert result.get_status() is False
