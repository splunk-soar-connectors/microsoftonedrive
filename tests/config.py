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
import os
from pathlib import Path


SDKFIED_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = SDKFIED_ROOT / ".env"

ASSET_CONFIG_ENV_KEYS = (
    "tenant_id",
    "client_id",
    "client_secret",
    "target_user_id",
)


def load_dotenv_file() -> None:
    """Load local .env values without overriding explicit environment values."""
    if not ENV_FILE.exists():
        return

    for raw_line in ENV_FILE.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def get_asset_config_value(name: str) -> str | None:
    """Resolve an asset config value from environment variables."""
    return os.environ.get(name)
