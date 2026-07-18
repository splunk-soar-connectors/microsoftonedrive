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
