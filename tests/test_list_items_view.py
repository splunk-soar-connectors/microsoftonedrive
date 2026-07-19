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
from soar_sdk.models.view import ViewContext
from pathlib import Path
import re

from src.actions.list_items import ListItemsOutput
from src.app import app


def test_list_items_registers_sdk_custom_view() -> None:
    action = app.actions_manager.get_action("list_items")

    assert action.meta.render_as == "custom"
    assert action.meta.view_handler is not None


def test_list_items_view_uses_parsed_outputs() -> None:
    action = app.actions_manager.get_action("list_items")
    assert action.meta.view_handler is not None

    context = ViewContext(
        QS={},
        container=123,
        app=456,
        no_connection=False,
        google_maps_key=False,
    )
    output = ListItemsOutput(
        id="folder-id",
        name="Reports",
        folder={"childCount": 2},
        parentReference={"driveId": "drive-id"},
        drive_id="configured-drive-id",
        folder_id="configured-folder-id",
        folder_path="Configured/Folder",
    )

    template_context = action.meta.view_handler.__wrapped__(context, [output])

    assert template_context["container_id"] == 123
    assert template_context["results"] == [{"data": [output]}]
    assert template_context["results"][0]["data"][0].drive_id == "configured-drive-id"


def test_list_items_widget_escapes_all_javascript_context_values() -> None:
    template = (
        Path(__file__).parents[1] / "templates" / "microsoftonedrive_list_items.html"
    ).read_text()
    interpolations = re.findall(r"'value': '(\{\{.*?\}\})'", template)

    assert interpolations
    assert all("|escapejs" in interpolation for interpolation in interpolations)
