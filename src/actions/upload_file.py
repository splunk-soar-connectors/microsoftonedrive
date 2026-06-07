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


class UploadFileParams(Params):
    drive_id: str | None = Param(
        description="Parent drive ID", primary=True, cef_types=["msonedrive drive id"]
    )
    vault_id: str = Param(
        description="Vault ID", primary=True, cef_types=["vault id", "sha1"]
    )
    file_path: str = Param(
        description="File path with file name", primary=True, cef_types=["file path"]
    )
    auto_rename: bool | None = Param(description="Auto rename file", default=True)


class ContentOutput(ActionOutput):
    downloadUrl: str = OutputField(
        cef_types=["url"],
        example_values=[
            "https://test-my.abc.com/test/test_xyz_com/_layouts/00/download.aspx?UniqueId=test&ApiVersion=2.0"
        ],
    )


class HashesOutput(ActionOutput):
    quickXorHash: str = OutputField(example_values=["AAAAAAAAAAAAAAAAAIwPCgAAAAA="])


class FileOutput(ActionOutput):
    irmEnabled: bool
    hashes: HashesOutput
    mimeType: str = OutputField(example_values=["text/plain"])


class OdataOutput(ActionOutput):
    context: str = OutputField(
        cef_types=["url"],
        example_values=[
            "https://test-my.abc.com/personal/test_abc_com/_api/v2.0/$metadata#items/$entity"
        ],
    )
    editLink: str = OutputField(
        example_values=[
            "drives/b!gy8xtu3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q/items/01FMDEUQ532OAQOAAUFVCL6MDY7H3CUEKN"
        ]
    )
    id: str = OutputField(
        cef_types=["url"],
        example_values=[
            "https://test-my.abc.com/personal/test_abc_com/_api/v2.0/drives/b!test123_TESTzTEST123faTEST123LTEST-7TEST123-MTEST123RJQb3TEST123/items/01TEST123TEST123TEST123U3KTTEST123"
        ],
    )
    type: str = OutputField(example_values=["#oneDrive.item"])


class ApplicationOutput(ActionOutput):
    displayName: str = OutputField(example_values=["Test_One-drive"])
    id: str = OutputField(example_values=["ba56122c-856c-469f-b6a0-a4335614c502"])


class UserOutput(ActionOutput):
    displayName: str = OutputField(
        cef_types=["user name"], example_values=["Test User"]
    )
    email: str = OutputField(cef_types=["email"], example_values=["test@test.xyz.com"])
    id: str = OutputField(example_values=["17be76d0-35ed-4881-ab62-d2eb73c2ebe3"])


class CreatedbyOutput(ActionOutput):
    application: ApplicationOutput
    user: UserOutput


class FilesysteminfoOutput(ActionOutput):
    createdDateTime: str = OutputField(example_values=["2018-09-01T12:22:02Z"])
    lastModifiedDateTime: str = OutputField(example_values=["2018-09-01T12:23:03Z"])


class LastmodifiedbyOutput(ActionOutput):
    application: ApplicationOutput
    user: UserOutput


class ParentreferenceOutput(ActionOutput):
    driveId: str = OutputField(
        cef_types=["msonedrive drive id"],
        example_values=[
            "b!gy8xtu3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q"
        ],
    )
    drivePath: str = OutputField(
        example_values=[
            "/drives/b!test123_TESTzTEST123faTEST123LTEST-7TEST123-MTEST123RJQb3TEST123/root:/"
        ]
    )
    driveType: str = OutputField(example_values=["business"])
    folderPath: str = OutputField(
        cef_types=["msonedrive folder path"], example_values=["TestParent/child"]
    )
    id: str = OutputField(
        cef_types=["msonedrive drive id", "msonedrive folder id"],
        example_values=["01FMDEUQZDNXCWNB3JIZCIM2A27DHROBE2"],
    )


class UploadFileOutput(ActionOutput):
    content: ContentOutput
    file: FileOutput
    odata: OdataOutput
    cTag: str = OutputField(
        example_values=['"c:{2test123-1234-1234-1234-test123test1},2"']
    )
    createdBy: CreatedbyOutput
    createdDateTime: str = OutputField(example_values=["2018-09-21T12:22:02Z"])
    eTag: str = OutputField(
        example_values=['"{2test123-1234-1234-1234-test123test1},3"']
    )
    fileSystemInfo: FilesysteminfoOutput
    id: str = OutputField(
        cef_types=["msonedrive file id"],
        example_values=["01TEST123TEST123TEST123U3KTTEST123"],
    )
    lastModifiedBy: LastmodifiedbyOutput
    lastModifiedDateTime: str = OutputField(example_values=["2018-09-01T12:23:03Z"])
    name: str = OutputField(example_values=["test135 3.txt"])
    parentReference: ParentreferenceOutput
    size: float = OutputField(cef_types=["file size"], example_values=[168791040])
    webUrl: str = OutputField(
        cef_types=["url"],
        example_values=[
            "https://test-my.TEST.com/personal/test_xyz_com/Documents/Test/abc135%203.txt"
        ],
    )


def upload_file(
    params: UploadFileParams, soar: SOARClient, asset: Asset
) -> UploadFileOutput:
    raise NotImplementedError()
