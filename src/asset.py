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
from soar_sdk.asset import BaseAsset, AssetField

from .consts import AUTH_METHOD_CLIENT_CREDENTIALS, AUTH_METHOD_DELEGATED


class Asset(BaseAsset):
    client_id: str = AssetField(description="Client ID")
    client_secret: str = AssetField(description="Client secret", sensitive=True)
    tenant_id: str | None = AssetField(description="Tenant ID", default="common")
    auth_method: str | None = AssetField(
        description="Authentication method",
        default=AUTH_METHOD_DELEGATED,
        value_list=[AUTH_METHOD_DELEGATED, AUTH_METHOD_CLIENT_CREDENTIALS],
    )
    target_user_id: str | None = AssetField(
        description="User ID or user principal name for client credentials mode",
        required=False,
    )
