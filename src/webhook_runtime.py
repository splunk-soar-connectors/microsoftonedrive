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
import ctypes
import os
import sys
import tempfile
import threading
from typing import Any

from soar_sdk.app import App

_STDOUT_LOCK = threading.RLock()


class WebhookApp(App):
    """Keep native webhook output out of the broker's JSON response channel."""

    def handle_webhook(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        # AppInterface captures Python stdout, but native extensions write to
        # descriptor 1 directly. Restore it before the platform serializes JSON.
        with _STDOUT_LOCK, tempfile.TemporaryFile(mode="w+b") as captured:
            libc = ctypes.CDLL(None)
            sys.stdout.flush()
            libc.fflush(None)
            saved_fd = os.dup(1)
            try:
                os.dup2(captured.fileno(), 1)
                result = super().handle_webhook(*args, **kwargs)
            finally:
                try:
                    sys.stdout.flush()
                    libc.fflush(None)
                finally:
                    os.dup2(saved_fd, 1)
                    os.close(saved_fd)
                captured_bytes = captured.tell()
                if captured_bytes:
                    # AppInterface records Python stderr in app_interface.log.
                    # Never log the captured output, which may contain secrets.
                    sys.stderr.write(
                        f"Captured {captured_bytes} bytes of native stdout during webhook execution.\n"
                    )
        return result
