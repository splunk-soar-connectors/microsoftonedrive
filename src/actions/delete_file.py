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
from soar_sdk import logging
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput
from soar_sdk.auth.client import OAuthClientError
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Param, Params

from ..asset import Asset
from ..auth import is_client_credentials_auth
from ..graph import encode_graph_id, encode_graph_path, get_graph_client
from ..target_user import resolve_target_user_id, target_user_id_param


AUTHORIZATION_REQUIRED_MESSAGE = (
    "Token not available. Please run Test Connectivity first."
)
DELETE_FILE_SUCCESS_MESSAGE = "File was deleted successfully"
MANDATORY_FILE_ID_OR_PATH_MESSAGE = "Either File ID or File Path is mandatory"
DELETE_FILE_DELEGATED_DRIVE_FILE_ID_ENDPOINT = "/me/drives/{drive_id}/items/{file_id}"
DELETE_FILE_DELEGATED_DRIVE_FILE_PATH_ENDPOINT = (
    "/me/drives/{drive_id}/root:/{file_path}"
)
DELETE_FILE_DELEGATED_FILE_ID_ENDPOINT = "/me/drive/items/{file_id}"
DELETE_FILE_DELEGATED_FILE_PATH_ENDPOINT = "/me/drive/root:/{file_path}"
DELETE_FILE_CLIENT_CREDENTIALS_DRIVE_FILE_ID_ENDPOINT = (
    "/drives/{drive_id}/items/{file_id}"
)
DELETE_FILE_CLIENT_CREDENTIALS_DRIVE_FILE_PATH_ENDPOINT = (
    "/drives/{drive_id}/root:/{file_path}"
)
DELETE_FILE_CLIENT_CREDENTIALS_FILE_ID_ENDPOINT = (
    "/users/{target_user_id}/drive/items/{file_id}"
)
DELETE_FILE_CLIENT_CREDENTIALS_FILE_PATH_ENDPOINT = (
    "/users/{target_user_id}/drive/root:/{file_path}"
)


class DeleteFileParams(Params):
    file_id: str | None = Param(
        description="File id",
        primary=True,
        cef_types=["msonedrive file id"],
        column_name="File ID",
    )
    drive_id: str | None = Param(
        description="Drive id",
        primary=True,
        cef_types=["msonedrive drive id"],
        column_name="Drive ID",
    )
    file_path: str | None = Param(
        description="Path of file",
        primary=True,
        cef_types=["file path"],
        column_name="File Path",
    )
    target_user_id: str | None = target_user_id_param()


class DeleteFileOutput(ActionOutput):
    pass


def _get_delegated_delete_file_endpoint(params: DeleteFileParams) -> str:
    drive_id = encode_graph_id(params.drive_id or "")
    file_id = encode_graph_id(params.file_id or "")
    file_path = encode_graph_path((params.file_path or "").strip("/\\"))

    if not file_id and not file_path:
        raise ActionFailure(MANDATORY_FILE_ID_OR_PATH_MESSAGE)

    if drive_id:
        if file_id:
            return DELETE_FILE_DELEGATED_DRIVE_FILE_ID_ENDPOINT.format(
                drive_id=drive_id,
                file_id=file_id,
            )
        return DELETE_FILE_DELEGATED_DRIVE_FILE_PATH_ENDPOINT.format(
            drive_id=drive_id,
            file_path=file_path,
        )

    if file_id:
        return DELETE_FILE_DELEGATED_FILE_ID_ENDPOINT.format(file_id=file_id)
    return DELETE_FILE_DELEGATED_FILE_PATH_ENDPOINT.format(file_path=file_path)


def _get_client_credentials_delete_file_endpoint(
    params: DeleteFileParams, asset: Asset
) -> str:
    drive_id = encode_graph_id(params.drive_id or "")
    file_id = encode_graph_id(params.file_id or "")
    file_path = encode_graph_path((params.file_path or "").strip("/\\"))

    if not file_id and not file_path:
        raise ActionFailure(MANDATORY_FILE_ID_OR_PATH_MESSAGE)

    if drive_id:
        if file_id:
            return DELETE_FILE_CLIENT_CREDENTIALS_DRIVE_FILE_ID_ENDPOINT.format(
                drive_id=drive_id,
                file_id=file_id,
            )
        return DELETE_FILE_CLIENT_CREDENTIALS_DRIVE_FILE_PATH_ENDPOINT.format(
            drive_id=drive_id,
            file_path=file_path,
        )

    target_user_id = encode_graph_id(
        resolve_target_user_id(params.target_user_id, asset.target_user_id)
    )
    if file_id:
        return DELETE_FILE_CLIENT_CREDENTIALS_FILE_ID_ENDPOINT.format(
            target_user_id=target_user_id,
            file_id=file_id,
        )
    return DELETE_FILE_CLIENT_CREDENTIALS_FILE_PATH_ENDPOINT.format(
        target_user_id=target_user_id,
        file_path=file_path,
    )


def _get_delete_file_endpoint(params: DeleteFileParams, asset: Asset) -> str:
    if is_client_credentials_auth(asset):
        return _get_client_credentials_delete_file_endpoint(params, asset)

    return _get_delegated_delete_file_endpoint(params)


def delete_file(
    params: DeleteFileParams, soar: SOARClient, asset: Asset
) -> DeleteFileOutput:
    logging.info("In action handler for: delete_file")
    endpoint = _get_delete_file_endpoint(params, asset)
    logging.info(f"Using Microsoft Graph delete file endpoint: {endpoint}")

    try:
        with get_graph_client(asset, str(soar.get_asset_id())) as graph_client:
            response = graph_client.delete(endpoint)
            response.raise_for_status()
    except OAuthClientError as e:
        raise ActionFailure(AUTHORIZATION_REQUIRED_MESSAGE) from e

    soar.set_message(DELETE_FILE_SUCCESS_MESSAGE)
    return DeleteFileOutput()
