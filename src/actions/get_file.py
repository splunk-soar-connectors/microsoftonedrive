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
import importlib
from pathlib import Path
from tempfile import NamedTemporaryFile

import httpx
from soar_sdk import logging
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField
from soar_sdk.auth.client import OAuthClientError
from soar_sdk.exceptions import ActionFailure, SoarAPIError
from soar_sdk.params import Param, Params

from ..asset import Asset
from ..auth import is_client_credentials_auth
from ..graph import get_graph_client
from ..target_user import resolve_target_user_id, target_user_id_param


DOWNLOAD_URL_FIELD = "@microsoft.graph.downloadUrl"
FILE_HAS_NO_CONTENT_MESSAGE = "File has no content"
FILE_NOT_FOUND_MESSAGE = "The requested file does not exist on OneDrive"
ERROR_READING_DOWNLOADED_FILE_MESSAGE = "Reading downloaded file data failed"
ADD_FILE_TO_VAULT_ERROR_MESSAGE = "Could not add file to vault"
MANDATORY_FILE_ID_OR_PATH_MESSAGE = "Either File ID or File Path is mandatory"
AUTHORIZATION_REQUIRED_MESSAGE = (
    "Token not available. Please run Test Connectivity first."
)
VAULT_ATTACHMENT_LOOKUP_ERROR = "Could not retrieve attachment information"
GET_FILE_DELEGATED_DRIVE_FILE_ID_ENDPOINT = "/me/drives/{drive_id}/items/{file_id}"
GET_FILE_DELEGATED_DRIVE_FILE_PATH_ENDPOINT = "/me/drives/{drive_id}/root:/{file_path}"
GET_FILE_DELEGATED_FILE_ID_ENDPOINT = "/me/drive/items/{file_id}"
GET_FILE_DELEGATED_FILE_PATH_ENDPOINT = "/me/drive/root:/{file_path}"
GET_FILE_DELEGATED_FILE_ID_CONTENT_ENDPOINT = "/me/drive/items/{file_id}/content"
GET_FILE_DELEGATED_FILE_PATH_CONTENT_ENDPOINT = "/me/drive/root:/{file_path}:/content"
GET_FILE_CLIENT_CREDENTIALS_DRIVE_FILE_ID_ENDPOINT = (
    "/drives/{drive_id}/items/{file_id}"
)
GET_FILE_CLIENT_CREDENTIALS_DRIVE_FILE_PATH_ENDPOINT = (
    "/drives/{drive_id}/root:/{file_path}"
)
GET_FILE_CLIENT_CREDENTIALS_FILE_ID_ENDPOINT = (
    "/users/{target_user_id}/drive/items/{file_id}"
)
GET_FILE_CLIENT_CREDENTIALS_FILE_PATH_ENDPOINT = (
    "/users/{target_user_id}/drive/root:/{file_path}"
)
GET_FILE_DRIVE_FILE_ID_CONTENT_ENDPOINT = "/drives/{drive_id}/items/{file_id}/content"
GET_FILE_DRIVE_FILE_PATH_CONTENT_ENDPOINT = (
    "/drives/{drive_id}/root:/{file_path}:/content"
)
GET_FILE_CLIENT_CREDENTIALS_FILE_ID_CONTENT_ENDPOINT = (
    "/users/{target_user_id}/drive/items/{file_id}/content"
)
GET_FILE_CLIENT_CREDENTIALS_FILE_PATH_CONTENT_ENDPOINT = (
    "/users/{target_user_id}/drive/root:/{file_path}:/content"
)
FORCE_INFECTED_DOWNLOAD_HEADER = {"Prefer": "forceInfectedDownload"}
DOWNLOAD_TIMEOUT_SECONDS = 30.0
DOWNLOAD_CHUNK_SIZE = 1024 * 1024


def _log_legacy_vault_lookup(container_id: int) -> None:
    try:
        ph_rules = importlib.import_module("phantom.rules")
    except ModuleNotFoundError:
        logging.info("phantom.rules unavailable; skipping legacy vault_info diagnostic")
        return

    success, message, vault_meta_info = ph_rules.vault_info(container_id=container_id)
    vault_meta_info = list(vault_meta_info)
    logging.info(
        "legacy phantom.rules.vault_info result: "
        f"success={success}, message={message!r}, item_count={len(vault_meta_info)}"
    )


