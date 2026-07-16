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
from typing import Any

from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Param


TARGET_USER_ID_REQUIRED_MESSAGE = (
    "Target User ID is required for Client Credentials authentication"
)


def target_user_id_param() -> Any:
    return Param(
        description=(
            "User ID or user principal name that overrides the asset Target User ID "
            "for this action in Client Credentials mode"
        ),
        column_name="Target User ID",
    )


def resolve_target_user_id(
    action_target_user_id: str | None,
    asset_target_user_id: str | None,
) -> str:
    action_target_user_id = (action_target_user_id or "").strip()
    asset_target_user_id = (asset_target_user_id or "").strip()
    target_user_id = action_target_user_id or asset_target_user_id
    if not target_user_id:
        raise ActionFailure(TARGET_USER_ID_REQUIRED_MESSAGE)
    return target_user_id
