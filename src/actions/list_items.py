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


class ListItemsParams(Params):
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


class GraphOutput(ActionOutput):
    downloadUrl: str = OutputField(
        cef_types=["url"],
        example_values=[
            "https://test-my.abc.com/test/test_xyz_com/_layouts/00/download.aspx?UniqueId=test&ApiVersion=2.0"
        ],
    )


class MicrosoftOutput(ActionOutput):
    graph: GraphOutput


class ApplicationOutput(ActionOutput):
    displayName: str = OutputField(example_values=["Test_One-drive"])
    id: str = OutputField(example_values=["ba56002c-856c-469f-b6a0-a4335614c502"])


class UserOutput(ActionOutput):
    displayName: str = OutputField(
        cef_types=["user name"], example_values=["Test User"]
    )
    email: str = OutputField(cef_types=["email"], example_values=["test@test.xyz.com"])
    id: str = OutputField(example_values=["17be00d0-35ed-4881-ab62-d2eb73c2ebe3"])


class CreatedbyOutput(ActionOutput):
    application: ApplicationOutput
    user: UserOutput


class CurrentuserroleOutput(ActionOutput):
    blocksDownload: bool
    readOnly: bool


class HashesOutput(ActionOutput):
    quickXorHash: str = OutputField(example_values=["fio2VWDQgVGaX34LXedeos6Y6/s="])


class FileOutput(ActionOutput):
    hashes: HashesOutput
    mimeType: str = OutputField(example_values=["image/png"])


class FilesysteminfoOutput(ActionOutput):
    createdDateTime: str = OutputField(example_values=["2018-09-01T09:21:24Z"])
    lastModifiedDateTime: str = OutputField(example_values=["2018-09-01T09:21:24Z"])


class FolderOutput(ActionOutput):
    childCount: float = OutputField(example_values=[17])


class ImageOutput(ActionOutput):
    height: float = OutputField(example_values=[183])
    width: float = OutputField(example_values=[275])


class LastmodifiedbyOutput(ActionOutput):
    application: ApplicationOutput
    user: UserOutput


class PackageOutput(ActionOutput):
    type: str = OutputField(example_values=["oneNote"])


class ParentreferenceOutput(ActionOutput):
    driveId: str = OutputField(
        cef_types=["msonedrive drive id"],
        example_values=["example-drive-id"],
    )
    drivePath: str = OutputField(example_values=["/drive/root:/"])
    driveType: str = OutputField(example_values=["business"])
    folderPath: str = OutputField(
        cef_types=["msonedrive folder path"], example_values=["Test/child"]
    )
    id: str = OutputField(
        cef_types=["msonedrive drive id", "msonedrive folder id"],
        example_values=["example-parent-reference-id"],
    )


class ListItemsOutput(ActionOutput):
    microsoft: MicrosoftOutput
    cTag: str = OutputField(
        example_values=['"c:{2test123-1234-1234-1234-test123test1},0"']
    )
    createdBy: CreatedbyOutput
    createdDateTime: str = OutputField(example_values=["2018-09-01T09:21:24Z"])
    currentUserRole: CurrentuserroleOutput
    eTag: str = OutputField(
        example_values=['"{2test123-1234-1234-1234-test123test1},1"']
    )
    file: FileOutput
    fileSystemInfo: FilesysteminfoOutput
    folder: FolderOutput
    id: str = OutputField(
        cef_types=["msonedrive file id", "msonedrive folder id"],
        example_values=["01TEST123TEST123TEST123U3KTTEST123"],
    )
    image: ImageOutput
    lastModifiedBy: LastmodifiedbyOutput
    lastModifiedDateTime: str = OutputField(example_values=["2018-09-01T10:37:09Z"])
    name: str = OutputField(example_values=["test file"])
    package: PackageOutput
    parentReference: ParentreferenceOutput
    size: float = OutputField(cef_types=["file size"], example_values=[359666])
    webUrl: str = OutputField(
        cef_types=["url"],
        example_values=[
            "https://test-my.test.com/personal/test_abc_com/Documents/Test"
        ],
    )


def list_items(
    params: ListItemsParams, soar: SOARClient, asset: Asset
) -> ListItemsOutput:
    raise NotImplementedError()
