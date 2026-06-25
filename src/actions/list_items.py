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


AUTHORIZATION_REQUIRED_MESSAGE = (
    "Token not available. Please run Test Connectivity first."
)
GRAPH_VALUE_FIELD = "value"
GRAPH_NEXT_LINK_FIELD = "@odata.nextLink"
ITEM_ID_FIELD = "id"
ITEM_FILE_FIELD = "file"
PARENT_REFERENCE_FIELD = "parentReference"
PARENT_PATH_FIELD = "path"
PARENT_DRIVE_PATH_FIELD = "drivePath"
PARENT_FOLDER_PATH_FIELD = "folderPath"
ROOT_PATH_SPLIT = "root:/"
LIST_ITEMS_DEFAULT_ENDPOINT = "/me/drive/root/children"
LIST_ITEMS_DRIVE_ID_ENDPOINT = "/me/drives/{drive_id}/root/children"
LIST_ITEMS_DRIVE_FOLDER_ID_ENDPOINT = "/me/drives/{drive_id}/items/{folder_id}/children"
LIST_ITEMS_DRIVE_FOLDER_PATH_ENDPOINT = (
    "/me/drives/{drive_id}/root:/{folder_path}:/children"
)
LIST_ITEMS_FOLDER_ID_ENDPOINT = "/me/drive/items/{folder_id}/children"
LIST_ITEMS_FOLDER_PATH_ENDPOINT = "/me/drive/root:/{folder_path}:/children"
LIST_ITEMS_APPLICATION_DEFAULT_ENDPOINT = "/users/{target_user_id}/drive/root/children"
LIST_ITEMS_APPLICATION_DRIVE_ID_ENDPOINT = "/drives/{drive_id}/root/children"
LIST_ITEMS_APPLICATION_DRIVE_FOLDER_ID_ENDPOINT = (
    "/drives/{drive_id}/items/{folder_id}/children"
)
LIST_ITEMS_APPLICATION_DRIVE_FOLDER_PATH_ENDPOINT = (
    "/drives/{drive_id}/root:/{folder_path}:/children"
)
LIST_ITEMS_APPLICATION_FOLDER_ID_ENDPOINT = (
    "/users/{target_user_id}/drive/items/{folder_id}/children"
)
LIST_ITEMS_APPLICATION_FOLDER_PATH_ENDPOINT = (
    "/users/{target_user_id}/drive/root:/{folder_path}:/children"
)
TARGET_USER_ID_REQUIRED_MESSAGE = (
    "Target User ID is required for Client Credentials authentication"
)


class ListItemsParams(Params):
    drive_id: str | None = Param(
        description="Parent drive ID", primary=True, cef_types=["msonedrive drive id"]
    )
    folder_id: str | None = Param(
        description="Parent folder ID", primary=True, cef_types=["msonedrive folder id"]
    )
    folder_path: str | None = Param(
        description="Parent folder path",
        primary=True,
        cef_types=["msonedrive folder path"],
    )


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


class CurrentuserroleOutput(ActionOutput):
    blocksDownload: bool | None
    readOnly: bool | None


class HashesOutput(ActionOutput):
    quickXorHash: str = OutputField(example_values=["fio2VWDQgVGaX34LXedeos6Y6/s="])


class FileOutput(ActionOutput):
    hashes: HashesOutput | None
    mimeType: str = OutputField(example_values=["image/png"])


class FilesysteminfoOutput(ActionOutput):
    createdDateTime: str = OutputField(example_values=["2018-09-01T09:21:24Z"])
    lastModifiedDateTime: str = OutputField(example_values=["2018-09-01T09:21:24Z"])


class FolderOutput(ActionOutput):
    childCount: float = OutputField(example_values=[17])


class ImageOutput(ActionOutput):
    height: float = OutputField(example_values=[183])
    width: float = OutputField(example_values=[275])


class LastmodifiedbyOutput(ActionOutput):
    application: ApplicationOutput | None
    user: UserOutput | None


class PackageOutput(ActionOutput):
    type: str = OutputField(example_values=["oneNote"])


class ParentreferenceOutput(ActionOutput):
    driveId: str = OutputField(
        cef_types=["msonedrive drive id"],
        example_values=["example-drive-id"],
    )
    drivePath: str = OutputField(example_values=["/drive/root:/"])
    driveType: str = OutputField(example_values=["business"])
    folderPath: str = OutputField(
        cef_types=["msonedrive folder path"], example_values=["Test/child"]
    )
    id: str = OutputField(
        cef_types=["msonedrive drive id", "msonedrive folder id"],
        example_values=["example-parent-reference-id"],
    )


