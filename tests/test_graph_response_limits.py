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
from unittest.mock import MagicMock

import pytest
from soar_sdk.exceptions import ActionFailure

from src.graph import get_bounded_graph_json


def test_graph_json_rejects_response_over_byte_budget() -> None:
    graph_client = MagicMock()
    response = MagicMock()
    response.iter_bytes.return_value = [b'{"value":"', b"0123456789", b'"}']
    graph_client.stream.return_value.__enter__.return_value = response

    with pytest.raises(ActionFailure, match="response-size limit"):
        get_bounded_graph_json(graph_client, "/items", max_bytes=16)


def test_graph_json_decodes_bounded_object() -> None:
    graph_client = MagicMock()
    response = MagicMock()
    response.iter_bytes.return_value = [b'{"value": []}']
    graph_client.stream.return_value.__enter__.return_value = response

    assert get_bounded_graph_json(graph_client, "/items") == {"value": []}
