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
from soar_sdk.app import App
from soar_sdk.params import Param, Params
from soar_sdk.action_results import ActionOutput, OutputField
from soar_sdk.logging import getLogger, PhantomLogger

from .asset import Asset

logger: PhantomLogger = getLogger()


def create_ms_onedrive_soar_connector_app() -> App:
    app = App(
        name="Microsoft OneDrive",
        app_type="sandbox",
        logo="logo_microsoftonedrive.svg",
        logo_dark="logo_microsoftonedrive_dark.svg",
        product_vendor="Microsoft",
        product_name="Microsoft OneDrive",
        publisher="Splunk",
        appid="564fe3f1-b1bb-4196-ba52-9422d0e4d430",
        fips_compliant=True,
        asset_cls=Asset,
    )

    @app.test_connectivity()
    def test_connectivity(soar: SOARClient, asset: Asset) -> None:
        raise NotImplementedError()

    return app


app: App = create_ms_onedrive_soar_connector_app()


class GetFileParams(Params):
    file_id: str | None = Param(
        description="ID of file", primary=True, cef_types=["msonedrive file id"]
    )
    drive_id: str | None = Param(
        description="Drive ID", primary=True, cef_types=["msonedrive drive id"]
    )
    file_path: str | None = Param(
        description="Path of file", primary=True, cef_types=["file path"]
    )


class GetFileOutput(ActionOutput):
    file_name: str = OutputField(example_values=["filetxt.txt"])
    size: float = OutputField(cef_types=["file size"], example_values=[4])
    vault_id: str = OutputField(
        cef_types=["vault id"],
        example_values=["example-vault-id"],
    )


@app.action(
    description="Download a file from server and add it to the vault",
    action_type="investigate",
)
def get_file(params: GetFileParams, soar: SOARClient, asset: Asset) -> GetFileOutput:
    raise NotImplementedError()


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


@app.action(description="List of items", action_type="investigate")
def list_items(
    params: ListItemsParams, soar: SOARClient, asset: Asset
) -> ListItemsOutput:
    raise NotImplementedError()


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


@app.action(description="List of Drives", action_type="investigate")
def list_drive(params: Params, soar: SOARClient, asset: Asset) -> ListDriveOutput:
    raise NotImplementedError()


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


@app.action(description="Upload file", action_type="generic", read_only=False)
def upload_file(
    params: UploadFileParams, soar: SOARClient, asset: Asset
) -> UploadFileOutput:
    raise NotImplementedError()


class DeleteFileParams(Params):
    file_id: str | None = Param(
        description="File id", primary=True, cef_types=["msonedrive file id"]
    )
    drive_id: str | None = Param(
        description="Drive id", primary=True, cef_types=["msonedrive drive id"]
    )
    file_path: str | None = Param(
        description="Path of file", primary=True, cef_types=["file path"]
    )


@app.action(description="Delete file", action_type="generic", read_only=False)
def delete_file(
    params: DeleteFileParams, soar: SOARClient, asset: Asset
) -> ActionOutput:
    raise NotImplementedError()


class DeleteFolderParams(Params):
    drive_id: str | None = Param(
        description="Parent drive ID", primary=True, cef_types=["msonedrive drive id"]
    )
    folder_id: str | None = Param(
        description="Folder ID", primary=True, cef_types=["msonedrive folder id"]
    )
    folder_path: str | None = Param(
        description="Folder path", primary=True, cef_types=["msonedrive folder path"]
    )


@app.action(description="Delete a folder", action_type="generic", read_only=False)
def delete_folder(
    params: DeleteFolderParams, soar: SOARClient, asset: Asset
) -> ActionOutput:
    raise NotImplementedError()


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


@app.action(description="Create a folder", action_type="generic", read_only=False)
def create_folder(
    params: CreateFolderParams, soar: SOARClient, asset: Asset
) -> CreateFolderOutput:
    raise NotImplementedError()


if __name__ == "__main__":
    app.cli()
