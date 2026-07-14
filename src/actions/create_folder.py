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
from collections.abc import Iterator
from typing import Any

from soar_sdk import logging
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import (
    ActionOutput,
    OutputField,
    OutputFieldSpecification,
)
from soar_sdk.auth.client import OAuthClientError
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Param, Params

from ..asset import Asset
from ..auth import is_client_credentials_auth
from ..graph import get_graph_client


AUTHORIZATION_REQUIRED_MESSAGE = (
    "Token not available. Please run Test Connectivity first."
)
TARGET_USER_ID_REQUIRED_MESSAGE = (
    "Target User ID is required for Client Credentials authentication"
)
CREATE_FOLDER_SUCCESS_MESSAGE = "The folder: {folder_name} is created successfully"
GRAPH_CONFLICT_BEHAVIOR_FIELD = "@microsoft.graph.conflictBehavior"
GRAPH_RENAME_VALUE = "rename"
ITEM_FOLDER_FIELD = "folder"
ITEM_NAME_FIELD = "name"
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
LIST_ITEMS_CLIENT_CREDENTIALS_DEFAULT_ENDPOINT = (
    "/users/{target_user_id}/drive/root/children"
)
LIST_ITEMS_CLIENT_CREDENTIALS_DRIVE_ID_ENDPOINT = "/drives/{drive_id}/root/children"
LIST_ITEMS_CLIENT_CREDENTIALS_DRIVE_FOLDER_ID_ENDPOINT = (
    "/drives/{drive_id}/items/{folder_id}/children"
)
LIST_ITEMS_CLIENT_CREDENTIALS_DRIVE_FOLDER_PATH_ENDPOINT = (
    "/drives/{drive_id}/root:/{folder_path}:/children"
)
LIST_ITEMS_CLIENT_CREDENTIALS_FOLDER_ID_ENDPOINT = (
    "/users/{target_user_id}/drive/items/{folder_id}/children"
)
LIST_ITEMS_CLIENT_CREDENTIALS_FOLDER_PATH_ENDPOINT = (
    "/users/{target_user_id}/drive/root:/{folder_path}:/children"
)


class CreateFolderParams(Params):
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
    folder_name: str = Param(
        description="Folder name", primary=True, cef_types=["msonedrive folder name"]
    )
    auto_rename: bool | None = Param(description="Auto rename folder", default=True)


class ApplicationOutput(ActionOutput):
    displayName: str | None = OutputField(example_values=["Test_One-drive"])
    id: str | None = OutputField(
        example_values=["ba56002c-856c-469f-b6a0-a4335614c502"]
    )


class CreatedByUserOutput(ActionOutput):
    displayName: str | None = OutputField(
        cef_types=["user name"], example_values=["Test User"]
    )
    email: str | None = OutputField(
        column_name="Created By",
        cef_types=["email"],
        example_values=["test@test.xyz.com"],
    )
    id: str | None = OutputField(
        example_values=["17be00d0-35ed-4881-ab62-d2eb73c2ebe3"]
    )


class LastModifiedByUserOutput(ActionOutput):
    displayName: str | None = OutputField(
        cef_types=["user name"], example_values=["Test User"]
    )
    email: str | None = OutputField(
        cef_types=["email"], example_values=["test@test.xyz.com"]
    )
    id: str | None = OutputField(
        example_values=["17be00d0-35ed-4881-ab62-d2eb73c2ebe3"]
    )


class CreatedbyOutput(ActionOutput):
    application: ApplicationOutput | None
    user: CreatedByUserOutput | None


class FilesysteminfoOutput(ActionOutput):
    createdDateTime: str | None = OutputField(example_values=["2018-09-01T08:49:18Z"])
    lastModifiedDateTime: str | None = OutputField(
        example_values=["2018-09-01T08:49:18Z"]
    )


class FolderOutput(ActionOutput):
    childCount: float | None = OutputField(example_values=[0])


class LastmodifiedbyOutput(ActionOutput):
    application: ApplicationOutput | None
    user: LastModifiedByUserOutput | None


class ParentreferenceOutput(ActionOutput):
    driveId: str | None = OutputField(
        column_name="Drive ID",
        cef_types=["msonedrive drive id"],
        example_values=[
            "b!gy8txu3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q"
        ],
    )
    drivePath: str | None = OutputField(
        example_values=[
            "/drives/b!test123_TESTzTEST123faTEST123LTEST-7TEST123-MTEST123RJQb3TEST123/root:/"
        ]
    )
    driveType: str | None = OutputField(example_values=["business"])
    folderPath: str | None = OutputField(
        column_name="Folder Path",
        cef_types=["msonedrive folder path"],
        example_values=["Test"],
    )
    id: str | None = OutputField(
        cef_types=["msonedrive drive id", "msonedrive folder id"],
        example_values=["01FMDUEQY3MRPCRFEYX5FJPU3KT7J24LJB"],
    )


