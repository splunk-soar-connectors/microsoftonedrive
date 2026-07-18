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
from soar_sdk.auth import AuthorizationCodeFlow, ClientCredentialsFlow

from .asset import Asset
from .consts import AUTH_METHOD_CLIENT_CREDENTIALS, OAUTH_NONCE_STATE_KEY


MICROSOFT_LOGIN_BASE_URL = "https://login.microsoftonline.com"
MICROSOFT_GRAPH_SCOPE = "files.readwrite.all"
MICROSOFT_GRAPH_APPLICATION_SCOPE = "https://graph.microsoft.com/.default"
CLIENT_CREDENTIALS_TENANT_ERROR = (
    "Tenant ID is required for Client Credentials authentication"
)


def is_client_credentials_auth(asset: Asset) -> bool:
    return (asset.auth_method or "").strip().lower() == (
        AUTH_METHOD_CLIENT_CREDENTIALS.lower()
    )


def get_auth_code_flow(
    asset: Asset,
    asset_id: str,
    *,
    redirect_uri: str,
) -> AuthorizationCodeFlow:
    tenant = asset.tenant_id or "common"
    nonce = asset.auth_state.get(OAUTH_NONCE_STATE_KEY)
    oauth_state = f"{asset_id}.{nonce}" if nonce else asset_id
    return AuthorizationCodeFlow(
        asset.auth_state,
        asset_id,
        client_id=asset.client_id,
        client_secret=asset.client_secret,
        authorization_endpoint=f"{MICROSOFT_LOGIN_BASE_URL}/{tenant}/oauth2/v2.0/authorize",
        token_endpoint=f"{MICROSOFT_LOGIN_BASE_URL}/{tenant}/oauth2/token",
        redirect_uri=redirect_uri,
        scope=MICROSOFT_GRAPH_SCOPE,
        extra_auth_params={"state": oauth_state},
        extra_token_params={"scope": MICROSOFT_GRAPH_SCOPE},
        use_pkce=False,
    )


def get_client_credentials_flow(asset: Asset) -> ClientCredentialsFlow:
    tenant = (asset.tenant_id or "").strip()
    if not tenant or tenant.lower() == "common":
        raise ValueError(CLIENT_CREDENTIALS_TENANT_ERROR)

    return ClientCredentialsFlow(
        asset.auth_state,
        client_id=asset.client_id,
        client_secret=asset.client_secret,
        token_endpoint=f"{MICROSOFT_LOGIN_BASE_URL}/{tenant}/oauth2/v2.0/token",
        scope=MICROSOFT_GRAPH_APPLICATION_SCOPE,
    )