class ListItemsOutput(PermissiveActionOutput):
    microsoft_graph_download_url: str = OutputField(
        alias="@microsoft.graph.downloadUrl",
        cef_types=["url"],
        example_values=[
            "https://test-my.abc.com/test/test_xyz_com/_layouts/00/download.aspx?UniqueId=test&ApiVersion=2.0"
        ],
    )
    cTag: str = OutputField(
        example_values=['"c:{2test123-1234-1234-1234-test123test1},0"']
    )
    createdBy: CreatedbyOutput | None
    createdDateTime: str = OutputField(example_values=["2018-09-01T09:21:24Z"])
    currentUserRole: CurrentuserroleOutput | None
    eTag: str = OutputField(
        example_values=['"{2test123-1234-1234-1234-test123test1},1"']
    )
    file: FileOutput | None
    fileSystemInfo: FilesysteminfoOutput | None
    folder: FolderOutput | None
    id: str = OutputField(
        cef_types=["msonedrive file id", "msonedrive folder id"],
        example_values=["01TEST123TEST123TEST123U3KTTEST123"],
    )
    image: ImageOutput | None
    lastModifiedBy: LastmodifiedbyOutput | None
    lastModifiedDateTime: str = OutputField(example_values=["2018-09-01T10:37:09Z"])
    name: str = OutputField(example_values=["test file"])
    package: PackageOutput | None
    parentReference: ParentreferenceOutput | None
    size: float = OutputField(cef_types=["file size"], example_values=[359666])
    webUrl: str = OutputField(
        cef_types=["url"],
        example_values=[
            "https://test-my.test.com/personal/test_abc_com/Documents/Test"
        ],
    )


class ListItemsSummary(ActionOutput):
    total_items: int


def _get_target_user_id(asset: Asset) -> str:
    target_user_id = (asset.target_user_id or "").strip()
    if not target_user_id:
        raise ActionFailure(TARGET_USER_ID_REQUIRED_MESSAGE)

    return target_user_id


def _get_delegated_list_items_endpoint(params: ListItemsParams) -> str:
    drive_id: str = params.drive_id or ""
    folder_id: str = params.folder_id or ""
    folder_path: str = (params.folder_path or "").strip("/\\")

    if drive_id:
        if folder_id:
            return LIST_ITEMS_DRIVE_FOLDER_ID_ENDPOINT.format(
                drive_id=drive_id,
                folder_id=folder_id,
            )
        if folder_path:
            return LIST_ITEMS_DRIVE_FOLDER_PATH_ENDPOINT.format(
                drive_id=drive_id,
                folder_path=folder_path,
            )
        return LIST_ITEMS_DRIVE_ID_ENDPOINT.format(drive_id=drive_id)

    if folder_id:
        return LIST_ITEMS_FOLDER_ID_ENDPOINT.format(folder_id=folder_id)
    if folder_path:
        return LIST_ITEMS_FOLDER_PATH_ENDPOINT.format(folder_path=folder_path)
    return LIST_ITEMS_DEFAULT_ENDPOINT


def _get_client_credentials_list_items_endpoint(
    params: ListItemsParams, asset: Asset
) -> str:
    drive_id: str = params.drive_id or ""
    folder_id: str = params.folder_id or ""
    folder_path: str = (params.folder_path or "").strip("/\\")

    if drive_id:
        if folder_id:
            return LIST_ITEMS_APPLICATION_DRIVE_FOLDER_ID_ENDPOINT.format(
                drive_id=drive_id,
                folder_id=folder_id,
            )
        if folder_path:
            return LIST_ITEMS_APPLICATION_DRIVE_FOLDER_PATH_ENDPOINT.format(
                drive_id=drive_id,
                folder_path=folder_path,
            )
        return LIST_ITEMS_APPLICATION_DRIVE_ID_ENDPOINT.format(drive_id=drive_id)

    target_user_id = _get_target_user_id(asset)
    if folder_id:
        return LIST_ITEMS_APPLICATION_FOLDER_ID_ENDPOINT.format(
            target_user_id=target_user_id,
            folder_id=folder_id,
        )
    if folder_path:
        return LIST_ITEMS_APPLICATION_FOLDER_PATH_ENDPOINT.format(
            target_user_id=target_user_id,
            folder_path=folder_path,
        )
    return LIST_ITEMS_APPLICATION_DEFAULT_ENDPOINT.format(target_user_id=target_user_id)


