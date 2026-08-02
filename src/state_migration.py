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
from pathlib import Path

from .asset import Asset


LEGACY_CLEARTEXT_STATE_KEYS = {
    "authorization_url",
    "code",
    "redirect_uri",
    "token",
}


def remove_legacy_cleartext_state(
    asset: Asset,
    *,
    legacy_app_dir: Path | None = None,
) -> None:
    """Remove credential-bearing state left by pre-SDK connector releases."""
    auth_state = asset.auth_state
    backend = getattr(auth_state, "backend", None)
    asset_id = str(getattr(auth_state, "asset_id", ""))
    if backend is None or not asset_id.isalnum():
        return

    state = backend.load_state() or {}
    migrated_state = {
        key: value
        for key, value in state.items()
        if key not in LEGACY_CLEARTEXT_STATE_KEYS
    }
    if migrated_state != state:
        backend.save_state(migrated_state)

    app_dir = legacy_app_dir or Path(__file__).resolve().parents[1]
    (app_dir / f"{asset_id}_state.json").unlink(missing_ok=True)