class CreateFolderOutput(ActionOutput):
    parentReference: ParentreferenceOutput
    id: str = OutputField(
        column_name="Folder ID",
        cef_types=["msonedrive folder id"],
        example_values=["01TEST123TEST123TEST123U3KTTEST123"],
    )
    name: str = OutputField(
        column_name="Folder Name",
        cef_types=["msonedrive folder name"],
        example_values=["Test_1 1"],
    )
    webUrl: str | None = OutputField(
        column_name="Folder Web URL",
        cef_types=["url"],
        example_values=[
            "https://test-my.test.com/personal/test_xyz_com/Documents/Test/Test_1%201"
        ],
    )
    size: float | None = OutputField(
        column_name="Size (Bytes)", cef_types=["file size"], example_values=[0]
    )
    createdBy: CreatedbyOutput | None
    createdDateTime: str | None = OutputField(
        column_name="Created At",
        example_values=["2018-09-01T08:49:18Z"],
    )
    odata_context: str | None = OutputField(
        alias="@odata.context",
        cef_types=["url"],
        example_values=[
            "https://abc.test.com/v1.0/$metadata#users(01TEST123TEST123TEST123U3KTTEST123)/drive/items(01TEST123TEST123TEST123U3KTTEST123)/children/$entity"
        ],
    )
    cTag: str | None = OutputField(
        example_values=['"c:{2test123-1234-1234-1234-test123test1},0"']
    )
    eTag: str | None = OutputField(
        example_values=['"{2test123-1234-1234-1234-test123test1},1"']
    )
    fileSystemInfo: FilesysteminfoOutput | None
    folder: FolderOutput
    lastModifiedBy: LastmodifiedbyOutput | None
    lastModifiedDateTime: str | None = OutputField(
        example_values=["2018-09-01T08:49:18Z"]
    )

    @classmethod
    def _to_json_schema(
        cls,
        parent_datapath: str = "action_result.data.*",
        column_order_counter: Iterator[int] | None = None,
    ) -> Iterator[OutputFieldSpecification]:
        fields = list(super()._to_json_schema(parent_datapath, column_order_counter))
        column_orders = {
            "action_result.data.*.parentReference.driveId": 0,
            "action_result.data.*.id": 1,
            "action_result.data.*.name": 2,
            "action_result.data.*.webUrl": 3,
            "action_result.data.*.parentReference.folderPath": 4,
            "action_result.data.*.size": 5,
            "action_result.data.*.createdBy.user.email": 6,
            "action_result.data.*.createdDateTime": 7,
        }

        for field in fields:
            column_order = column_orders.get(field["data_path"])
            if column_order is not None:
                field["column_order"] = column_order
            yield field


def _get_target_user_id(asset: Asset) -> str:
    target_user_id = (asset.target_user_id or "").strip()
    if not target_user_id:
        raise ActionFailure(TARGET_USER_ID_REQUIRED_MESSAGE)

    return target_user_id


def _get_delegated_create_folder_endpoint(params: CreateFolderParams) -> str:
    drive_id = params.drive_id or ""
    folder_id = params.folder_id or ""
    folder_path = (params.folder_path or "").strip("/\\")

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


def _get_client_credentials_create_folder_endpoint(
    params: CreateFolderParams, asset: Asset
) -> str:
    drive_id = params.drive_id or ""
    folder_id = params.folder_id or ""
    folder_path = (params.folder_path or "").strip("/\\")
    target_user_id = _get_target_user_id(asset)

    if drive_id:
        if folder_id:
            return LIST_ITEMS_CLIENT_CREDENTIALS_DRIVE_FOLDER_ID_ENDPOINT.format(
                drive_id=drive_id,
                folder_id=folder_id,
            )
        if folder_path:
            return LIST_ITEMS_CLIENT_CREDENTIALS_DRIVE_FOLDER_PATH_ENDPOINT.format(
                drive_id=drive_id,
                folder_path=folder_path,
            )
        return LIST_ITEMS_CLIENT_CREDENTIALS_DRIVE_ID_ENDPOINT.format(drive_id=drive_id)

    if folder_id:
        return LIST_ITEMS_CLIENT_CREDENTIALS_FOLDER_ID_ENDPOINT.format(
            target_user_id=target_user_id,
            folder_id=folder_id,
        )
    if folder_path:
        return LIST_ITEMS_CLIENT_CREDENTIALS_FOLDER_PATH_ENDPOINT.format(
            target_user_id=target_user_id,
            folder_path=folder_path,
        )
    return LIST_ITEMS_CLIENT_CREDENTIALS_DEFAULT_ENDPOINT.format(
        target_user_id=target_user_id
    )


def _get_create_folder_endpoint(params: CreateFolderParams, asset: Asset) -> str:
    if is_client_credentials_auth(asset):
        return _get_client_credentials_create_folder_endpoint(params, asset)

    return _get_delegated_create_folder_endpoint(params)


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


def _get_request_body(params: CreateFolderParams) -> dict[str, Any]:
    request_body: dict[str, Any] = {
        ITEM_NAME_FIELD: params.folder_name,
        ITEM_FOLDER_FIELD: {},
    }

    if params.auto_rename:
        request_body[GRAPH_CONFLICT_BEHAVIOR_FIELD] = GRAPH_RENAME_VALUE

    return request_body


def _get_created_folder_name(response: dict[str, Any], fallback_name: str) -> str:
    created_folder_name = response.get(ITEM_NAME_FIELD)
    if created_folder_name:
        return str(created_folder_name)
    return fallback_name


def create_folder(
    params: CreateFolderParams, soar: SOARClient, asset: Asset
) -> CreateFolderOutput:
    logging.info("In action handler for: create_folder")
    endpoint = _get_create_folder_endpoint(params, asset)
    logging.info(f"Using Microsoft Graph create folder endpoint: {endpoint}")

    try:
        with get_graph_client(asset, str(soar.get_asset_id())) as graph_client:
            response = graph_client.post(endpoint, json=_get_request_body(params))
            response.raise_for_status()
            response_json = response.json()
    except OAuthClientError as e:
        raise ActionFailure(AUTHORIZATION_REQUIRED_MESSAGE) from e

    _normalize_parent_reference(response_json)
    created_folder_name = _get_created_folder_name(response_json, params.folder_name)
    soar.set_message(
        CREATE_FOLDER_SUCCESS_MESSAGE.format(folder_name=created_folder_name)
    )
    return CreateFolderOutput(**response_json)
