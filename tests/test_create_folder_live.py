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
from soar_sdk.app import App

from src.consts import AUTH_METHOD_CLIENT_CREDENTIALS


def test_create_folder_live_creates_folder_in_target_user_root(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
) -> None:
    target_user_id = live_asset_config["target_user_id"]
    folder_name = f"sdkfied-create-folder-{uuid.uuid4().hex}"
    created_folder_id: str | None = None

    input_data = build_soar_action_input(
        action="create_folder",
        asset_config={
            "auth_method": AUTH_METHOD_CLIENT_CREDENTIALS,
        },
        parameters=[
            {
                "drive_id": "",
                "folder_id": "",
                "folder_path": "",
                "folder_name": folder_name,
                "auto_rename": False,
            }
        ],
    )

    try:
        connector_app.handle(json.dumps(input_data))

        result = connector_app.actions_manager.get_action_results()[-1]
        assert result.get_status() is True, result.get_message()
        assert result.get_message() == (
            f"The folder: {folder_name} is created successfully"
        )

        created_folder = result.get_data()[0]
        created_folder_id = created_folder["id"]
        assert created_folder["name"] == folder_name
        assert "folder" in created_folder
        assert created_folder["parentReference"]["driveId"]

        graph_response = microsoft_graph_client.get(
            f"/users/{target_user_id}/drive/items/{created_folder_id}"
        )
        graph_response.raise_for_status()
        graph_folder = graph_response.json()

        assert graph_folder["id"] == created_folder_id
        assert graph_folder["name"] == folder_name
        assert graph_folder["folder"]["childCount"] == 0
        assert (
            graph_folder["parentReference"]["driveId"]
            == (created_folder["parentReference"]["driveId"])
        )
    finally:
        if created_folder_id:
            delete_response = microsoft_graph_client.delete(
                f"/users/{target_user_id}/drive/items/{created_folder_id}"
            )
            delete_response.raise_for_status()
