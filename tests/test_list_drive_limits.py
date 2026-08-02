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

from src.actions.list_drive import _get_list_response


def test_list_drive_rejects_repeated_empty_page() -> None:
    graph_client = MagicMock()
    response = MagicMock()
    response.json.return_value = {
        "value": [],
        "@odata.nextLink": "https://graph.microsoft.com/repeated",
    }
    graph_client.get.return_value = response

    with pytest.raises(ActionFailure, match="repeated a continuation URL"):
        _get_list_response(graph_client, "https://graph.microsoft.com/repeated")

    graph_client.get.assert_called_once()
