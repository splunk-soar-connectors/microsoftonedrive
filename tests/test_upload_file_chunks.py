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
import importlib
import io
from typing import Any


class UploadResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


def test_upload_file_chunks_streams_file_and_uses_next_expected_ranges(
    monkeypatch,
) -> None:
    upload_file = importlib.import_module("src.actions.upload_file")
    calls: list[dict[str, Any]] = []
    responses = [
        UploadResponse({"nextExpectedRanges": ["2-"]}),
        UploadResponse({"id": "uploaded-file-id", "name": "uploaded.txt"}),
    ]

    def fake_put(
        url: str,
        *,
        headers: dict[str, str],
        content: bytes,
        timeout: float,
    ) -> UploadResponse:
        calls.append(
            {
                "url": url,
                "headers": headers,
                "content": content,
                "timeout": timeout,
            }
        )
        return responses.pop(0)

    monkeypatch.setattr(upload_file, "CHUNK_SIZE", 4)
    monkeypatch.setattr(upload_file.httpx, "put", fake_put)

    result = upload_file._upload_file_chunks(
        "https://upload.example/session",
        io.BytesIO(b"abcdef"),
        6,
    )

    assert result == {"id": "uploaded-file-id", "name": "uploaded.txt"}
    assert [call["content"] for call in calls] == [b"abcd", b"cdef"]
    assert [call["headers"]["Content-Range"] for call in calls] == [
        "bytes 0-3/6",
        "bytes 2-5/6",
    ]
