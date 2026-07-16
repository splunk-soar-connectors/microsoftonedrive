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
from types import SimpleNamespace

import pytest
from soar_sdk.exceptions import ActionFailure

from src.actions.search_file import (
    SearchFileOutput,
    SearchFileParams,
    _get_max_results,
    _get_search_endpoint,
)
from src.app import app
from src.consts import AUTH_METHOD_CLIENT_CREDENTIALS, AUTH_METHOD_DELEGATED


def _asset(
    *,
    auth_method: str = AUTH_METHOD_DELEGATED,
    target_user_id: str | None = "target@example.com",
) -> SimpleNamespace:
    return SimpleNamespace(auth_method=auth_method, target_user_id=target_user_id)


def test_search_file_registers_table_action() -> None:
    action = app.actions_manager.get_action("search_file")

    assert action.meta.render_as == "table"
    assert action.meta.summary_type is not None


@pytest.mark.parametrize(
    ("params", "asset", "expected_endpoint"),
    [
        (
            SearchFileParams(search_text="Quarterly Report"),
            _asset(),
            "/me/drive/root/search(q='Quarterly%20Report')",
        ),
        (
            SearchFileParams(search_text="Project", folder_id="folder-id"),
            _asset(),
            "/me/drive/items/folder-id/search(q='Project')",
        ),
        (
            SearchFileParams(search_text="Project", drive_id="drive-id"),
            _asset(),
            "/drives/drive-id/root/search(q='Project')",
        ),
        (
            SearchFileParams(
                search_text="Bob's Report",
                drive_id="drive-id",
                folder_id="folder-id",
            ),
            _asset(),
            "/drives/drive-id/items/folder-id/search(q='Bob%27%27s%20Report')",
        ),
        (
            SearchFileParams(search_text="Project", drive_id="drive-id"),
            _asset(auth_method=AUTH_METHOD_CLIENT_CREDENTIALS),
            "/drives/drive-id/root/search(q='Project')",
        ),
    ],
)
def test_get_search_endpoint_uses_existing_identity_contract(
    params: SearchFileParams,
    asset: SimpleNamespace,
    expected_endpoint: str,
) -> None:
    assert _get_search_endpoint(params, asset) == expected_endpoint


def test_get_search_endpoint_requires_target_user_for_client_credentials() -> None:
    params = SearchFileParams(search_text="Project")
    asset = _asset(auth_method=AUTH_METHOD_CLIENT_CREDENTIALS, target_user_id="")

    with pytest.raises(ActionFailure, match="Target User ID is required"):
        _get_search_endpoint(params, asset)


@pytest.mark.parametrize("max_results", [0, -1])
def test_search_file_rejects_invalid_max_results(max_results: int) -> None:
    with pytest.raises(ActionFailure, match="Max Results must be greater than zero"):
        _get_max_results(
            SearchFileParams(search_text="Quarterly", max_results=max_results)
        )


def test_search_file_caps_max_results() -> None:
    assert (
        _get_max_results(SearchFileParams(search_text="Quarterly", max_results=500))
        == 200
    )


def test_search_file_output_accepts_sparse_graph_result() -> None:
    output = SearchFileOutput(
        **{
            "id": "folder-id",
            "name": "Reports",
            "folder": {},
            "parentReference": {"driveId": "drive-id"},
            "is_folder": True,
            "search_text": "Reports",
            "drive_id": "drive-id",
        }
    )

    assert output.id == "folder-id"
    assert output.folder.childCount is None
    assert output.parentReference.driveId == "drive-id"
