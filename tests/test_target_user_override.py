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
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

import pytest
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Params

from src.actions.create_folder import (
    CreateFolderParams,
    _get_create_folder_endpoint,
)
from src.actions.delete_file import DeleteFileParams, _get_delete_file_endpoint
from src.actions.delete_folder import DeleteFolderParams, _get_delete_folder_endpoint
from src.actions.get_file import GetFileParams, _get_file_content_endpoint
from src.actions.list_drive import ListDriveParams, _get_list_drives_endpoint
from src.actions.list_items import (
    ListItemsParams,
    _get_list_items_child_endpoint,
    _get_list_items_endpoint,
)
from src.actions.search_file import SearchFileParams, _get_search_endpoint
from src.actions.target_user import resolve_target_user_id
from src.actions.upload_file import UploadFileParams, _get_upload_session_endpoint
from src.app import app
from src.consts import AUTH_METHOD_CLIENT_CREDENTIALS, AUTH_METHOD_DELEGATED


EndpointBuilder = Callable[[Any, SimpleNamespace], str]


def _asset(
    *,
    auth_method: str = AUTH_METHOD_CLIENT_CREDENTIALS,
    target_user_id: str | None = "asset@example.com",
) -> SimpleNamespace:
    return SimpleNamespace(auth_method=auth_method, target_user_id=target_user_id)


@pytest.mark.parametrize(
    ("action_target_user_id", "asset_target_user_id", "expected"),
    [
        (" action@example.com ", "asset@example.com", "action@example.com"),
        (None, " asset@example.com ", "asset@example.com"),
        ("", "asset@example.com", "asset@example.com"),
        ("   ", "asset@example.com", "asset@example.com"),
    ],
)
def test_resolve_target_user_id_uses_action_then_asset_precedence(
    action_target_user_id: str | None,
    asset_target_user_id: str | None,
    expected: str,
) -> None:
    assert (
        resolve_target_user_id(action_target_user_id, asset_target_user_id) == expected
    )


@pytest.mark.parametrize(
    ("action_target_user_id", "asset_target_user_id"),
    [(None, None), ("", ""), ("   ", "   ")],
)
def test_resolve_target_user_id_requires_action_or_asset_value(
    action_target_user_id: str | None,
    asset_target_user_id: str | None,
) -> None:
    with pytest.raises(ActionFailure, match="Target User ID is required"):
        resolve_target_user_id(action_target_user_id, asset_target_user_id)


@pytest.mark.parametrize(
    ("params", "endpoint_builder", "expected_endpoint"),
    [
        (
            CreateFolderParams(
                folder_name="Reports",
                target_user_id="action@example.com",
            ),
            _get_create_folder_endpoint,
            "/users/action@example.com/drive/root/children",
        ),
        (
            DeleteFileParams(
                file_id="file-id",
                target_user_id="action@example.com",
            ),
            _get_delete_file_endpoint,
            "/users/action@example.com/drive/items/file-id",
        ),
        (
            DeleteFolderParams(
                folder_id="folder-id",
                target_user_id="action@example.com",
            ),
            _get_delete_folder_endpoint,
            "/users/action@example.com/drive/items/folder-id",
        ),
        (
            GetFileParams(
                file_id="file-id",
                target_user_id="action@example.com",
            ),
            _get_file_content_endpoint,
            "/users/action@example.com/drive/items/file-id/content",
        ),
        (
            ListDriveParams(target_user_id="action@example.com"),
            _get_list_drives_endpoint,
            "/users/action@example.com/drives",
        ),
        (
            ListItemsParams(target_user_id="action@example.com"),
            _get_list_items_endpoint,
            "/users/action@example.com/drive/root/children",
        ),
        (
            UploadFileParams(
                vault_id="vault-id",
                file_path="report.txt",
                target_user_id="action@example.com",
            ),
            _get_upload_session_endpoint,
            "/users/action@example.com/drive/root:/report.txt:/createUploadSession",
        ),
    ],
)
def test_client_credentials_actions_override_asset_target_user(
    params: Params,
    endpoint_builder: EndpointBuilder,
    expected_endpoint: str,
) -> None:
    assert endpoint_builder(params, _asset()) == expected_endpoint


@pytest.mark.parametrize(
    ("params", "expected_endpoint"),
    [
        (
            CreateFolderParams(
                drive_id="drive-id",
                folder_name="Reports",
            ),
            "/drives/drive-id/root/children",
        ),
        (
            CreateFolderParams(
                drive_id="drive-id",
                folder_id="folder-id",
                folder_name="Reports",
            ),
            "/drives/drive-id/items/folder-id/children",
        ),
        (
            CreateFolderParams(
                drive_id="drive-id",
                folder_path="Parent Folder",
                folder_name="Reports",
            ),
            "/drives/drive-id/root:/Parent Folder:/children",
        ),
    ],
)
def test_create_folder_drive_scope_does_not_require_target_user(
    params: CreateFolderParams,
    expected_endpoint: str,
) -> None:
    assert (
        _get_create_folder_endpoint(params, _asset(target_user_id=None))
        == expected_endpoint
    )


