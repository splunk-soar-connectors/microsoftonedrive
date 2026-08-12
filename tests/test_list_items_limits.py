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
from unittest.mock import MagicMock, patch

import pytest
from soar_sdk.exceptions import ActionFailure

from src.actions.list_items import (
    ListItemsParams,
    _get_list_response,
    _get_max_results,
)


@pytest.mark.parametrize("max_results", [0, -1])
def test_list_items_rejects_invalid_max_results(max_results: int) -> None:
    with pytest.raises(ActionFailure, match="greater than zero"):
        _get_max_results(ListItemsParams(max_results=max_results))


def test_list_items_caps_max_results() -> None:
    assert _get_max_results(ListItemsParams(max_results=500)) == 200


def test_list_response_stops_before_fetching_another_page() -> None:
    graph_client = MagicMock()
    first_response = {
        "value": [{"id": "one"}, {"id": "two"}, {"id": "three"}],
        "@odata.nextLink": "https://graph.microsoft.com/next",
    }

    with patch(
        "src.actions.list_items.get_bounded_graph_json", return_value=first_response
    ) as get_json:
        items = _get_list_response(graph_client, "/root/children", max_results=2)

    assert items == [{"id": "one"}, {"id": "two"}]
    get_json.assert_called_once_with(graph_client, "/root/children")


def test_list_response_uses_remaining_budget_on_later_pages() -> None:
    graph_client = MagicMock()
    first_response = {
        "value": [{"id": "one"}],
        "@odata.nextLink": "https://graph.microsoft.com/next",
    }
    second_response = {
        "value": [{"id": "two"}, {"id": "three"}],
    }

    with patch(
        "src.actions.list_items.get_bounded_graph_json",
        side_effect=[first_response, second_response],
    ) as get_json:
        items = _get_list_response(graph_client, "/root/children", max_results=2)

    assert items == [{"id": "one"}, {"id": "two"}]
    assert get_json.call_count == 2


def test_list_response_rejects_repeated_empty_page() -> None:
    graph_client = MagicMock()
    response_json = {
        "value": [],
        "@odata.nextLink": "https://graph.microsoft.com/repeated",
    }

    with (
        patch(
            "src.actions.list_items.get_bounded_graph_json", return_value=response_json
        ),
        pytest.raises(ActionFailure, match="repeated a continuation URL"),
    ):
        _get_list_response(graph_client, "https://graph.microsoft.com/repeated", 10)
