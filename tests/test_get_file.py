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
from unittest.mock import patch

import pytest
from soar_sdk.exceptions import ActionFailure

from src.actions.get_file import (
    GetFileParams,
    _download_file_to_tmp,
    _get_file_content_endpoint,
    _validate_download_url,
)
from src.consts import AUTH_METHOD_CLIENT_CREDENTIALS, AUTH_METHOD_DELEGATED


def _asset(
    *,
    auth_method: str = AUTH_METHOD_DELEGATED,
    target_user_id: str | None = "target@example.com",
) -> SimpleNamespace:
    return SimpleNamespace(auth_method=auth_method, target_user_id=target_user_id)


@pytest.mark.parametrize(
    ("params", "asset", "expected_endpoint"),
    [
        (
            GetFileParams(file_id="file-id"),
            _asset(),
            "/me/drive/items/file-id/content",
        ),
        (
            GetFileParams(file_path="Reports/file.txt"),
            _asset(),
            "/me/drive/root:/Reports/file.txt:/content",
        ),
        (
            GetFileParams(file_id="file-id", drive_id="drive-id"),
            _asset(),
            "/drives/drive-id/items/file-id/content",
        ),
        (
            GetFileParams(file_path="/Reports/file.txt", drive_id="drive-id"),
            _asset(),
            "/drives/drive-id/root:/Reports/file.txt:/content",
        ),
        (
            GetFileParams(file_id="file-id"),
            _asset(auth_method=AUTH_METHOD_CLIENT_CREDENTIALS),
            "/users/target@example.com/drive/items/file-id/content",
        ),
        (
            GetFileParams(file_path="Reports/file.txt"),
            _asset(auth_method=AUTH_METHOD_CLIENT_CREDENTIALS),
            "/users/target@example.com/drive/root:/Reports/file.txt:/content",
        ),
        (
            GetFileParams(file_id="file-id", drive_id="drive-id"),
            _asset(auth_method=AUTH_METHOD_CLIENT_CREDENTIALS),
            "/drives/drive-id/items/file-id/content",
        ),
    ],
)
def test_get_file_content_endpoint_preserves_identity_contract(
    params: GetFileParams,
    asset: SimpleNamespace,
    expected_endpoint: str,
) -> None:
    assert _get_file_content_endpoint(params, asset) == expected_endpoint


def test_get_file_content_endpoint_requires_file_id_or_path() -> None:
    with pytest.raises(ActionFailure, match="Either File ID or File Path"):
        _get_file_content_endpoint(GetFileParams(), _asset())


def test_get_file_content_endpoint_requires_target_user_for_client_credentials() -> (
    None
):
    params = GetFileParams(file_id="file-id")
    asset = _asset(auth_method=AUTH_METHOD_CLIENT_CREDENTIALS, target_user_id="")

    with pytest.raises(ActionFailure, match="Target User ID is required"):
        _get_file_content_endpoint(params, asset)


def test_get_file_content_endpoint_encodes_untrusted_path_components() -> None:
    params = GetFileParams(file_id="file/id?select=secret", drive_id="drive/id")

    assert _get_file_content_endpoint(params, _asset()) == (
        "/drives/drive%2Fid/items/file%2Fid%3Fselect%3Dsecret/content"
    )


def test_get_file_content_endpoint_rejects_dot_segments() -> None:
    with pytest.raises(ActionFailure, match="dot segments"):
        _get_file_content_endpoint(GetFileParams(file_path="../secret.txt"), _asset())


@pytest.mark.parametrize(
    "url",
    [
        "http://download.example/file",
        "https://user:password@download.example/file",
        "https://download.example:8443/file",
        "https://download.example/file#fragment",
        "not-a-url",
    ],
)
def test_validate_download_url_rejects_unsafe_structure(url: str) -> None:
    with pytest.raises(ActionFailure, match="unsafe file download URL"):
        _validate_download_url(url)


@pytest.mark.parametrize(
    "address", ["127.0.0.1", "10.0.0.1", "169.254.1.1", "::1", "fc00::1"]
)
def test_validate_download_url_rejects_non_global_addresses(address: str) -> None:
    answers = [(None, None, None, None, (address, 443))]

    with (
        patch("src.actions.get_file.socket.getaddrinfo", return_value=answers),
        pytest.raises(ActionFailure, match="unsafe file download URL"),
    ):
        _validate_download_url("https://download.example/file")


def test_validate_download_url_accepts_only_global_answers() -> None:
    answers = [
        (None, None, None, None, ("8.8.8.8", 443)),
        (None, None, None, None, ("2606:4700:4700::1111", 443, 0, 0)),
    ]

    with patch("src.actions.get_file.socket.getaddrinfo", return_value=answers):
        _validate_download_url("https://download.example/file")


def test_download_validates_before_creating_temporary_file(tmp_path) -> None:
    with (
        patch("src.actions.get_file.NamedTemporaryFile") as temporary_file,
        pytest.raises(ActionFailure, match="unsafe file download URL"),
    ):
        _download_file_to_tmp("http://127.0.0.1/secret", tmp_path)

    temporary_file.assert_not_called()