def test_create_folder_user_scope_requires_target_user() -> None:
    params = CreateFolderParams(folder_name="Reports")

    with pytest.raises(ActionFailure, match="Target User ID is required"):
        _get_create_folder_endpoint(params, _asset(target_user_id=None))


@pytest.mark.parametrize(
    ("params", "asset", "expected_endpoint"),
    [
        (
            ListItemsParams(drive_id="drive-id"),
            _asset(target_user_id=None),
            "/drives/drive-id/items/folder-id/children",
        ),
        (
            ListItemsParams(drive_id="drive-id"),
            _asset(
                auth_method=AUTH_METHOD_DELEGATED,
                target_user_id=None,
            ),
            "/me/drives/drive-id/items/folder-id/children",
        ),
        (
            ListItemsParams(target_user_id="action@example.com"),
            _asset(),
            "/users/action@example.com/drive/items/folder-id/children",
        ),
        (
            ListItemsParams(target_user_id="action@example.com"),
            _asset(
                auth_method=AUTH_METHOD_DELEGATED,
                target_user_id=None,
            ),
            "/me/drive/items/folder-id/children",
        ),
    ],
)
def test_list_items_recursive_child_endpoint_uses_requested_scope(
    params: ListItemsParams,
    asset: SimpleNamespace,
    expected_endpoint: str,
) -> None:
    assert (
        _get_list_items_child_endpoint(
            params,
            asset,
            "folder-id",
        )
        == expected_endpoint
    )


@pytest.mark.parametrize(
    ("params", "endpoint_builder", "expected_endpoint"),
    [
        (
            CreateFolderParams(
                folder_name="Reports",
                target_user_id="action@example.com",
            ),
            _get_create_folder_endpoint,
            "/me/drive/root/children",
        ),
        (
            DeleteFileParams(
                file_id="file-id",
                target_user_id="action@example.com",
            ),
            _get_delete_file_endpoint,
            "/me/drive/items/file-id",
        ),
        (
            DeleteFolderParams(
                folder_id="folder-id",
                target_user_id="action@example.com",
            ),
            _get_delete_folder_endpoint,
            "/me/drive/items/folder-id",
        ),
        (
            GetFileParams(
                file_id="file-id",
                target_user_id="action@example.com",
            ),
            _get_file_content_endpoint,
            "/me/drive/items/file-id/content",
        ),
        (
            ListDriveParams(target_user_id="action@example.com"),
            _get_list_drives_endpoint,
            "/me/drives",
        ),
        (
            ListItemsParams(target_user_id="action@example.com"),
            _get_list_items_endpoint,
            "/me/drive/root/children",
        ),
        (
            SearchFileParams(
                search_text="Report",
                target_user_id="action@example.com",
            ),
            _get_search_endpoint,
            "/me/drive/root/search(q='Report')",
        ),
        (
            UploadFileParams(
                vault_id="vault-id",
                file_path="report.txt",
                target_user_id="action@example.com",
            ),
            _get_upload_session_endpoint,
            "/me/drive/root:/report.txt:/createUploadSession",
        ),
    ],
)
def test_delegated_actions_ignore_target_user_override(
    params: Params,
    endpoint_builder: EndpointBuilder,
    expected_endpoint: str,
) -> None:
    delegated_asset = _asset(
        auth_method=AUTH_METHOD_DELEGATED,
        target_user_id=None,
    )
    assert endpoint_builder(params, delegated_asset) == expected_endpoint


@pytest.mark.parametrize(
    "action_name",
    [
        "create_folder",
        "delete_file",
        "delete_folder",
        "get_file",
        "list_drive",
        "list_items",
        "search_file",
        "upload_file",
    ],
)
def test_user_routed_actions_expose_optional_target_user_id(action_name: str) -> None:
    action = app.actions_manager.get_action(action_name)
    target_user_schema = action.meta.parameters._to_json_schema()["target_user_id"]
    target_user_metadata = action.meta.parameters.model_fields[
        "target_user_id"
    ].json_schema_extra

    assert target_user_schema["required"] is False
    assert "overrides the asset Target User ID" in target_user_schema["description"]
    assert "column_name" not in target_user_metadata


def test_make_request_does_not_expose_target_user_override() -> None:
    action = app.actions_manager.get_action("make_request")

    assert "target_user_id" not in action.meta.parameters._to_json_schema()
