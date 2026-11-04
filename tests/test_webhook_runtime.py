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
import subprocess
import sys
import textwrap

import pytest

from src.webhook_runtime import WebhookApp


@pytest.mark.parametrize("raises", [False, True])
def test_native_stdout_cannot_corrupt_serialized_webhook_response(raises):
    script = textwrap.dedent(
        """
        import ctypes
        import json
        import os
        from soar_sdk.app import App
        from src.webhook_runtime import WebhookApp

        def handler(self, **kwargs):
            os.write(1, b"[2026 diagnostic] ENCRYPTION_HELPER private_key.pem secret-canary\\n")
            ctypes.CDLL(None).printf(b"buffered native secret-canary\\n")
            if RAISES:
                raise ValueError("secret-canary")
            return {"status_code":302,"headers":[("Location","https://example.invalid/authorize")],"content":""}

        App.handle_webhook = handler
        app = object.__new__(WebhookApp)
        try:
            result = app.handle_webhook()
        except ValueError:
            result = {"caught":"ValueError"}
        print(json.dumps(result))
        """
    ).replace("RAISES", repr(raises))
    process = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=True,
    )
    result = json.loads(process.stdout)
    assert "secret-canary" not in process.stdout + process.stderr
    assert "bytes of native stdout during webhook execution." in process.stderr
    if raises:
        assert result == {"caught": "ValueError"}
    else:
        assert result["status_code"] == 302
        headers = dict(result["headers"])
        assert headers["Location"] == "https://example.invalid/authorize"


def test_clean_webhook_preserves_response_and_stdout():
    script = textwrap.dedent(
        """
        import json
        from soar_sdk.app import App
        from src.webhook_runtime import WebhookApp

        def handler(self):
            return {"status_code":200,"headers":[],"content":"ok"}

        App.handle_webhook = handler
        app = object.__new__(WebhookApp)
        result = app.handle_webhook()
        print(json.dumps(result))
        """
    )
    process = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=True,
    )
    result = json.loads(process.stdout)
    assert result["status_code"] == 200
    assert result["content"] == "ok"
    assert result["headers"] == []
    assert not process.stderr


def test_app_factory_uses_native_stdout_capture(connector_app):
    assert isinstance(connector_app, WebhookApp)
