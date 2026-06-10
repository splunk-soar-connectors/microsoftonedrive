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
from soar_sdk.auth import AuthorizationCodeFlow

from .asset import Asset


MICROSOFT_LOGIN_BASE_URL = "https://login.microsoftonline.com"
MICROSOFT_GRAPH_SCOPE = "files.readwrite.all"


def get_auth_code_flow(
    asset: Asset,
    asset_id: str,
    *,
    redirect_uri: str,
) -> AuthorizationCodeFlow:
    tenant = asset.tenant_id or "common"
    return AuthorizationCodeFlow(
        asset.auth_state,
        asset_id,
        client_id=asset.client_id,
        client_secret=asset.client_secret,
        authorization_endpoint=f"{MICROSOFT_LOGIN_BASE_URL}/{tenant}/oauth2/v2.0/authorize",
        token_endpoint=f"{MICROSOFT_LOGIN_BASE_URL}/{tenant}/oauth2/token",
        redirect_uri=redirect_uri,
        scope=MICROSOFT_GRAPH_SCOPE,
        extra_auth_params={"state": asset_id},
        extra_token_params={"scope": MICROSOFT_GRAPH_SCOPE},
        use_pkce=False,
    )
