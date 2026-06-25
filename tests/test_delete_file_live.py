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

DELETE_FILE_CONTENT = b"delete file live test\n"
DELETE_FILE_SUCCESS_MESSAGE = "File was deleted successfully"


def create_graph_file(
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
) -> dict[str, Any]:
    target_user_id = live_asset_config["target_user_id"]
    file_name = f"sdkfied-delete-file-{uuid.uuid4().hex}.txt"
    response = microsoft_graph_client.put(
        f"/users/{target_user_id}/drive/root:/{file_name}:/content",
        content=DELETE_FILE_CONTENT,
    )
    response.raise_for_status()
    return response.json()


def delete_graph_file_if_exists(
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
    file_id: str | None,
) -> None:
    if not file_id:
        return

    target_user_id = live_asset_config["target_user_id"]
    response = microsoft_graph_client.delete(
        f"/users/{target_user_id}/drive/items/{file_id}"
    )
    if response.status_code != httpx.codes.NOT_FOUND:
        response.raise_for_status()


def assert_graph_file_deleted(
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
    file_id: str,
) -> None:
    target_user_id = live_asset_config["target_user_id"]
    response = microsoft_graph_client.get(
        f"/users/{target_user_id}/drive/items/{file_id}"
    )
    assert response.status_code == httpx.codes.NOT_FOUND


def run_delete_file_action(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    parameters: dict[str, Any],
) -> Any:
    input_data = build_soar_action_input(
        action="delete_file",
        asset_config={
            "auth_method": AUTH_METHOD_CLIENT_CREDENTIALS,
        },
        parameters=[parameters],
    )

    connector_app.handle(json.dumps(input_data))
    return connector_app.actions_manager.get_action_results()[-1]


@pytest.mark.parametrize(
    ("locator", "use_drive_id"),
    [
        ("file_id", False),
        ("file_id", True),
        ("file_path", False),
        ("file_path", True),
    ],
)
def test_delete_file_live_deletes_file(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
    locator: str,
    use_drive_id: bool,
) -> None:
    graph_file = create_graph_file(microsoft_graph_client, live_asset_config)
    file_id = graph_file["id"]
    file_name = graph_file["name"]
    drive_id = graph_file["parentReference"]["driveId"] if use_drive_id else ""

    parameters = {
        "file_id": file_id if locator == "file_id" else "",
        "drive_id": drive_id,
        "file_path": file_name if locator == "file_path" else "",
    }

    try:
        result = run_delete_file_action(
            connector_app,
            build_soar_action_input,
            parameters,
        )

        assert result.get_status() is True, result.get_message()
        assert result.get_message() == DELETE_FILE_SUCCESS_MESSAGE
        assert_graph_file_deleted(microsoft_graph_client, live_asset_config, file_id)
        file_id = None
    finally:
        delete_graph_file_if_exists(
            microsoft_graph_client,
            live_asset_config,
            file_id,
        )


@pytest.mark.parametrize(
    "parameters",
    [
        {
            "file_id": "",
            "drive_id": "",
            "file_path": "",
        },
        {
            "file_id": "INVALIDWIAZ3KR2L4Z2NAZTY3WX5S52AXW",
            "drive_id": "",
            "file_path": "",
        },
        {
            "file_id": "test",
            "drive_id": "invalid-drive-id",
            "file_path": "",
        },
        {
            "file_id": "",
            "drive_id": "",
            "file_path": "missing-file.txt",
        },
    ],
)
def test_delete_file_live_fails_for_invalid_inputs(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    parameters: dict[str, str],
) -> None:
    result = run_delete_file_action(
        connector_app,
        build_soar_action_input,
        parameters,
    )
    assert result.get_status() is False
