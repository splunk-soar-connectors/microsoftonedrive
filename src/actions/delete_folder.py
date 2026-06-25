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
from ..graph import get_graph_client


AUTHORIZATION_REQUIRED_MESSAGE = (
    "Token not available. Please run Test Connectivity first."
)
TARGET_USER_ID_REQUIRED_MESSAGE = (
    "Target User ID is required for Client Credentials authentication"
)
DELETE_FOLDER_SUCCESS_MESSAGE = "The folder is deleted successfully"
MANDATORY_FOLDER_ID_OR_PATH_MESSAGE = "Either Folder ID or Folder Path is mandatory"
DELETE_FOLDER_DRIVE_FOLDER_ID_ENDPOINT = "/me/drives/{drive_id}/items/{folder_id}"
DELETE_FOLDER_DRIVE_FOLDER_PATH_ENDPOINT = "/me/drives/{drive_id}/root:/{folder_path}"
DELETE_FOLDER_FOLDER_ID_ENDPOINT = "/me/drive/items/{folder_id}"
DELETE_FOLDER_FOLDER_PATH_ENDPOINT = "/me/drive/root:/{folder_path}"
DELETE_FOLDER_CLIENT_CREDENTIALS_DRIVE_FOLDER_ID_ENDPOINT = (
    "/drives/{drive_id}/items/{folder_id}"
)
DELETE_FOLDER_CLIENT_CREDENTIALS_DRIVE_FOLDER_PATH_ENDPOINT = (
    "/drives/{drive_id}/root:/{folder_path}"
)
DELETE_FOLDER_CLIENT_CREDENTIALS_FOLDER_ID_ENDPOINT = (
    "/users/{target_user_id}/drive/items/{folder_id}"
)
DELETE_FOLDER_CLIENT_CREDENTIALS_FOLDER_PATH_ENDPOINT = (
    "/users/{target_user_id}/drive/root:/{folder_path}"
)


class DeleteFolderParams(Params):
    drive_id: str | None = Param(
        description="Parent drive ID",
        primary=True,
        cef_types=["msonedrive drive id"],
        column_name="Drive ID",
    )
    folder_id: str | None = Param(
        description="Folder ID",
        primary=True,
        cef_types=["msonedrive folder id"],
        column_name="Folder ID",
    )
    folder_path: str | None = Param(
        description="Folder path",
        primary=True,
        cef_types=["msonedrive folder path"],
        column_name="Folder Path",
    )


class DeleteFolderOutput(ActionOutput):
    pass


def _get_target_user_id(asset: Asset) -> str:
    target_user_id = (asset.target_user_id or "").strip()
    if not target_user_id:
        raise ActionFailure(TARGET_USER_ID_REQUIRED_MESSAGE)

    return target_user_id


def _get_delegated_delete_folder_endpoint(params: DeleteFolderParams) -> str:
    drive_id = params.drive_id or ""
    folder_id = params.folder_id or ""
    folder_path = (params.folder_path or "").strip("/\\")

    if not folder_id and not folder_path:
        raise ActionFailure(MANDATORY_FOLDER_ID_OR_PATH_MESSAGE)

    if drive_id:
        if folder_id:
            return DELETE_FOLDER_DRIVE_FOLDER_ID_ENDPOINT.format(
                drive_id=drive_id,
                folder_id=folder_id,
            )
        return DELETE_FOLDER_DRIVE_FOLDER_PATH_ENDPOINT.format(
            drive_id=drive_id,
            folder_path=folder_path,
        )

    if folder_id:
        return DELETE_FOLDER_FOLDER_ID_ENDPOINT.format(folder_id=folder_id)
    return DELETE_FOLDER_FOLDER_PATH_ENDPOINT.format(folder_path=folder_path)


def _get_client_credentials_delete_folder_endpoint(
    params: DeleteFolderParams, asset: Asset
) -> str:
    drive_id = params.drive_id or ""
    folder_id = params.folder_id or ""
    folder_path = (params.folder_path or "").strip("/\\")

    if not folder_id and not folder_path:
        raise ActionFailure(MANDATORY_FOLDER_ID_OR_PATH_MESSAGE)

    if drive_id:
        if folder_id:
            return DELETE_FOLDER_CLIENT_CREDENTIALS_DRIVE_FOLDER_ID_ENDPOINT.format(
                drive_id=drive_id,
                folder_id=folder_id,
            )
        return DELETE_FOLDER_CLIENT_CREDENTIALS_DRIVE_FOLDER_PATH_ENDPOINT.format(
            drive_id=drive_id,
            folder_path=folder_path,
        )

    target_user_id = _get_target_user_id(asset)
    if folder_id:
        return DELETE_FOLDER_CLIENT_CREDENTIALS_FOLDER_ID_ENDPOINT.format(
            target_user_id=target_user_id,
            folder_id=folder_id,
        )
    return DELETE_FOLDER_CLIENT_CREDENTIALS_FOLDER_PATH_ENDPOINT.format(
        target_user_id=target_user_id,
        folder_path=folder_path,
    )


def _get_delete_folder_endpoint(params: DeleteFolderParams, asset: Asset) -> str:
    if is_client_credentials_auth(asset):
        return _get_client_credentials_delete_folder_endpoint(params, asset)

    return _get_delegated_delete_folder_endpoint(params)


def delete_folder(
    params: DeleteFolderParams, soar: SOARClient, asset: Asset
) -> DeleteFolderOutput:
    logging.info("In action handler for: delete_folder")
    endpoint = _get_delete_folder_endpoint(params, asset)
    logging.info(f"Using Microsoft Graph delete folder endpoint: {endpoint}")

    try:
        with get_graph_client(asset, str(soar.get_asset_id())) as graph_client:
            response = graph_client.delete(endpoint)
            response.raise_for_status()
    except OAuthClientError as e:
        raise ActionFailure(AUTHORIZATION_REQUIRED_MESSAGE) from e

    soar.set_message(DELETE_FOLDER_SUCCESS_MESSAGE)
    return DeleteFolderOutput()
