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

from src.graph import encode_graph_id


@pytest.mark.parametrize("identifier", [".", ".."])
def test_encode_graph_id_rejects_exact_dot_segments(identifier: str) -> None:
    with pytest.raises(ActionFailure, match="cannot be dot segments"):
        encode_graph_id(identifier)
