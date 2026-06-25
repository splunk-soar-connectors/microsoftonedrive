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

import httpx
from soar_sdk import logging
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import (
    ActionOutput,
    OutputField,
    OutputFieldSpecification,
)
from soar_sdk.auth.client import OAuthClientError
from soar_sdk.exceptions import ActionFailure, SoarAPIError
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
UNABLE_TO_RETRIEVE_VAULT_ITEM_MESSAGE = "Unable to retrieve vault item details"
VAULT_PATH_ABSENT_MESSAGE = "Vault path not accessible for provided Vault ID"
VAULT_INFO_ABSENT_MESSAGE = "Vault info not accessible for provided Vault ID"
ERROR_READING_VAULT_FILE_MESSAGE = "Reading file data from vault failed"
UPLOAD_FILE_SUCCESS_MESSAGE = "The file is uploaded successfully"
UPLOAD_FILE_FAILED_MESSAGE = "Uploading file failed"

CHUNK_SIZE = 62_914_560
UPLOAD_TIMEOUT_SECONDS = 300.0
CREATE_UPLOAD_SESSION_IF_DRIVE_ENDPOINT = (
    "/me/drives/{drive_id}/root:/{file_path}:/createUploadSession"
)
CREATE_UPLOAD_SESSION_NO_DRIVE_ENDPOINT = (
    "/me/drive/root:/{file_path}:/createUploadSession"
)
CREATE_UPLOAD_SESSION_CLIENT_CREDENTIALS_DRIVE_ENDPOINT = (
    "/drives/{drive_id}/root:/{file_path}:/createUploadSession"
)
CREATE_UPLOAD_SESSION_CLIENT_CREDENTIALS_NO_DRIVE_ENDPOINT = (
    "/users/{target_user_id}/drive/root:/{file_path}:/createUploadSession"
)
GRAPH_CONFLICT_BEHAVIOR_FIELD = "@microsoft.graph.conflictBehavior"
GRAPH_RENAME_VALUE = "rename"
GRAPH_FAIL_VALUE = "fail"
GRAPH_ITEM_FIELD = "item"
UPLOAD_URL_FIELD = "uploadUrl"
NEXT_EXPECTED_RANGES_FIELD = "nextExpectedRanges"
PARENT_REFERENCE_FIELD = "parentReference"
PARENT_PATH_FIELD = "path"
PARENT_DRIVE_PATH_FIELD = "drivePath"
PARENT_FOLDER_PATH_FIELD = "folderPath"
ROOT_PATH_SPLIT = "root:/"


class UploadFileParams(Params):
    drive_id: str | None = Param(
        description="Parent drive ID",
        primary=True,
        cef_types=["msonedrive drive id"],
        column_name="Drive ID",
    )
    vault_id: str = Param(
        description="Vault ID", primary=True, cef_types=["vault id", "sha1"]
    )
    file_path: str = Param(
        description="File path with file name", primary=True, cef_types=["file path"]
    )
    auto_rename: bool | None = Param(description="Auto rename file", default=True)


class HashesOutput(ActionOutput):
    quickXorHash: str | None = OutputField(
        example_values=["AAAAAAAAAAAAAAAAAIwPCgAAAAA="]
    )


class FileOutput(ActionOutput):
    irmEnabled: bool | None
    hashes: HashesOutput | None
    mimeType: str | None = OutputField(example_values=["text/plain"])


class ApplicationOutput(ActionOutput):
    displayName: str | None = OutputField(example_values=["Test_One-drive"])
    id: str | None = OutputField(
        example_values=["ba56122c-856c-469f-b6a0-a4335614c502"]
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
        example_values=["17be76d0-35ed-4881-ab62-d2eb73c2ebe3"]
    )


class LastModifiedByUserOutput(ActionOutput):
    displayName: str | None = OutputField(
        cef_types=["user name"], example_values=["Test User"]
    )
    email: str | None = OutputField(
        cef_types=["email"], example_values=["test@test.xyz.com"]
    )
    id: str | None = OutputField(
        example_values=["17be76d0-35ed-4881-ab62-d2eb73c2ebe3"]
    )


class CreatedbyOutput(ActionOutput):
    application: ApplicationOutput | None
    user: CreatedByUserOutput | None


