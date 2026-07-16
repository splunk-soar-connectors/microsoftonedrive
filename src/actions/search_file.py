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
import urllib.parse
from typing import Any

from soar_sdk import logging
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField, PermissiveActionOutput
from soar_sdk.auth.client import OAuthClientError
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Param, Params

from ..asset import Asset
from ..auth import is_client_credentials_auth
from ..graph import get_graph_client
from .target_user import resolve_target_user_id, target_user_id_param


AUTHORIZATION_REQUIRED_MESSAGE = (
    "Token not available. Please run Test Connectivity first."
)
GRAPH_VALUE_FIELD = "value"
GRAPH_NEXT_LINK_FIELD = "@odata.nextLink"
PARENT_REFERENCE_FIELD = "parentReference"
PARENT_DRIVE_ID_FIELD = "driveId"
FOLDER_FIELD = "folder"
DEFAULT_MAX_RESULTS = 100
MAX_RESULTS_LIMIT = 200
INVALID_MAX_RESULTS_MESSAGE = "Max Results must be greater than zero"
SEARCH_DELEGATED_DEFAULT_ENDPOINT = "/me/drive/root/search(q='{search_text}')"
SEARCH_DELEGATED_FOLDER_ID_ENDPOINT = (
    "/me/drive/items/{folder_id}/search(q='{search_text}')"
)
SEARCH_DRIVE_ID_ENDPOINT = "/drives/{drive_id}/root/search(q='{search_text}')"
SEARCH_DRIVE_FOLDER_ID_ENDPOINT = (
    "/drives/{drive_id}/items/{folder_id}/search(q='{search_text}')"
)
SEARCH_CLIENT_CREDENTIALS_DEFAULT_ENDPOINT = (
    "/users/{target_user_id}/drive/root/search(q='{search_text}')"
)
SEARCH_CLIENT_CREDENTIALS_FOLDER_ID_ENDPOINT = (
    "/users/{target_user_id}/drive/items/{folder_id}/search(q='{search_text}')"
)
SEARCH_SELECT_FIELDS = (
    "id,name,size,webUrl,createdDateTime,lastModifiedDateTime,file,folder,"
    "parentReference,createdBy,lastModifiedBy,@microsoft.graph.downloadUrl"
)


class SearchFileParams(Params):
    search_text: str = Param(
        description="Text to search for in file or folder names and content",
        required=True,
        primary=True,
        column_name="Search Text",
    )
    drive_id: str | None = Param(
        description="Drive ID",
        primary=True,
        cef_types=["msonedrive drive id"],
        column_name="Drive ID",
    )
    folder_id: str | None = Param(
        description="Folder ID to limit search scope",
        primary=True,
        cef_types=["msonedrive folder id"],
        column_name="Folder ID",
    )
    max_results: int | None = Param(
        description="Maximum number of matching items to return, capped at 200",
        default=DEFAULT_MAX_RESULTS,
        column_name="Max Results",
    )
    target_user_id: str | None = target_user_id_param()


class ApplicationOutput(ActionOutput):
    displayName: str = OutputField(example_values=["Test_One-drive"])
    id: str = OutputField(example_values=["ba56002c-856c-469f-b6a0-a4335614c502"])


class UserOutput(ActionOutput):
    displayName: str = OutputField(
        cef_types=["user name"], example_values=["Test User"]
    )
    email: str = OutputField(cef_types=["email"], example_values=["test@test.xyz.com"])
    id: str = OutputField(example_values=["17be00d0-35ed-4881-ab62-d2eb73c2ebe3"])


class CreatedbyOutput(ActionOutput):
    application: ApplicationOutput | None
    user: UserOutput | None


class LastmodifiedbyOutput(ActionOutput):
    application: ApplicationOutput | None
    user: UserOutput | None


class HashesOutput(ActionOutput):
    quickXorHash: str = OutputField(example_values=["fio2VWDQgVGaX34LXedeos6Y6/s="])
    sha1Hash: str | None = OutputField(example_values=["example-sha1"])
    sha256Hash: str | None = OutputField(example_values=["example-sha256"])


class FileOutput(ActionOutput):
    hashes: HashesOutput | None
    mimeType: str = OutputField(example_values=["image/png"])


class FolderOutput(ActionOutput):
    childCount: float | None = OutputField(example_values=[17])


class ParentreferenceOutput(ActionOutput):
    driveId: str = OutputField(
        cef_types=["msonedrive drive id"],
        example_values=["example-drive-id"],
    )
    driveType: str = OutputField(example_values=["business"])
    id: str = OutputField(
        cef_types=["msonedrive drive id", "msonedrive folder id"],
        example_values=["example-parent-reference-id"],
    )
    path: str = OutputField(example_values=["/drive/root:/Test"])


class SearchFileOutput(PermissiveActionOutput):
    drive_id: str | None = OutputField(
        column_name="Drive ID",
        cef_types=["msonedrive drive id"],
        example_values=["example-drive-id"],
    )
    folder_id: str | None = OutputField(
        cef_types=["msonedrive folder id"],
        example_values=["example-folder-id"],
    )
    search_text: str = OutputField(example_values=["report"])
    is_folder: bool = OutputField(column_name="Is Folder", example_values=[False])
    microsoft_graph_download_url: str = OutputField(
        alias="@microsoft.graph.downloadUrl",
        cef_types=["url"],
        example_values=[
            "https://test-my.abc.com/test/test_xyz_com/_layouts/00/download.aspx?UniqueId=test&ApiVersion=2.0"
        ],
    )
    createdBy: CreatedbyOutput | None
    createdDateTime: str = OutputField(example_values=["2018-09-01T09:21:24Z"])
    file: FileOutput | None
    folder: FolderOutput | None
    id: str = OutputField(
        column_name="Item ID",
        cef_types=["msonedrive file id", "msonedrive folder id"],
        example_values=["01TEST123TEST123TEST123U3KTTEST123"],
    )
    lastModifiedBy: LastmodifiedbyOutput | None
    lastModifiedDateTime: str = OutputField(example_values=["2018-09-01T10:37:09Z"])
    name: str = OutputField(column_name="Name", example_values=["test file"])
    parentReference: ParentreferenceOutput | None
    size: float = OutputField(
        column_name="Size (Bytes)",
        cef_types=["file size"],
        example_values=[359666],
    )
    webUrl: str = OutputField(
        column_name="Web URL",
        cef_types=["url"],
        example_values=[
            "https://test-my.test.com/personal/test_abc_com/Documents/Test"
        ],
    )


