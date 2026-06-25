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
from src.actions.list_drive import ListDriveOutput
from src.actions.list_items import ListItemsOutput


def test_list_drive_output_accepts_sparse_graph_drive() -> None:
    output = ListDriveOutput(
        **{
            "id": "drive-id",
            "name": "PersonalCacheLibrary",
            "driveType": "documentLibrary",
            "createdBy": {"user": {"displayName": "System Account"}},
            "quota": {},
        }
    )

    assert output.id == "drive-id"
    assert output.createdBy.user.displayName == "System Account"
    assert output.createdBy.user.email is None
    assert output.lastModifiedBy is None
    assert output.quota.used is None


def test_list_items_output_accepts_folder_without_file_only_fields() -> None:
    output = ListItemsOutput(
        **{
            "id": "folder-id",
            "name": "Reports",
            "folder": {"childCount": 2},
            "currentUserRole": {},
            "parentReference": {"driveId": "drive-id"},
        }
    )

    assert output.id == "folder-id"
    assert output.cTag is None
    assert output.file is None
    assert output.folder.childCount == 2
    assert output.currentUserRole.blocksDownload is None
    assert output.parentReference.driveId == "drive-id"
