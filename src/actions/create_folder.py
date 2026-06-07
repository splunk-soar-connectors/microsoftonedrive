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
from soar_sdk.params import Param, Params

from ..asset import Asset


class CreateFolderParams(Params):
    drive_id: str | None = Param(
        description="Parent drive ID", primary=True, cef_types=["msonedrive drive id"]
    )
    folder_id: str | None = Param(
        description="Parent folder ID", primary=True, cef_types=["msonedrive folder id"]
    )
    folder_path: str | None = Param(
        description="Parent folder path",
        primary=True,
        cef_types=["msonedrive folder path"],
    )
    folder_name: str = Param(
        description="Folder name", primary=True, cef_types=["msonedrive folder name"]
    )
    auto_rename: bool | None = Param(description="Auto rename folder", default=True)


class OdataOutput(ActionOutput):
    context: str = OutputField(
        cef_types=["url"],
        example_values=[
            "https://abc.test.com/v1.0/$metadata#users(01TEST123TEST123TEST123U3KTTEST123)/drive/items(01TEST123TEST123TEST123U3KTTEST123)/children/$entity"
        ],
    )


class ApplicationOutput(ActionOutput):
    displayName: str = OutputField(example_values=["Test_One-drive"])
    id: str = OutputField(example_values=["ba56002c-856c-469f-b6a0-a4335614c502"])


class UserOutput(ActionOutput):
    displayName: str = OutputField(
        cef_types=["file path"], example_values=["Test User"]
    )
    email: str = OutputField(cef_types=["email"], example_values=["test@test.xyz.com"])
    id: str = OutputField(example_values=["17be00d0-35ed-4881-ab62-d2eb73c2ebe3"])


class CreatedbyOutput(ActionOutput):
    application: ApplicationOutput
    user: UserOutput


class FilesysteminfoOutput(ActionOutput):
    createdDateTime: str = OutputField(example_values=["2018-09-01T08:49:18Z"])
    lastModifiedDateTime: str = OutputField(example_values=["2018-09-01T08:49:18Z"])


class FolderOutput(ActionOutput):
    childCount: float = OutputField(example_values=[0])


class LastmodifiedbyOutput(ActionOutput):
    application: ApplicationOutput
    user: UserOutput


class ParentreferenceOutput(ActionOutput):
    driveId: str = OutputField(
        cef_types=["msonedrive drive id"],
        example_values=[
            "b!gy8txu3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q"
        ],
    )
    drivePath: str = OutputField(
        example_values=[
            "/drives/b!test123_TESTzTEST123faTEST123LTEST-7TEST123-MTEST123RJQb3TEST123/root:/"
        ]
    )
    driveType: str = OutputField(example_values=["business"])
    folderPath: str = OutputField(
        cef_types=["msonedrive folder path"], example_values=["Test"]
    )
    id: str = OutputField(
        cef_types=["msonedrive drive id", "msonedrive folder id"],
        example_values=["01FMDUEQY3MRPCRFEYX5FJPU3KT7J24LJB"],
    )


class CreateFolderOutput(ActionOutput):
    odata: OdataOutput
    cTag: str = OutputField(
        example_values=['"c:{2test123-1234-1234-1234-test123test1},0"']
    )
    createdBy: CreatedbyOutput
    createdDateTime: str = OutputField(example_values=["2018-09-01T08:49:18Z"])
    eTag: str = OutputField(
        example_values=['"{2test123-1234-1234-1234-test123test1},1"']
    )
    fileSystemInfo: FilesysteminfoOutput
    folder: FolderOutput
    id: str = OutputField(
        cef_types=["msonedrive folder id"],
        example_values=["01TEST123TEST123TEST123U3KTTEST123"],
    )
    lastModifiedBy: LastmodifiedbyOutput
    lastModifiedDateTime: str = OutputField(example_values=["2018-09-01T08:49:18Z"])
    name: str = OutputField(
        cef_types=["msonedrive folder name"], example_values=["Test_1 1"]
    )
    parentReference: ParentreferenceOutput
    size: float = OutputField(cef_types=["file size"], example_values=[0])
    webUrl: str = OutputField(
        cef_types=["url"],
        example_values=[
            "https://test-my.test.com/personal/test_xyz_com/Documents/Test/Test_1%201"
        ],
    )


def create_folder(
    params: CreateFolderParams, soar: SOARClient, asset: Asset
) -> CreateFolderOutput:
    raise NotImplementedError()
