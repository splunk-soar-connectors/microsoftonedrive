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
from pathlib import Path
from typing import Any

import httpx
import pytest
from soar_sdk.app import App

from src.consts import AUTH_METHOD_CLIENT_CREDENTIALS

SCRIPT_LIKE_VALUE = "phantom.debug('on_start() called')"
UPLOAD_FILE_CONTENT = b"upload file live test\n"
UPLOAD_FILE_SUCCESS_MESSAGE = "The file is uploaded successfully"


def create_vault_file(
    connector_app: App,
    tmp_path: Path,
    container_id: int,
    *,
    file_name: str = "upload-source.txt",
) -> str:
    file_path = tmp_path / file_name
    file_path.write_bytes(UPLOAD_FILE_CONTENT)
    return connector_app.soar_client.vault.add_attachment(
        container_id=container_id,
        file_location=str(file_path),
        file_name=file_name,
    )


def run_upload_file_action(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    parameters: dict[str, Any],
) -> Any:
    input_data = build_soar_action_input(
        action="upload_file",
        asset_config={
            "auth_method": AUTH_METHOD_CLIENT_CREDENTIALS,
        },
        parameters=[parameters],
    )

    connector_app.handle(json.dumps(input_data))
    return connector_app.actions_manager.get_action_results()[-1]


def delete_uploaded_file_if_exists(
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


def assert_uploaded_file_content(
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
    file_id: str,
) -> None:
    target_user_id = live_asset_config["target_user_id"]
    response = microsoft_graph_client.get(
        f"/users/{target_user_id}/drive/items/{file_id}/content",
        follow_redirects=True,
    )
    response.raise_for_status()
    assert response.content == UPLOAD_FILE_CONTENT


@pytest.mark.parametrize("use_drive_id", [False, True])
def test_upload_file_live_uploads_vault_file_to_target_user_root(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
    tmp_path: Path,
    use_drive_id: bool,
) -> None:
    action_input = build_soar_action_input(action="upload_file")
    vault_id = create_vault_file(
        connector_app,
        tmp_path,
        action_input["container_id"],
    )
    drive_id = ""
    if use_drive_id:
        drive_response = microsoft_graph_client.get(
            f"/users/{live_asset_config['target_user_id']}/drive"
        )
        drive_response.raise_for_status()
        drive_id = drive_response.json()["id"]

    file_name = f"sdkfied-upload-{uuid.uuid4().hex}.txt"
    uploaded_file_id: str | None = None

    try:
        result = run_upload_file_action(
            connector_app,
            build_soar_action_input,
            {
                "drive_id": drive_id,
                "vault_id": vault_id,
                "file_path": file_name,
                "auto_rename": False,
            },
        )

        assert result.get_status() is True, result.get_message()
        assert result.get_message() == UPLOAD_FILE_SUCCESS_MESSAGE

        uploaded_file = result.get_data()[0]
        uploaded_file_id = uploaded_file["id"]
        assert uploaded_file["name"] == file_name
        assert uploaded_file["size"] == len(UPLOAD_FILE_CONTENT)
        assert uploaded_file["parentReference"]["driveId"]
        if drive_id:
            assert uploaded_file["parentReference"]["driveId"] == drive_id

        assert_uploaded_file_content(
            microsoft_graph_client,
            live_asset_config,
            uploaded_file_id,
        )
    finally:
        delete_uploaded_file_if_exists(
            microsoft_graph_client, live_asset_config, uploaded_file_id
        )


@pytest.mark.parametrize(
    "parameter_overrides",
    [
        {
            "drive_id": "test123",
            "file_path": "test.txt",
        },
        {
            "drive_id": "@#@#$@##",
            "file_path": "test.txt",
        },
        {
            "drive_id": "⛰⛱⛲⛳⛵",
            "file_path": "test.txt",
        },
        {
            "drive_id": SCRIPT_LIKE_VALUE,
            "file_path": "test.txt",
        },
        {
            "vault_id": "$$#@$#$@#",
            "file_path": "test.txt",
        },
        {
            "vault_id": SCRIPT_LIKE_VALUE,
            "file_path": "test.txt",
        },
        {
            "file_path": "invalid|file.txt",
        },
        {
            "file_path": "invalid*file.txt",
        },
    ],
)
def test_upload_file_live_fails_for_invalid_inputs(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    tmp_path: Path,
    parameter_overrides: dict[str, str],
) -> None:
    action_input = build_soar_action_input(action="upload_file")
    vault_id = create_vault_file(
        connector_app,
        tmp_path,
        action_input["container_id"],
    )
    parameters = {
        "drive_id": "",
        "vault_id": vault_id,
        "file_path": "test.txt",
        "auto_rename": True,
    }
    parameters.update(parameter_overrides)

    result = run_upload_file_action(connector_app, build_soar_action_input, parameters)
    assert result.get_status() is False
