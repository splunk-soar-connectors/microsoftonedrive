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
import httpx
from soar_sdk.auth import OAuthBearerAuth

from .asset import Asset
from .auth import get_auth_code_flow
from .consts import MICROSOFT_GRAPH_BASE_URL, REDIRECT_URI_STATE_KEY


def get_graph_client(asset: Asset, asset_id: str) -> httpx.Client:
    flow = get_auth_code_flow(
        asset,
        asset_id,
        redirect_uri=asset.auth_state.get(REDIRECT_URI_STATE_KEY, ""),
    )
    return httpx.Client(
        base_url=MICROSOFT_GRAPH_BASE_URL,
        auth=OAuthBearerAuth(flow.client),
        timeout=30.0,
    )
