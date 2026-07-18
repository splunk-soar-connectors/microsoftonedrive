import pytest
from soar_sdk.exceptions import ActionFailure

from src.graph import encode_graph_id, encode_graph_path


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("opaque/id", "opaque%2Fid"),
        ("../item", "..%2Fitem"),
        ("user@example.com", "user@example.com"),
        ("café", "caf%C3%A9"),
    ],
)
def test_encode_graph_id_encodes_entire_path_segment(value: str, expected: str):
    assert encode_graph_id(value) == expected


def test_encode_graph_path_preserves_only_path_separators():
    assert encode_graph_path("Reports/Q3 results/final.txt") == (
        "Reports/Q3%20results/final.txt"
    )


@pytest.mark.parametrize("value", ["../secret", "folder/./secret"])
def test_encode_graph_path_rejects_dot_segments(value: str):
    with pytest.raises(ActionFailure, match="dot segments"):
        encode_graph_path(value)
