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
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from soar_sdk.app import App

from src.consts import AUTH_METHOD_CLIENT_CREDENTIALS

DELETE_FOLDER_SUCCESS_MESSAGE = "The folder is deleted successfully"
INVALID_UNICODE_VALUE = "⛰⛱⛲⛳⛵"
INVALID_PATH_VALUE = "invalid|path"
SCRIPT_LIKE_VALUE = "phantom.debug('on_start() called')"


def create_graph_folder(
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
) -> dict[str, Any]:
    target_user_id = live_asset_config["target_user_id"]
    folder_name = f"sdkfied-delete-folder-{uuid.uuid4().hex}"
    response = microsoft_graph_client.post(
        f"/users/{target_user_id}/drive/root/children",
        json={
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail",
        },
    )
    response.raise_for_status()
    folder = response.json()
    folder["root_path"] = folder_name
    return folder


def delete_graph_folder_if_exists(
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
    folder_id: str | None,
) -> None:
    if not folder_id:
        return

    target_user_id = live_asset_config["target_user_id"]
    response = microsoft_graph_client.delete(
        f"/users/{target_user_id}/drive/items/{folder_id}"
    )
    if response.status_code != httpx.codes.NOT_FOUND:
        response.raise_for_status()


def assert_graph_folder_absent(
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
    folder_id: str,
) -> None:
    target_user_id = live_asset_config["target_user_id"]
    response = microsoft_graph_client.get(
        f"/users/{target_user_id}/drive/items/{folder_id}"
    )
    assert response.status_code == httpx.codes.NOT_FOUND, response.text


def run_delete_folder_action(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    parameters: dict[str, str],
) -> Any:
    input_data = build_soar_action_input(
        action="delete_folder",
        asset_config={
            "auth_method": AUTH_METHOD_CLIENT_CREDENTIALS,
        },
        parameters=[parameters],
    )

    connector_app.handle(json.dumps(input_data))
    return connector_app.actions_manager.get_action_results()[-1]


@pytest.mark.parametrize(
    "case_name",
    [
        "folder_id",
        "drive_id_folder_id",
        "folder_path",
        "drive_id_folder_path",
    ],
)
def test_delete_folder_live_deletes_folder_by_supported_identifier(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
    case_name: str,
) -> None:
    folder = create_graph_folder(microsoft_graph_client, live_asset_config)
    folder_id = folder["id"]
    drive_id = folder["parentReference"]["driveId"]

    parameters_by_case = {
        "folder_id": {
            "drive_id": "",
            "folder_id": folder_id,
            "folder_path": "",
        },
        "drive_id_folder_id": {
            "drive_id": drive_id,
            "folder_id": folder_id,
            "folder_path": "",
        },
        "folder_path": {
            "drive_id": "",
            "folder_id": "",
            "folder_path": folder["root_path"],
        },
        "drive_id_folder_path": {
            "drive_id": drive_id,
            "folder_id": "",
            "folder_path": folder["root_path"],
        },
    }

    try:
        result = run_delete_folder_action(
            connector_app,
            build_soar_action_input,
            parameters_by_case[case_name],
        )

        assert result.get_status() is True, result.get_message()
        assert result.get_message() == DELETE_FOLDER_SUCCESS_MESSAGE
        assert_graph_folder_absent(microsoft_graph_client, live_asset_config, folder_id)
        folder_id = None
    finally:
        delete_graph_folder_if_exists(
            microsoft_graph_client, live_asset_config, folder_id
        )


@pytest.mark.parametrize(
    "parameters",
    [
        {"drive_id": "", "folder_id": "", "folder_path": ""},
        {"drive_id": "test123", "folder_id": "test123", "folder_path": "test123"},
        {"drive_id": "#@@$#@$@", "folder_id": "test", "folder_path": ""},
        {"drive_id": "", "folder_id": "@$#@$@#$@$", "folder_path": ""},
        {"drive_id": "", "folder_id": "", "folder_path": "#@$@$@$@$##"},
        {"drive_id": "", "folder_id": "", "folder_path": INVALID_PATH_VALUE},
        {
            "drive_id": INVALID_UNICODE_VALUE,
            "folder_id": "test",
            "folder_path": "",
        },
        {
            "drive_id": "",
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
def test_delete_folder_live_fails_for_invalid_inputs(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    parameters: dict[str, str],
) -> None:
    result = run_delete_folder_action(
        connector_app, build_soar_action_input, parameters
    )

    assert result.get_status() is False
