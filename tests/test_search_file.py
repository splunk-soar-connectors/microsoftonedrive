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
    MAX_FILENAME_SCAN_REQUESTS,
    SearchFileOutput,
    SearchFileParams,
    _get_filename_search_response,
    _get_max_results,
    _get_search_message,
    _get_search_endpoint,
    _is_filename_fallback_enabled,
    _normalize_search_result,
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


def test_filename_fallback_defaults_to_disabled() -> None:
    params = SearchFileParams(search_text="Quarterly")

    assert (
        _is_filename_fallback_enabled(
            params,
            _asset(auth_method=AUTH_METHOD_CLIENT_CREDENTIALS),
        )
        is False
    )


def test_search_file_exposes_optional_filename_fallback() -> None:
    action = app.actions_manager.get_action("search_file")
    fallback_schema = action.meta.parameters._to_json_schema()[
        "fallback_to_filename_scan"
    ]

    assert fallback_schema["required"] is False
    assert fallback_schema["default"] is False


@pytest.mark.parametrize(
    ("auth_method", "fallback_to_filename_scan", "expected"),
    [
        (AUTH_METHOD_CLIENT_CREDENTIALS, False, False),
        (AUTH_METHOD_CLIENT_CREDENTIALS, True, True),
        (AUTH_METHOD_DELEGATED, True, False),
    ],
)
def test_filename_fallback_requires_explicit_client_credentials_opt_in(
    auth_method: str,
    fallback_to_filename_scan: bool,
    expected: bool,
) -> None:
    params = SearchFileParams(
        search_text="Quarterly",
        fallback_to_filename_scan=fallback_to_filename_scan,
    )

    assert (
        _is_filename_fallback_enabled(params, _asset(auth_method=auth_method))
        is expected
    )


def test_filename_scan_stops_when_request_budget_is_exhausted() -> None:
    filename_scan = _get_filename_search_response(
        None,
        "drive-id",
        None,
        "Quarterly",
        max_results=10,
        max_requests=0,
    )

    assert filename_scan.items == []
    assert filename_scan.request_limit_reached is True


def test_filename_scan_limit_is_reported_as_incomplete() -> None:
    message = _get_search_message(
        2,
        filename_fallback_used=True,
        filename_scan_incomplete=True,
    )

    assert f"limit of {MAX_FILENAME_SCAN_REQUESTS} Microsoft Graph requests" in message
    assert "results may be incomplete" in message


def test_search_file_output_accepts_sparse_graph_result() -> None:
    output = SearchFileOutput(
        **{
            "id": "folder-id",
            "name": "Reports",
            "folder": {},
            "parentReference": {"driveId": "drive-id"},
            "is_folder": True,
            "drive_id": "drive-id",
        }
    )

    assert output.id == "folder-id"
    assert output.folder.childCount is None
    assert output.parentReference.driveId == "drive-id"


def test_search_scope_parameters_are_not_duplicated_in_output_data() -> None:
    params = SearchFileParams(
        search_text="Reports",
        folder_id="folder-id",
        drive_id="requested-drive-id",
    )
    item = {"parentReference": {"driveId": "resolved-drive-id"}}

    _normalize_search_result(item, params)

    assert "search_text" in SearchFileParams.model_fields
    assert "folder_id" in SearchFileParams.model_fields
    assert "search_text" not in SearchFileOutput.model_fields
    assert "folder_id" not in SearchFileOutput.model_fields
    assert item == {
        "parentReference": {"driveId": "resolved-drive-id"},
        "drive_id": "resolved-drive-id",
        "is_folder": False,
    }