def _get_list_items_endpoint(params: ListItemsParams, asset: Asset) -> str:
    if is_client_credentials_auth(asset):
        return _get_client_credentials_list_items_endpoint(params, asset)

    return _get_delegated_list_items_endpoint(params)


def _get_list_response(graph_client: Any, endpoint: str) -> list[dict[str, Any]]:
    """Return every item from a paginated Microsoft Graph list response.

    Microsoft Graph paginates list responses by returning a page of items in
    "value" and, when more pages exist, an "@odata.nextLink" URL for the next
    page. This follows that next-link chain until Graph stops returning one.
    """
    items: list[dict[str, Any]] = []
    next_endpoint: str | None = endpoint

    while next_endpoint:
        response = graph_client.get(next_endpoint)
        response.raise_for_status()
        response_json = response.json()
        items.extend(response_json.get(GRAPH_VALUE_FIELD, []))
        next_endpoint = response_json.get(GRAPH_NEXT_LINK_FIELD)

    return items


def _normalize_parent_reference(item: dict[str, Any]) -> None:
    parent_reference = item.get(PARENT_REFERENCE_FIELD)
    if not parent_reference:
        return

    full_path = parent_reference.get(PARENT_PATH_FIELD)
    if not full_path:
        return

    path_elements = full_path.split(ROOT_PATH_SPLIT)
    if len(path_elements) > 1:
        parent_reference[PARENT_DRIVE_PATH_FIELD] = (
            f"{path_elements[0]}{ROOT_PATH_SPLIT}"
        )
        parent_reference[PARENT_FOLDER_PATH_FIELD] = path_elements[1].strip("/\\")
    else:
        parent_reference[PARENT_DRIVE_PATH_FIELD] = path_elements[0]
        parent_reference[PARENT_FOLDER_PATH_FIELD] = ""
    parent_reference.pop(PARENT_PATH_FIELD, None)


def list_items(
    params: ListItemsParams, soar: SOARClient, asset: Asset
) -> list[ListItemsOutput]:
    logging.info("In action handler for: list_items")
    client_credentials_auth = is_client_credentials_auth(asset)
    endpoint = _get_list_items_endpoint(params, asset)
    logging.info(f"Using Microsoft Graph list items endpoint: {endpoint}")

    try:
        with get_graph_client(asset, str(soar.get_asset_id())) as graph_client:
            items: list[dict[str, Any]] = []
            pending_endpoints: list[str] = [endpoint]
            target_user_id = (
                _get_target_user_id(asset) if client_credentials_auth else ""
            )

            while pending_endpoints:
                current_endpoint: str = pending_endpoints.pop()
                children: list[dict[str, Any]] = _get_list_response(
                    graph_client, current_endpoint
                )

                for child in children:
                    items.append(child)
                    if not child.get(ITEM_FILE_FIELD):
                        child_id: str | None = child.get(ITEM_ID_FIELD)
                        if params.drive_id:
                            folder_endpoint = (
                                LIST_ITEMS_APPLICATION_DRIVE_FOLDER_ID_ENDPOINT
                                if client_credentials_auth
                                else LIST_ITEMS_DRIVE_FOLDER_ID_ENDPOINT
                            )
                            pending_endpoint = folder_endpoint.format(
                                drive_id=params.drive_id,
                                folder_id=child_id,
                            )
                        elif client_credentials_auth:
                            pending_endpoint = (
                                LIST_ITEMS_APPLICATION_FOLDER_ID_ENDPOINT.format(
                                    target_user_id=target_user_id,
                                    folder_id=child_id,
                                )
                            )
                        else:
                            pending_endpoint = LIST_ITEMS_FOLDER_ID_ENDPOINT.format(
                                folder_id=child_id
                            )
                        pending_endpoints.append(pending_endpoint)

    except OAuthClientError as e:
        raise ActionFailure(AUTHORIZATION_REQUIRED_MESSAGE) from e

    for item in items:
        _normalize_parent_reference(item)

    soar.set_summary(ListItemsSummary(total_items=len(items)))
    return [ListItemsOutput(**item) for item in items]
