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
from urllib.parse import quote
from typing import Any

import httpx
from soar_sdk.auth import OAuthBearerAuth
from soar_sdk.auth.flows import AuthorizationCodeFlow
from soar_sdk.exceptions import ActionFailure

from .asset import Asset
from .auth import (
    get_auth_code_flow,
    get_client_credentials_flow,
    is_client_credentials_auth,
)
from .consts import MICROSOFT_GRAPH_BASE_URL, REDIRECT_URI_STATE_KEY


MAX_GRAPH_JSON_BYTES = 10 * 1024 * 1024


def encode_graph_id(value: str) -> str:
    """Encode an opaque value used as one Microsoft Graph path segment."""
    if value in {".", ".."}:
        raise ActionFailure("Microsoft Graph identifiers cannot be dot segments")
    return quote(value, safe="@")


def encode_graph_path(value: str) -> str:
    """Encode a Microsoft Graph item path while retaining its separators."""
    segments = value.split("/")
    if any(segment in {".", ".."} for segment in segments):
        raise ActionFailure("Microsoft Graph paths cannot contain dot segments")
    return "/".join(encode_graph_id(segment) for segment in segments)


def get_bounded_graph_json(
    graph_client: httpx.Client,
    endpoint: str,
    *,
    max_bytes: int = MAX_GRAPH_JSON_BYTES,
) -> dict[str, Any]:
    """Stream and decode one Graph JSON response within a fixed byte budget."""
    chunks: list[bytes] = []
    total_bytes = 0
    with graph_client.stream("GET", endpoint) as response:
        response.raise_for_status()
        for chunk in response.iter_bytes():
            total_bytes += len(chunk)
            if total_bytes > max_bytes:
                raise ActionFailure(
                    "Microsoft Graph response exceeded the response-size limit"
                )
            chunks.append(chunk)

    try:
        payload = json.loads(b"".join(chunks))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ActionFailure("Microsoft Graph returned invalid JSON") from e
    if not isinstance(payload, dict):
        raise ActionFailure("Microsoft Graph returned an invalid response shape")
    return payload


def get_graph_client(
    asset: Asset,
    asset_id: str,
    *,
    base_url: str = MICROSOFT_GRAPH_BASE_URL,
    verify: bool = True,
) -> httpx.Client:
    if is_client_credentials_auth(asset):
        token = get_client_credentials_flow(asset).get_token()
        return httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token.access_token}"},
            timeout=30.0,
            verify=verify,
        )

    flow: AuthorizationCodeFlow = get_auth_code_flow(
        asset,
        asset_id,
        redirect_uri=asset.auth_state.get(REDIRECT_URI_STATE_KEY, ""),
    )
    return httpx.Client(
        base_url=base_url,
        auth=OAuthBearerAuth(oauth_client=flow.client),
        timeout=30.0,
        verify=verify,
    )
