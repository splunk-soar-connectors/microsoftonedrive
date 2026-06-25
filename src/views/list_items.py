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
from typing import Any

from soar_sdk.views.template_renderer import get_template_renderer, get_templates_dir


LIST_ITEMS_ACTION = "list items"
LIST_ITEMS_TEMPLATE = "microsoftonedrive_list_items.html"


def _get_container_id(context: dict[str, Any]) -> int | str | None:
    container = context.get("container")
    if isinstance(container, dict):
        return container.get("id")
    return getattr(container, "id", container)


def _get_context_result(provides: str, result: Any) -> dict[str, Any] | None:
    ctx_result: dict[str, Any] = {
        "param": result.get_param(),
        "action": provides,
    }

    summary = result.get_summary()
    if summary:
        ctx_result["summary"] = summary

    data = result.get_data()
    if not data:
        if provides == LIST_ITEMS_ACTION:
            ctx_result["data"] = []
        return ctx_result

    if provides == LIST_ITEMS_ACTION:
        ctx_result["data"] = data

    return ctx_result


def display_view(
    provides: str,
    all_app_runs: list[tuple[dict[str, Any], list[Any]]],
    context: dict[str, Any],
) -> str:
    """Render the custom List Items widget.

    This keeps the legacy custom-view input shape because list items needs
    access to both action parameters and action data.
    """
    context["results"] = []
    context["container_id"] = _get_container_id(context)
    context["prerender"] = True

    for _summary, action_results in all_app_runs:
        for result in action_results:
            ctx_result = _get_context_result(provides, result)
            if ctx_result:
                context["results"].append(ctx_result)

    renderer = get_template_renderer("jinja", get_templates_dir(globals()))
    return renderer.render_template(LIST_ITEMS_TEMPLATE, context)
