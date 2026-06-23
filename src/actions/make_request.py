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
import json
from typing import Any

import httpx
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import MakeRequestOutput
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import MakeRequestParams, Param

from ..asset import Asset
from ..graph import get_graph_client

MICROSOFT_GRAPH_ROOT_URL = "https://graph.microsoft.com"
DEFAULT_REQUEST_TIMEOUT_SECONDS = 30
INVALID_ENDPOINT_MESSAGE = (
    "Invalid endpoint: {endpoint}. Provide a Microsoft Graph path beginning with "
    "'/v1.0/' or '/beta/' and do not include the base URL."
)


class OneDriveMakeRequestParams(MakeRequestParams):
    endpoint: str = Param(
        description=(
            "Microsoft Graph endpoint to call, appended to the API base URL. "
            "Example: '/v1.0/me/drive/root' or "
            "'/beta/users/{id}/drive/root'"
        ),
        required=True,
    )
    verify_ssl: bool = Param(
        description="Whether to verify the SSL certificate.",
        required=False,
        default=True,
    )


def _get_endpoint(endpoint: str) -> str:
    endpoint = endpoint.strip()
    if endpoint.startswith(("http://", "https://")):
        raise ActionFailure(INVALID_ENDPOINT_MESSAGE.format(endpoint=endpoint))

    endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    if not endpoint.startswith(("/v1.0/", "/beta/")):
        raise ActionFailure(INVALID_ENDPOINT_MESSAGE.format(endpoint=endpoint))

    return endpoint


def _get_headers(params: OneDriveMakeRequestParams) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    if not params.headers:
        return headers

    try:
        parsed_headers = json.loads(params.headers)
    except (json.JSONDecodeError, TypeError) as e:
        raise ActionFailure(f"Invalid JSON headers: {params.headers}") from e

    if not isinstance(parsed_headers, dict):
        raise ActionFailure(f"Invalid JSON headers: {params.headers}")

    headers.update(parsed_headers)
    return headers


def _get_query_params(
    params: OneDriveMakeRequestParams,
    endpoint: str,
) -> tuple[str, dict[str, Any] | None]:
    if not params.query_parameters:
        return endpoint, None

    try:
        parsed_params = json.loads(params.query_parameters)
    except (json.JSONDecodeError, TypeError):
        query_string = params.query_parameters.lstrip("?")
        separator = "&" if "?" in endpoint else "?"
        return f"{endpoint}{separator}{query_string}", None

    if not isinstance(parsed_params, dict):
        raise ActionFailure(f"Invalid query parameters: {params.query_parameters}")

    return endpoint, parsed_params


def _get_body(params: OneDriveMakeRequestParams, headers: dict[str, str]) -> Any:
    if not params.body:
        return None

    content_type = headers.get("Content-Type", "").lower()
    if "json" not in content_type:
        return params.body

    try:
        return json.loads(params.body)
    except (json.JSONDecodeError, TypeError) as e:
        raise ActionFailure(f"Invalid JSON body: {params.body}") from e


def make_request(
    params: OneDriveMakeRequestParams, soar: SOARClient, asset: Asset
) -> MakeRequestOutput:
    """
    Make an arbitrary Microsoft Graph request using this asset's authentication.
    """
    endpoint = _get_endpoint(params.endpoint)
    headers = _get_headers(params)
    endpoint, query_params = _get_query_params(params, endpoint)
    body = _get_body(params, headers)
    timeout = params.timeout or DEFAULT_REQUEST_TIMEOUT_SECONDS

    try:
        with get_graph_client(
            asset,
            str(soar.get_asset_id()),
            base_url=MICROSOFT_GRAPH_ROOT_URL,
            verify=params.verify_ssl,
        ) as graph_client:
            response = graph_client.request(
                params.http_method,
                endpoint,
                headers=headers,
                params=query_params,
                json=body if isinstance(body, dict | list) else None,
                content=body if isinstance(body, str) else None,
                timeout=timeout,
            )
    except httpx.HTTPError as e:
        raise ActionFailure(f"Request failed: {e}") from e

    return MakeRequestOutput(
        status_code=response.status_code,
        response_body=response.text,
    )
