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
import pytest
from soar_sdk.app import App

from src.consts import AUTH_METHOD_CLIENT_CREDENTIALS


def run_make_request_action(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    parameters: dict[str, Any],
) -> Any:
    input_data = build_soar_action_input(
        action="make_request",
        asset_config={
            "auth_method": AUTH_METHOD_CLIENT_CREDENTIALS,
        },
        parameters=[parameters],
    )

    connector_app.handle(json.dumps(input_data))
    return connector_app.actions_manager.get_action_results()[-1]


def test_make_request_live_gets_target_user_drive_root(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    live_asset_config: dict[str, str],
) -> None:
    target_user_id = live_asset_config["target_user_id"]
    result = run_make_request_action(
        connector_app,
        build_soar_action_input,
        {
            "http_method": "GET",
            "endpoint": f"/v1.0/users/{target_user_id}/drive/root",
            "query_parameters": json.dumps({"$select": "id,name"}),
            "timeout": 30,
            "verify_ssl": True,
        },
    )

    assert result.get_status() is True, result.get_message()
    output = result.get_data()[0]
    assert output["status_code"] == 200
    response_body = json.loads(output["response_body"])
    assert response_body["id"]
    assert response_body["name"]


def test_make_request_live_gets_drive_root_by_drive_id(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    live_asset_config: dict[str, str],
    microsoft_graph_client: httpx.Client,
) -> None:
    target_user_id = live_asset_config["target_user_id"]
    drive_response = microsoft_graph_client.get(
        f"/users/{target_user_id}/drive",
        params={"$select": "id"},
    )
    drive_response.raise_for_status()
    drive_id = drive_response.json()["id"]

    result = run_make_request_action(
        connector_app,
        build_soar_action_input,
        {
            "http_method": "GET",
            "endpoint": f"/v1.0/drives/{drive_id}/root",
            "query_parameters": json.dumps({"$select": "id,name"}),
            "timeout": 30,
            "verify_ssl": True,
        },
    )

    assert result.get_status() is True, result.get_message()
    output = result.get_data()[0]
    assert output["status_code"] == 200
    response_body = json.loads(output["response_body"])
    assert response_body["id"]
    assert response_body["name"]


def test_make_request_live_returns_graph_error_response_as_data(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    live_asset_config: dict[str, str],
) -> None:
    target_user_id = live_asset_config["target_user_id"]
    result = run_make_request_action(
        connector_app,
        build_soar_action_input,
        {
            "http_method": "GET",
            "endpoint": f"/v1.0/users/{target_user_id}/drive/root:/missing-file.txt",
            "timeout": 30,
            "verify_ssl": True,
        },
    )

    assert result.get_status() is True, result.get_message()
    output = result.get_data()[0]
    assert output["status_code"] == 404
    response_body = json.loads(output["response_body"])
    assert response_body["error"]


@pytest.mark.parametrize(
    "parameters",
    [
        {
            "http_method": "GET",
            "endpoint": "https://graph.microsoft.com/v1.0/me/drive/root",
        },
        {
            "http_method": "GET",
            "endpoint": "/me/drive/root",
        },
        {
            "http_method": "GET",
            "endpoint": "/v1.0/me/drive/root",
            "headers": "{not-json}",
        },
        {
            "http_method": "POST",
            "endpoint": "/v1.0/me/drive/root",
            "body": "{not-json}",
        },
    ],
)
def test_make_request_live_fails_for_invalid_request_parameters(
    connector_app: App,
    build_soar_action_input: Callable[..., dict[str, Any]],
    parameters: dict[str, str],
) -> None:
    result = run_make_request_action(connector_app, build_soar_action_input, parameters)
    assert result.get_status() is False
