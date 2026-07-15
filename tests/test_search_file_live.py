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
import time
import urllib.parse
import uuid
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from soar_sdk.app import App

from src.consts import AUTH_METHOD_CLIENT_CREDENTIALS


SEARCH_INDEX_TIMEOUT_SECONDS = 90.0
SEARCH_INDEX_POLL_SECONDS = 2.0
SEARCH_FILE_CONTENT = b"search file live test\n"


def create_graph_folder(
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
) -> dict[str, Any]:
    target_user_id = live_asset_config["target_user_id"]
    folder_name = f"sdkfied-search-file-{uuid.uuid4().hex}"
    response = microsoft_graph_client.post(
        f"/users/{target_user_id}/drive/root/children",
        json={
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail",
        },
    )
    response.raise_for_status()
    return response.json()


def create_graph_file(
    microsoft_graph_client: httpx.Client,
    folder: dict[str, Any],
) -> dict[str, Any]:
    drive_id = folder["parentReference"]["driveId"]
    folder_id = folder["id"]
    file_name = f"search-target-{uuid.uuid4().hex}.txt"
    response = microsoft_graph_client.put(
        f"/drives/{drive_id}/items/{folder_id}:/{file_name}:/content",
        content=SEARCH_FILE_CONTENT,
    )
    response.raise_for_status()
    return response.json()


def delete_graph_folder_if_exists(
    microsoft_graph_client: httpx.Client,
    drive_id: str,
    folder_id: str | None,
) -> None:
    if not folder_id:
        return

    response = microsoft_graph_client.delete(f"/drives/{drive_id}/items/{folder_id}")
    if response.status_code != httpx.codes.NOT_FOUND:
        response.raise_for_status()


def wait_for_graph_search_index(
    microsoft_graph_client: httpx.Client,
    drive_id: str,
    file_name: str,
    file_id: str,
) -> None:
    encoded_query = urllib.parse.quote(file_name, safe="")
    endpoint = f"/drives/{drive_id}/root/search(q='{encoded_query}')"
    deadline = time.monotonic() + SEARCH_INDEX_TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        response = microsoft_graph_client.get(
            endpoint,
            params={"$select": "id,name"},
        )
        if response.is_error:
            error = response.json().get("error", {})
            pytest.fail(
                "Microsoft Graph search failed with "
                f"{error.get('code', response.status_code)}: "
                f"{error.get('message', response.reason_phrase)}"
            )
        if any(item.get("id") == file_id for item in response.json().get("value", [])):
            return
        time.sleep(SEARCH_INDEX_POLL_SECONDS)

    pytest.fail(
        f"Microsoft Graph did not index {file_name!r} within "
        f"{SEARCH_INDEX_TIMEOUT_SECONDS:.0f} seconds"
    )


def run_search_file_action(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    parameters: dict[str, Any],
) -> Any:
    input_data = build_soar_action_input(
        action="search_file",
        asset_config={"auth_method": AUTH_METHOD_CLIENT_CREDENTIALS},
        parameters=[parameters],
    )

    connector_app.handle(json.dumps(input_data))
    return connector_app.actions_manager.get_action_results()[-1]


def test_search_file_live_finds_file_by_supported_scope(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    microsoft_graph_client: httpx.Client,
    live_asset_config: dict[str, str],
) -> None:
    folder = create_graph_folder(microsoft_graph_client, live_asset_config)
    folder_id = folder["id"]
    drive_id = folder["parentReference"]["driveId"]

    try:
        graph_file = create_graph_file(microsoft_graph_client, folder)
        file_id = graph_file["id"]
        file_name = graph_file["name"]
        wait_for_graph_search_index(
            microsoft_graph_client,
            drive_id,
            file_name,
            file_id,
        )
        for use_drive_id, use_folder_id in (
            (True, False),
            (True, True),
            (False, False),
            (False, True),
        ):
            result = run_search_file_action(
                connector_app,
                build_soar_action_input,
                {
                    "search_text": file_name,
                    "drive_id": drive_id if use_drive_id else "",
                    "folder_id": folder_id if use_folder_id else "",
                    "max_results": 10,
                },
            )

            assert result.get_status() is True, result.get_message()
            matching_items = [
                item for item in result.get_data() if item.get("id") == file_id
            ]
            assert len(matching_items) == 1
            assert matching_items[0]["name"] == file_name
            assert matching_items[0]["drive_id"] == drive_id
            assert matching_items[0]["is_folder"] is False
            assert result.get_summary()["total_items_found"] >= 1
    finally:
        delete_graph_folder_if_exists(
            microsoft_graph_client,
            drive_id,
            folder_id,
        )