class SearchFileSummary(ActionOutput):
    total_items_found: int = OutputField(example_values=[1])


def _encode_search_text(search_text: str) -> str:
    escaped_search_text = search_text.replace("'", "''")
    return urllib.parse.quote(escaped_search_text, safe="")


def _get_max_results(params: SearchFileParams) -> int:
    max_results = (
        params.max_results if params.max_results is not None else DEFAULT_MAX_RESULTS
    )
    if max_results <= 0:
        raise ActionFailure(INVALID_MAX_RESULTS_MESSAGE)
    return min(max_results, MAX_RESULTS_LIMIT)


def _get_delegated_search_endpoint(params: SearchFileParams) -> str:
    drive_id = params.drive_id or ""
    folder_id = params.folder_id or ""
    search_text = _encode_search_text(params.search_text)

    if drive_id:
        if folder_id:
            return SEARCH_DRIVE_FOLDER_ID_ENDPOINT.format(
                drive_id=drive_id,
                folder_id=folder_id,
                search_text=search_text,
            )
        return SEARCH_DRIVE_ID_ENDPOINT.format(
            drive_id=drive_id,
            search_text=search_text,
        )

    if folder_id:
        return SEARCH_DELEGATED_FOLDER_ID_ENDPOINT.format(
            folder_id=folder_id,
            search_text=search_text,
        )
    return SEARCH_DELEGATED_DEFAULT_ENDPOINT.format(search_text=search_text)


def _get_client_credentials_search_endpoint(
    params: SearchFileParams, asset: Asset
) -> str:
    drive_id = params.drive_id or ""
    folder_id = params.folder_id or ""
    search_text = _encode_search_text(params.search_text)

    if drive_id:
        if folder_id:
            return SEARCH_DRIVE_FOLDER_ID_ENDPOINT.format(
                drive_id=drive_id,
                folder_id=folder_id,
                search_text=search_text,
            )
        return SEARCH_DRIVE_ID_ENDPOINT.format(
            drive_id=drive_id,
            search_text=search_text,
        )

    target_user_id = resolve_target_user_id(
        params.target_user_id,
        asset.target_user_id,
    )
    if folder_id:
        return SEARCH_CLIENT_CREDENTIALS_FOLDER_ID_ENDPOINT.format(
            target_user_id=target_user_id,
            folder_id=folder_id,
            search_text=search_text,
        )
    return SEARCH_CLIENT_CREDENTIALS_DEFAULT_ENDPOINT.format(
        target_user_id=target_user_id,
        search_text=search_text,
    )


def _get_search_endpoint(params: SearchFileParams, asset: Asset) -> str:
    if is_client_credentials_auth(asset):
        return _get_client_credentials_search_endpoint(params, asset)

    return _get_delegated_search_endpoint(params)


def _get_search_response(
    graph_client: Any,
    endpoint: str,
    *,
    max_results: int,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    next_endpoint: str | None = endpoint
    query_params: dict[str, Any] | None = {
        "$select": SEARCH_SELECT_FIELDS,
        "$top": min(max_results, MAX_RESULTS_LIMIT),
    }

    while next_endpoint and len(items) < max_results:
        response = graph_client.get(next_endpoint, params=query_params)
        response.raise_for_status()
        response_json = response.json()
        remaining_count = max_results - len(items)
        items.extend(response_json.get(GRAPH_VALUE_FIELD, [])[:remaining_count])
        next_endpoint = response_json.get(GRAPH_NEXT_LINK_FIELD)
        query_params = None

    return items


def _normalize_search_result(
    item: dict[str, Any],
    params: SearchFileParams,
) -> None:
    parent_reference = item.get(PARENT_REFERENCE_FIELD) or {}
    item["drive_id"] = parent_reference.get(PARENT_DRIVE_ID_FIELD) or params.drive_id
    item["folder_id"] = params.folder_id
    item["search_text"] = params.search_text
    item["is_folder"] = FOLDER_FIELD in item


def search_file(
    params: SearchFileParams, soar: SOARClient, asset: Asset
) -> list[SearchFileOutput]:
    logging.info("In action handler for: search_file")
    max_results = _get_max_results(params)
    endpoint = _get_search_endpoint(params, asset)
    logging.info(f"Using Microsoft Graph search endpoint: {endpoint}")

    try:
        with get_graph_client(asset, str(soar.get_asset_id())) as graph_client:
            items = _get_search_response(
                graph_client,
                endpoint,
                max_results=max_results,
            )
    except OAuthClientError as e:
        raise ActionFailure(AUTHORIZATION_REQUIRED_MESSAGE) from e

    for item in items:
        _normalize_search_result(item, params)

    total_items_found = len(items)
    soar.set_summary(SearchFileSummary(total_items_found=total_items_found))
    soar.set_message(f"Total items found: {total_items_found}")
    return [SearchFileOutput(**item) for item in items]
