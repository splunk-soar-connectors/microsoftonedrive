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
from types import SimpleNamespace
from unittest.mock import MagicMock

from soar_sdk.asset_state import AssetState

from src.state_migration import remove_legacy_cleartext_state


def test_sdk_auth_partition_encrypts_tokens_at_rest() -> None:
    backend = MagicMock()
    persisted: dict = {}
    backend.load_state.side_effect = lambda: persisted
    backend.save_state.side_effect = lambda value: persisted.update(value)
    auth_state = AssetState(backend, "auth", "42", encrypted=True)

    auth_state.put_all(
        {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
        }
    )

    serialized = json.dumps(persisted)
    assert "access-token" not in serialized
    assert "refresh-token" not in serialized
    assert auth_state.get_all()["refresh_token"] == "refresh-token"


def test_migration_removes_legacy_state_and_preserves_sdk_partitions(tmp_path) -> None:
    backend = MagicMock()
    backend.load_state.return_value = {
        "app_version": "2.4.1",
        "auth": "encrypted-auth-partition",
        "cache": {"cursor": "next"},
        "token": {"refresh_token": "legacy-refresh-token"},
        "code": "legacy-authorization-code",
    }
    auth_state = SimpleNamespace(backend=backend, asset_id="42")
    asset = SimpleNamespace(auth_state=auth_state)
    legacy_copy = tmp_path / "42_state.json"
    legacy_copy.write_text('{"token":{"refresh_token":"legacy-refresh-token"}}')

    remove_legacy_cleartext_state(asset, legacy_app_dir=tmp_path)

    backend.save_state.assert_called_once_with(
        {
            "app_version": "2.4.1",
            "auth": "encrypted-auth-partition",
            "cache": {"cursor": "next"},
        }
    )
    assert not legacy_copy.exists()


def test_migration_is_idempotent_when_legacy_state_is_absent(tmp_path) -> None:
    backend = MagicMock()
    backend.load_state.return_value = {"auth": "encrypted-auth-partition"}
    asset = SimpleNamespace(
        auth_state=SimpleNamespace(backend=backend, asset_id="42")
    )

    remove_legacy_cleartext_state(asset, legacy_app_dir=tmp_path)

    backend.save_state.assert_not_called()
