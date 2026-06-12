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

from soar_sdk import logging
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField
from soar_sdk.auth.client import OAuthClientError
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Params

from ..asset import Asset
from ..graph import get_graph_client


AUTHORIZATION_REQUIRED_MESSAGE = (
    "Token not available. Please run Test Connectivity first."
)
GRAPH_VALUE_FIELD = "value"
GRAPH_NEXT_LINK_FIELD = "@odata.nextLink"
LIST_DRIVES_ENDPOINT = "/me/drives"


class CreatedByUserOutput(ActionOutput):
    displayName: str = OutputField(
        column_name="Created By",
        cef_types=["user name"],
        example_values=["Test User"],
    )
    email: str = OutputField(cef_types=["email"], example_values=["test@test.abc.com"])
    id: str = OutputField(example_values=["17be76d0-35ed-4881-ab62-d2eb73c2ebe3"])


class CreatedbyOutput(ActionOutput):
    user: CreatedByUserOutput


class LastModifiedByUserOutput(ActionOutput):
    displayName: str = OutputField(
        column_name="Last Modified By",
        cef_types=["user name"],
        example_values=["Test User"],
    )
    email: str = OutputField(cef_types=["email"], example_values=["test@test.abc.com"])
    id: str = OutputField(example_values=["17be76d0-35ed-4881-ab62-d2eb73c2ebe3"])


class LastmodifiedbyOutput(ActionOutput):
    user: LastModifiedByUserOutput


class OwnerUserOutput(ActionOutput):
    displayName: str = OutputField(
        column_name="Owner",
        cef_types=["user name"],
        example_values=["Test User"],
    )
    email: str = OutputField(cef_types=["email"], example_values=["test@test.abc.com"])
    id: str = OutputField(example_values=["17be76d0-35ed-4881-ab62-d2eb73c2ebe3"])


class OwnerOutput(ActionOutput):
    user: OwnerUserOutput


class QuotaOutput(ActionOutput):
    deleted: float = OutputField(example_values=[2555167314])
    remaining: float = OutputField(example_values=[1097114685696])
    state: str = OutputField(example_values=["normal"])
    total: float = OutputField(example_values=[1099511627776])
    used: float = OutputField(example_values=[355597522])


class ListDriveOutput(ActionOutput):
    name: str = OutputField(column_name="Name", example_values=["OneDrive"])
    driveType: str = OutputField(
        column_name="Drive Type",
        example_values=["business"],
    )
    id: str = OutputField(
        column_name="Drive ID",
        cef_types=["msonedrive drive id"],
        example_values=[
            "b!test123_TESTzTEST123faTEST123LTEST-7TEST123-MTEST123RJQb3TEST123"
        ],
    )
    owner: OwnerOutput
    lastModifiedDateTime: str = OutputField(
        column_name="Last Modified Date Time",
        example_values=["2018-09-21T05:40:10Z"],
    )
    lastModifiedBy: LastmodifiedbyOutput | None
    createdDateTime: str = OutputField(
        column_name="Created Date Time",
        example_values=["2018-09-04T01:34:10Z"],
    )
    createdBy: CreatedbyOutput
    webUrl: str = OutputField(
        column_name="Web URL",
        cef_types=["url"],
        example_values=["https://test-my.abc.com/personal/test_test_xyz_com/Documents"],
    )
    description: str
    quota: QuotaOutput


class ListDriveSummary(ActionOutput):
    total_drives: int = OutputField(example_values=[1])


def _get_list_response(graph_client: Any, endpoint: str) -> list[dict[str, Any]]:
    """Return every drive from a paginated Microsoft Graph list response.

    Args:
        graph_client: Authenticated Microsoft Graph client.
        endpoint: First Graph endpoint or next-link URL to request.

    Returns:
        Every drive object from the "value" arrays across all pages.
    """
    drives: list[dict[str, Any]] = []
    next_endpoint: str | None = endpoint

    while next_endpoint:
        response = graph_client.get(next_endpoint)
        response.raise_for_status()
        response_json = response.json()
        drives.extend(response_json.get(GRAPH_VALUE_FIELD, []))
        next_endpoint = response_json.get(GRAPH_NEXT_LINK_FIELD)

    return drives


def list_drive(params: Params, soar: SOARClient, asset: Asset) -> list[ListDriveOutput]:
    logging.info("In action handler for: list_drive")

    try:
        with get_graph_client(asset, str(soar.get_asset_id())) as graph_client:
            drives = _get_list_response(graph_client, LIST_DRIVES_ENDPOINT)
    except OAuthClientError as e:
        raise ActionFailure(AUTHORIZATION_REQUIRED_MESSAGE) from e

    total_drives = len(drives)
    soar.set_summary(ListDriveSummary(total_drives=total_drives))
    soar.set_message(f"Total drives: {total_drives}")
    return [ListDriveOutput(**drive) for drive in drives]