class FilesysteminfoOutput(ActionOutput):
    createdDateTime: str | None = OutputField(example_values=["2018-09-01T12:22:02Z"])
    lastModifiedDateTime: str | None = OutputField(
        example_values=["2018-09-01T12:23:03Z"]
    )


class LastmodifiedbyOutput(ActionOutput):
    application: ApplicationOutput | None
    user: LastModifiedByUserOutput | None


class ParentreferenceOutput(ActionOutput):
    driveId: str | None = OutputField(
        cef_types=["msonedrive drive id"],
        example_values=[
            "b!gy8xtu3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q"
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
        example_values=["TestParent/child"],
    )
    id: str | None = OutputField(
        cef_types=["msonedrive drive id", "msonedrive folder id"],
        example_values=["01FMDEUQZDNXCWNB3JIZCIM2A27DHROBE2"],
    )


class UploadFileOutput(ActionOutput):
    content_download_url: str | None = OutputField(
        alias="@content.downloadUrl",
        cef_types=["url"],
        example_values=[
            "https://test-my.abc.com/test/test_xyz_com/_layouts/00/download.aspx?UniqueId=test&ApiVersion=2.0"
        ],
    )
    odata_context: str | None = OutputField(
        alias="@odata.context",
        cef_types=["url"],
        example_values=[
            "https://test-my.abc.com/personal/test_abc_com/_api/v2.0/$metadata#items/$entity"
        ],
    )
    odata_edit_link: str | None = OutputField(
        alias="@odata.editLink",
        example_values=[
            "drives/b!gy8xtu3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q/items/01FMDEUQ532OAQOAAUFVCL6MDY7H3CUEKN"
        ],
    )
    odata_id: str | None = OutputField(
        alias="@odata.id",
        cef_types=["url"],
        example_values=[
            "https://test-my.abc.com/personal/test_abc_com/_api/v2.0/drives/b!test123_TESTzTEST123faTEST123LTEST-7TEST123-MTEST123RJQb3TEST123/items/01TEST123TEST123TEST123U3KTTEST123"
        ],
    )
    odata_type: str | None = OutputField(
        alias="@odata.type",
        example_values=["#oneDrive.item"],
    )
    file: FileOutput | None
    cTag: str | None = OutputField(
        example_values=['"c:{2test123-1234-1234-1234-test123test1},2"']
    )
    createdBy: CreatedbyOutput | None
    createdDateTime: str | None = OutputField(
        column_name="Created At",
        example_values=["2018-09-21T12:22:02Z"],
    )
    eTag: str | None = OutputField(
        example_values=['"{2test123-1234-1234-1234-test123test1},3"']
    )
    fileSystemInfo: FilesysteminfoOutput | None
    id: str = OutputField(
        column_name="File ID",
        cef_types=["msonedrive file id"],
        example_values=["01TEST123TEST123TEST123U3KTTEST123"],
    )
    lastModifiedBy: LastmodifiedbyOutput | None
    lastModifiedDateTime: str | None = OutputField(
        example_values=["2018-09-01T12:23:03Z"]
    )
    name: str = OutputField(column_name="File Name", example_values=["test135 3.txt"])
    parentReference: ParentreferenceOutput | None
    size: float | None = OutputField(
        column_name="Size (Bytes)",
        cef_types=["file size"],
        example_values=[168791040],
    )
    webUrl: str | None = OutputField(
        column_name="File Web URL",
        cef_types=["url"],
        example_values=[
            "https://test-my.TEST.com/personal/test_xyz_com/Documents/Test/abc135%203.txt"
        ],
    )

    @classmethod
    def _to_json_schema(
        cls,
        parent_datapath: str = "action_result.data.*",
        column_order_counter: Iterator[int] | None = None,
    ) -> Iterator[OutputFieldSpecification]:
        fields = list(super()._to_json_schema(parent_datapath, column_order_counter))
        column_orders = {
            "action_result.parameter.drive_id": 0,
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


def _get_delegated_upload_session_endpoint(params: UploadFileParams) -> str:
    drive_id = params.drive_id or ""
    file_path = params.file_path.strip("/\\")

    if drive_id:
        return CREATE_UPLOAD_SESSION_IF_DRIVE_ENDPOINT.format(
            drive_id=drive_id,
            file_path=file_path,
        )
    return CREATE_UPLOAD_SESSION_NO_DRIVE_ENDPOINT.format(file_path=file_path)


def _get_client_credentials_upload_session_endpoint(
    params: UploadFileParams, asset: Asset
) -> str:
    drive_id = params.drive_id or ""
    file_path = params.file_path.strip("/\\")

    if drive_id:
        return CREATE_UPLOAD_SESSION_CLIENT_CREDENTIALS_DRIVE_ENDPOINT.format(
            drive_id=drive_id,
            file_path=file_path,
        )

    return CREATE_UPLOAD_SESSION_CLIENT_CREDENTIALS_NO_DRIVE_ENDPOINT.format(
        target_user_id=_get_target_user_id(asset),
        file_path=file_path,
    )


def _get_upload_session_endpoint(params: UploadFileParams, asset: Asset) -> str:
    if is_client_credentials_auth(asset):
        return _get_client_credentials_upload_session_endpoint(params, asset)

    return _get_delegated_upload_session_endpoint(params)


def _get_upload_session_body(params: UploadFileParams) -> dict[str, dict[str, str]]:
    conflict_behavior = GRAPH_RENAME_VALUE if params.auto_rename else GRAPH_FAIL_VALUE
    return {
        GRAPH_ITEM_FIELD: {
            GRAPH_CONFLICT_BEHAVIOR_FIELD: conflict_behavior,
        }
    }


def _get_vault_attachment(soar: SOARClient, vault_id: str) -> tuple[bytes, int]:
    try:
        attachments = soar.vault.get_attachment(vault_id=vault_id)
    except SoarAPIError as e:
        raise ActionFailure(
            f"{UNABLE_TO_RETRIEVE_VAULT_ITEM_MESSAGE},{e.message}"
        ) from e

    if not attachments:
        raise ActionFailure(UNABLE_TO_RETRIEVE_VAULT_ITEM_MESSAGE)

    attachment = attachments[0]
    if not attachment.path:
        raise ActionFailure(VAULT_PATH_ABSENT_MESSAGE)
    if not attachment.size:
        raise ActionFailure(VAULT_INFO_ABSENT_MESSAGE)

    try:
        with attachment.open("rb") as file_obj:
            file_data = file_obj.read()
    except OSError as e:
        raise ActionFailure(ERROR_READING_VAULT_FILE_MESSAGE) from e

    return file_data, len(file_data)


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


def _upload_file_chunks(
    upload_url: str,
    file_data: bytes,
    file_size: int,
) -> dict[str, Any]:
    chunk_start = 0

    while chunk_start < file_size:
        chunk_end = min(chunk_start + CHUNK_SIZE, file_size) - 1
        content = file_data[chunk_start : chunk_end + 1]
        headers = {
            "Content-Length": str(len(content)),
            "Content-Range": f"bytes {chunk_start}-{chunk_end}/{file_size}",
        }

        response = httpx.put(
            upload_url,
            headers=headers,
            content=content,
            timeout=UPLOAD_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        response_json = response.json()

        if not response_json.get(NEXT_EXPECTED_RANGES_FIELD):
            return response_json

        chunk_start = chunk_end + 1

    raise ActionFailure(UPLOAD_FILE_FAILED_MESSAGE)


def upload_file(
    params: UploadFileParams, soar: SOARClient, asset: Asset
) -> UploadFileOutput:
    logging.info("In action handler for: upload_file")
    endpoint = _get_upload_session_endpoint(params, asset)
    logging.info(f"Using Microsoft Graph upload session endpoint: {endpoint}")

    file_data, file_size = _get_vault_attachment(soar, params.vault_id)

    try:
        with get_graph_client(asset, str(soar.get_asset_id())) as graph_client:
            response = graph_client.post(
                endpoint,
                json=_get_upload_session_body(params),
            )
            response.raise_for_status()
            session_response = response.json()
    except OAuthClientError as e:
        raise ActionFailure(AUTHORIZATION_REQUIRED_MESSAGE) from e

    upload_url = session_response[UPLOAD_URL_FIELD]
    upload_response = _upload_file_chunks(upload_url, file_data, file_size)
    _normalize_parent_reference(upload_response)

    soar.set_message(UPLOAD_FILE_SUCCESS_MESSAGE)
    return UploadFileOutput(**upload_response)
