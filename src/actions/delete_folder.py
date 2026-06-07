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
from soar_sdk.action_results import ActionOutput
from soar_sdk.params import Param, Params

from ..asset import Asset


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


def delete_folder(
    params: DeleteFolderParams, soar: SOARClient, asset: Asset
) -> ActionOutput:
    raise NotImplementedError()
