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

INVALID_UNICODE_VALUE = "⛰⛱⛲⛳⛵✔️❤️"
INVALID_PATH_VALUE = "invalid|path"
SCRIPT_LIKE_VALUE = "phantom.debug('on_start() called')"
SPECIAL_FOLDER_NAME = "#@$@$@$@$#@"
UNICODE_FOLDER_NAME = "A valid unicode name -⛰⛱⛲⛳⛵✔️❤️"
UNICODE_PARENT_FOLDER_NAME = "1 .❤️"
UNICODE_CHILD_FOLDER_NAME = "1.1 ❤️"


def run_create_folder_action(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    parameters: dict[str, Any],
) -> Any:
    input_data = build_soar_action_input(
        action="create_folder",
        asset_config={
            "auth_method": AUTH_METHOD_CLIENT_CREDENTIALS,
        },
        parameters=[parameters],
    )

    connector_app.handle(json.dumps(input_data))
    return connector_app.actions_manager.get_action_results()[-1]


def delete_folder_if_created(
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
    folder_id: str | None,
) -> None:
    if not folder_id:
        return

    target_user_id = live_asset_config["target_user_id"]
    delete_response = microsoft_graph_client.delete(
        f"/users/{target_user_id}/drive/items/{folder_id}"
    )
    if delete_response.status_code != httpx.codes.NOT_FOUND:
        delete_response.raise_for_status()


def assert_created_folder_exists(
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
    folder_id: str,
    folder_name: str,
) -> dict[str, Any]:
    target_user_id = live_asset_config["target_user_id"]
    graph_response = microsoft_graph_client.get(
        f"/users/{target_user_id}/drive/items/{folder_id}"
    )
    graph_response.raise_for_status()
    graph_folder = graph_response.json()

    assert graph_folder["id"] == folder_id
    assert graph_folder["name"] == folder_name
    assert "folder" in graph_folder
    return graph_folder


def test_create_folder_live_creates_folder_in_target_user_root(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
) -> None:
    folder_name = f"sdkfied-create-folder-{uuid.uuid4().hex}"
    created_folder_id: str | None = None

    try:
        result = run_create_folder_action(
            connector_app,
            build_soar_action_input,
            {
                "drive_id": "",
                "folder_id": "",
                "folder_path": "",
                "folder_name": folder_name,
                "auto_rename": False,
            },
        )
        assert result.get_status() is True, result.get_message()
        assert result.get_message() == (
            f"The folder: {folder_name} is created successfully"
        )

        created_folder = result.get_data()[0]
        created_folder_id = created_folder["id"]
        assert created_folder["name"] == folder_name
        assert "folder" in created_folder
        assert created_folder["parentReference"]["driveId"]

        graph_folder = assert_created_folder_exists(
            microsoft_graph_client,
            live_asset_config,
            created_folder_id,
            folder_name,
        )
        assert graph_folder["folder"]["childCount"] == 0
        assert (
            graph_folder["parentReference"]["driveId"]
            == (created_folder["parentReference"]["driveId"])
        )
    finally:
        delete_folder_if_created(
            microsoft_graph_client, live_asset_config, created_folder_id
        )


@pytest.mark.parametrize("folder_name", [UNICODE_FOLDER_NAME, SPECIAL_FOLDER_NAME])
def test_create_folder_live_creates_supported_special_folder_names(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
    folder_name: str,
) -> None:
    created_folder_id: str | None = None

    try:
        result = run_create_folder_action(
            connector_app,
            build_soar_action_input,
            {
                "drive_id": "",
                "folder_id": "",
                "folder_path": "",
                "folder_name": folder_name,
                "auto_rename": True,
            },
        )

        assert result.get_status() is True, result.get_message()
        created_folder = result.get_data()[0]
        created_folder_id = created_folder["id"]
        assert created_folder["name"] == folder_name
        assert_created_folder_exists(
            microsoft_graph_client,
            live_asset_config,
            created_folder_id,
            folder_name,
        )
    finally:
        delete_folder_if_created(
            microsoft_graph_client, live_asset_config, created_folder_id
        )


def test_create_folder_live_creates_child_folder_by_parent_path(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
) -> None:
    parent_name = f"sdkfied-parent-{uuid.uuid4().hex}-{UNICODE_PARENT_FOLDER_NAME}"
    parent_folder_id: str | None = None
    child_folder_id: str | None = None

    try:
        parent_result = run_create_folder_action(
            connector_app,
            build_soar_action_input,
            {
                "drive_id": "",
                "folder_id": "",
                "folder_path": "",
                "folder_name": parent_name,
                "auto_rename": False,
            },
        )
        assert parent_result.get_status() is True, parent_result.get_message()
        parent_folder = parent_result.get_data()[0]
        parent_folder_id = parent_folder["id"]

        child_result = run_create_folder_action(
            connector_app,
            build_soar_action_input,
            {
                "drive_id": "",
                "folder_id": "",
                "folder_path": parent_name,
                "folder_name": UNICODE_CHILD_FOLDER_NAME,
                "auto_rename": True,
            },
        )
        assert child_result.get_status() is True, child_result.get_message()

        child_folder = child_result.get_data()[0]
        child_folder_id = child_folder["id"]
        assert child_folder["name"] == UNICODE_CHILD_FOLDER_NAME
        assert child_folder["parentReference"]["id"] == parent_folder_id

        graph_child = assert_created_folder_exists(
            microsoft_graph_client,
            live_asset_config,
            child_folder_id,
            UNICODE_CHILD_FOLDER_NAME,
        )
        assert graph_child["parentReference"]["id"] == parent_folder_id
    finally:
        delete_folder_if_created(
            microsoft_graph_client, live_asset_config, parent_folder_id
        )


@pytest.mark.parametrize(
    "parameters",
    [
        {
            "drive_id": "test123",
            "folder_id": "test123",
            "folder_path": "test123",
            "folder_name": "test123",
            "auto_rename": True,
        },
        {
            "drive_id": "@$#@$@#$@#$#@",
            "folder_id": "",
            "folder_path": "",
            "folder_name": "test",
            "auto_rename": False,
        },
        {
            "drive_id": INVALID_UNICODE_VALUE,
            "folder_id": "",
            "folder_path": "",
            "folder_name": "test",
            "auto_rename": True,
        },
        {
            "drive_id": "",
            "folder_id": "@#$@#$@#$@##@#$#@#",
            "folder_path": "",
            "folder_name": "test",
            "auto_rename": True,
        },
        {
            "drive_id": "",
            "folder_id": "",
            "folder_path": "##@$#@$@##@$",
            "folder_name": "",
            "auto_rename": True,
        },
        {
            "drive_id": "",
            "folder_id": "",
            "folder_path": INVALID_PATH_VALUE,
            "folder_name": "test",
            "auto_rename": True,
        },
        {
            "drive_id": "",
            "folder_id": "",
            "folder_path": "",
            "folder_name": "invalid/name",
            "auto_rename": True,
        },
        {
            "drive_id": "",
            "folder_id": SCRIPT_LIKE_VALUE,
            "folder_path": "",
            "folder_name": "test",
            "auto_rename": True,
        },
    ],
)
def test_create_folder_live_fails_for_invalid_inputs(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
    parameters: dict[str, Any],
) -> None:
    result = run_create_folder_action(
        connector_app, build_soar_action_input, parameters
    )

    created_folder_id = None
    if result.get_data():
        created_folder_id = result.get_data()[0].get("id")
    delete_folder_if_created(
        microsoft_graph_client, live_asset_config, created_folder_id
    )

    assert result.get_status() is False
