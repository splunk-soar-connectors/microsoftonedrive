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
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField
from soar_sdk.params import Params

from ..asset import Asset


class UserOutput(ActionOutput):
    displayName: str = OutputField(
        cef_types=["user name"], example_values=["Test User"]
    )
    email: str = OutputField(cef_types=["email"], example_values=["test@test.abc.com"])
    id: str = OutputField(example_values=["17be76d0-35ed-4881-ab62-d2eb73c2ebe3"])


class CreatedbyOutput(ActionOutput):
    user: UserOutput


class LastmodifiedbyOutput(ActionOutput):
    user: UserOutput


class OwnerOutput(ActionOutput):
    user: UserOutput


class QuotaOutput(ActionOutput):
    deleted: float = OutputField(example_values=[2555167314])
    remaining: float = OutputField(example_values=[1097114685696])
    state: str = OutputField(example_values=["normal"])
    total: float = OutputField(example_values=[1099511627776])
    used: float = OutputField(example_values=[355597522])


class ListDriveOutput(ActionOutput):
    createdBy: CreatedbyOutput
    createdDateTime: str = OutputField(example_values=["2018-09-04T01:34:10Z"])
    description: str
    driveType: str = OutputField(example_values=["business"])
    id: str = OutputField(
        cef_types=["msonedrive drive id"],
        example_values=[
            "b!test123_TESTzTEST123faTEST123LTEST-7TEST123-MTEST123RJQb3TEST123"
        ],
    )
    lastModifiedBy: LastmodifiedbyOutput
    lastModifiedDateTime: str = OutputField(example_values=["2018-09-21T05:40:10Z"])
    name: str = OutputField(example_values=["OneDrive"])
    owner: OwnerOutput
    quota: QuotaOutput
    webUrl: str = OutputField(
        cef_types=["url"],
        example_values=["https://test-my.abc.com/personal/test_test_xyz_com/Documents"],
    )


def list_drive(params: Params, soar: SOARClient, asset: Asset) -> ListDriveOutput:
    raise NotImplementedError()
