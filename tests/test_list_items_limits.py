from unittest.mock import MagicMock

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
    first_response = MagicMock()
    first_response.json.return_value = {
        "value": [{"id": "one"}, {"id": "two"}, {"id": "three"}],
        "@odata.nextLink": "https://graph.microsoft.com/next",
    }
    graph_client.get.return_value = first_response

    items = _get_list_response(graph_client, "/root/children", max_results=2)

    assert items == [{"id": "one"}, {"id": "two"}]
    graph_client.get.assert_called_once_with("/root/children")


def test_list_response_uses_remaining_budget_on_later_pages() -> None:
    graph_client = MagicMock()
    first_response = MagicMock()
    first_response.json.return_value = {
        "value": [{"id": "one"}],
        "@odata.nextLink": "https://graph.microsoft.com/next",
    }
    second_response = MagicMock()
    second_response.json.return_value = {
        "value": [{"id": "two"}, {"id": "three"}],
    }
    graph_client.get.side_effect = [first_response, second_response]

    items = _get_list_response(graph_client, "/root/children", max_results=2)

    assert items == [{"id": "one"}, {"id": "two"}]
    assert graph_client.get.call_count == 2