def _log_sdk_vault_lookup(container_id: int) -> None:
    try:
        phantom_vault = importlib.import_module("phantom.vault")
    except ModuleNotFoundError:
        logging.info("phantom.vault unavailable; skipping SDK vault_info diagnostic")
        return

    success, message, vault_meta_info = phantom_vault.vault_info(
        None,
        None,
        container_id,
        download_file=True,
    )
    vault_meta_info = list(vault_meta_info)
    logging.info(
        "SDK phantom.vault.vault_info result: "
        f"success={success}, message={message!r}, item_count={len(vault_meta_info)}"
    )


class GetFileParams(Params):
    file_id: str | None = Param(
        description="ID of file",
        primary=True,
        cef_types=["msonedrive file id"],
        column_name="File ID",
    )
    drive_id: str | None = Param(
        description="Drive ID",
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
    force_infected_download: bool | None = Param(
        description=(
            "Download a file that Microsoft has flagged as infected by sending "
            "the Prefer: forceInfectedDownload header"
        ),
        default=False,
        column_name="Force Infected Download",
    )
    target_user_id: str | None = target_user_id_param()


class GetFileOutput(ActionOutput):
    file_name: str = OutputField(
        column_name="File Name",
        example_values=["filetxt.txt"],
    )
    vault_id: str = OutputField(
        column_name="Vault ID",
        cef_types=["vault id"],
        example_values=["example-vault-id"],
    )
    size: float = OutputField(
        column_name="Size (Bytes)",
        cef_types=["file size"],
        example_values=[4],
    )
    force_infected_download: bool = OutputField(
        column_name="Force Infected Download",
        example_values=[False],
    )
    malware_flagged: bool = OutputField(
        column_name="Malware Flagged",
        example_values=[False],
    )


class GetFileSummary(ActionOutput):
    vault_id: str = OutputField(
        cef_types=["vault id"],
        example_values=["example-vault-id"],
    )


def _get_delegated_file_endpoint(params: GetFileParams) -> str:
    file_id = params.file_id or ""
    drive_id = params.drive_id or ""
    file_path = (params.file_path or "").strip("/\\")

    if not file_id and not file_path:
        raise ActionFailure(MANDATORY_FILE_ID_OR_PATH_MESSAGE)

    if drive_id:
        if file_id:
            return GET_FILE_DELEGATED_DRIVE_FILE_ID_ENDPOINT.format(
                drive_id=drive_id,
                file_id=file_id,
            )
        return GET_FILE_DELEGATED_DRIVE_FILE_PATH_ENDPOINT.format(
            drive_id=drive_id,
            file_path=file_path,
        )

    if file_id:
        return GET_FILE_DELEGATED_FILE_ID_ENDPOINT.format(file_id=file_id)
    return GET_FILE_DELEGATED_FILE_PATH_ENDPOINT.format(file_path=file_path)


def _get_client_credentials_file_endpoint(params: GetFileParams, asset: Asset) -> str:
    file_id = params.file_id or ""
    drive_id = params.drive_id or ""
    file_path = (params.file_path or "").strip("/\\")

    if not file_id and not file_path:
        raise ActionFailure(MANDATORY_FILE_ID_OR_PATH_MESSAGE)

    if drive_id:
        if file_id:
            return GET_FILE_CLIENT_CREDENTIALS_DRIVE_FILE_ID_ENDPOINT.format(
                drive_id=drive_id,
                file_id=file_id,
            )
        return GET_FILE_CLIENT_CREDENTIALS_DRIVE_FILE_PATH_ENDPOINT.format(
            drive_id=drive_id,
            file_path=file_path,
        )

    target_user_id = resolve_target_user_id(
        params.target_user_id,
        asset.target_user_id,
    )
    if file_id:
        return GET_FILE_CLIENT_CREDENTIALS_FILE_ID_ENDPOINT.format(
            target_user_id=target_user_id,
            file_id=file_id,
        )
    return GET_FILE_CLIENT_CREDENTIALS_FILE_PATH_ENDPOINT.format(
        target_user_id=target_user_id,
        file_path=file_path,
    )


def _get_file_endpoint(params: GetFileParams, asset: Asset) -> str:
    if is_client_credentials_auth(asset):
        return _get_client_credentials_file_endpoint(params, asset)

    return _get_delegated_file_endpoint(params)


def _get_delegated_file_content_endpoint(params: GetFileParams) -> str:
    file_id = params.file_id or ""
    drive_id = params.drive_id or ""
    file_path = (params.file_path or "").strip("/\\")

    if not file_id and not file_path:
        raise ActionFailure(MANDATORY_FILE_ID_OR_PATH_MESSAGE)

    if drive_id:
        if file_id:
            return GET_FILE_DRIVE_FILE_ID_CONTENT_ENDPOINT.format(
                drive_id=drive_id,
                file_id=file_id,
            )
        return GET_FILE_DRIVE_FILE_PATH_CONTENT_ENDPOINT.format(
            drive_id=drive_id,
            file_path=file_path,
        )

    if file_id:
        return GET_FILE_DELEGATED_FILE_ID_CONTENT_ENDPOINT.format(file_id=file_id)
    return GET_FILE_DELEGATED_FILE_PATH_CONTENT_ENDPOINT.format(file_path=file_path)


def _get_client_credentials_file_content_endpoint(
    params: GetFileParams, asset: Asset
) -> str:
    file_id = params.file_id or ""
    drive_id = params.drive_id or ""
    file_path = (params.file_path or "").strip("/\\")

    if not file_id and not file_path:
        raise ActionFailure(MANDATORY_FILE_ID_OR_PATH_MESSAGE)

    if drive_id:
        if file_id:
            return GET_FILE_DRIVE_FILE_ID_CONTENT_ENDPOINT.format(
                drive_id=drive_id,
                file_id=file_id,
            )
        return GET_FILE_DRIVE_FILE_PATH_CONTENT_ENDPOINT.format(
            drive_id=drive_id,
            file_path=file_path,
        )

    target_user_id = resolve_target_user_id(
        params.target_user_id,
        asset.target_user_id,
    )
    if file_id:
        return GET_FILE_CLIENT_CREDENTIALS_FILE_ID_CONTENT_ENDPOINT.format(
            target_user_id=target_user_id,
            file_id=file_id,
        )
    return GET_FILE_CLIENT_CREDENTIALS_FILE_PATH_CONTENT_ENDPOINT.format(
        target_user_id=target_user_id,
        file_path=file_path,
    )


def _get_file_content_endpoint(params: GetFileParams, asset: Asset) -> str:
    if is_client_credentials_auth(asset):
        return _get_client_credentials_file_content_endpoint(params, asset)

    return _get_delegated_file_content_endpoint(params)


def _get_existing_vault_id(
    soar: SOARClient,
    *,
    file_name: str,
    file_size: int,
) -> str | None:
    container_id = soar.get_executing_container_id()
    logging.info(f"Checking existing vault attachments for container_id={container_id}")
    _log_legacy_vault_lookup(container_id)
    _log_sdk_vault_lookup(container_id)

    try:
        attachments = soar.vault.get_attachment(container_id=container_id)
    except SoarAPIError as e:
        if e.message == VAULT_ATTACHMENT_LOOKUP_ERROR:
            logging.info(
                "Could not retrieve existing vault attachments; "
                "skipping duplicate check"
            )
            return None
        raise

    logging.info(f"Retrieved {len(attachments)} vault attachment(s)")

    for attachment in attachments:
        if attachment.name == file_name and attachment.size == file_size:
            logging.info(
                f"Found existing vault attachment for file_name={file_name} "
                f"size={file_size}"
            )
            return attachment.vault_id
    logging.info("No matching vault attachment found")
    return None


def _get_download_tmp_dir(soar: SOARClient) -> Path | None:
    vault_tmp_dir = Path(soar.vault.get_vault_tmp_dir())
    if vault_tmp_dir.exists():
        return vault_tmp_dir
    return None


def _download_file_to_tmp(download_url: str, temp_dir: Path | None) -> tuple[Path, int]:
    temp_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "wb",
            delete=False,
            dir=temp_dir,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            file_size = 0

            with httpx.stream(
                "GET", download_url, timeout=DOWNLOAD_TIMEOUT_SECONDS
            ) as response:
                response.raise_for_status()
                for chunk in response.iter_bytes(chunk_size=DOWNLOAD_CHUNK_SIZE):
                    if not chunk:
                        continue
                    temp_file.write(chunk)
                    file_size += len(chunk)
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise

    return temp_path, file_size


def _download_graph_content_to_tmp(
    graph_client: httpx.Client,
    endpoint: str,
    temp_dir: Path | None,
    *,
    headers: dict[str, str] | None = None,
) -> tuple[Path, int]:
    temp_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "wb",
            delete=False,
            dir=temp_dir,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            file_size = 0

            with graph_client.stream(
                "GET",
                endpoint,
                headers=headers,
                timeout=DOWNLOAD_TIMEOUT_SECONDS,
                follow_redirects=True,
            ) as response:
                response.raise_for_status()
                for chunk in response.iter_bytes(chunk_size=DOWNLOAD_CHUNK_SIZE):
                    if not chunk:
                        continue
                    temp_file.write(chunk)
                    file_size += len(chunk)
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise

    return temp_path, file_size


def _add_platform_vault_attachment(
    soar: SOARClient,
    *,
    temp_path: Path,
    file_name: str,
    metadata: dict[str, str],
) -> str | None:
    try:
        phantom_vault = importlib.import_module("phantom.vault")
        phantom = importlib.import_module("phantom.app")
    except ModuleNotFoundError:
        return None

    vault_response = phantom_vault.Vault.add_attachment(
        str(temp_path),
        container_id=soar.get_executing_container_id(),
        file_name=file_name,
        metadata=metadata,
    )
    if not vault_response.get("succeeded"):
        raise ActionFailure(ADD_FILE_TO_VAULT_ERROR_MESSAGE)

    return vault_response.get("vault_id") or vault_response[phantom.APP_JSON_HASH]


def _create_downloaded_vault_attachment(
    soar: SOARClient,
    *,
    temp_path: Path,
    file_name: str,
    file_size: int,
) -> str:
    vault_tmp_dir = _get_download_tmp_dir(soar)
    metadata = {"size": str(file_size)}
    if vault_tmp_dir is not None and temp_path.is_relative_to(vault_tmp_dir):
        platform_vault_id = _add_platform_vault_attachment(
            soar,
            temp_path=temp_path,
            file_name=file_name,
            metadata=metadata,
        )
        if platform_vault_id is not None:
            return platform_vault_id

        return soar.vault.add_attachment(
            soar.get_executing_container_id(),
            str(temp_path),
            file_name,
            metadata=metadata,
        )

    try:
        file_content = temp_path.read_bytes()
    except OSError as e:
        raise ActionFailure(ERROR_READING_DOWNLOADED_FILE_MESSAGE) from e

    return soar.vault.create_attachment(
        soar.get_executing_container_id(),
        file_content,
        file_name,
        metadata=metadata,
    )


def get_file(params: GetFileParams, soar: SOARClient, asset: Asset) -> GetFileOutput:
    logging.info("In action handler for: get_file")
    endpoint = _get_file_endpoint(params, asset)
    logging.info(f"Using Microsoft Graph metadata endpoint: {endpoint}")

    try:
        with get_graph_client(asset, str(soar.get_asset_id())) as graph_client:
            metadata_response = graph_client.get(endpoint)
            metadata_response.raise_for_status()
            metadata = metadata_response.json()

            file_name = metadata.get("name")
            if not file_name:
                raise ActionFailure(FILE_NOT_FOUND_MESSAGE)
            logging.info(f"Resolved OneDrive file metadata for file_name={file_name}")

            if params.force_infected_download:
                content_endpoint = _get_file_content_endpoint(params, asset)
                logging.info(
                    "force_infected_download enabled; using Microsoft Graph "
                    f"content endpoint: {content_endpoint}"
                )
                temp_path, file_size = _download_graph_content_to_tmp(
                    graph_client,
                    content_endpoint,
                    _get_download_tmp_dir(soar),
                    headers=FORCE_INFECTED_DOWNLOAD_HEADER,
                )
            else:
                download_url = metadata.get(DOWNLOAD_URL_FIELD)
                if not download_url:
                    raise ActionFailure(FILE_NOT_FOUND_MESSAGE)
                temp_path, file_size = _download_file_to_tmp(
                    download_url,
                    _get_download_tmp_dir(soar),
                )
    except OAuthClientError as e:
        raise ActionFailure(AUTHORIZATION_REQUIRED_MESSAGE) from e

    try:
        if not file_size:
            raise ActionFailure(FILE_HAS_NO_CONTENT_MESSAGE)
        logging.info(f"Downloaded file content size={file_size}")

        vault_id = _get_existing_vault_id(
            soar,
            file_name=file_name,
            file_size=file_size,
        )
        if vault_id is None:
            vault_id = _create_downloaded_vault_attachment(
                soar,
                temp_path=temp_path,
                file_name=file_name,
                file_size=file_size,
            )
            logging.info(f"Created vault attachment for file_name={file_name}")
    finally:
        temp_path.unlink(missing_ok=True)

    soar.set_summary(GetFileSummary(vault_id=vault_id))
    return GetFileOutput(
        file_name=file_name,
        vault_id=vault_id,
        size=file_size,
        force_infected_download=bool(params.force_infected_download),
        malware_flagged="malware" in metadata,
    )
