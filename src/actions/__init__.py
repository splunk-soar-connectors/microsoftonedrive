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
from soar_sdk.app import App

from .create_folder import create_folder
from .delete_file import delete_file
from .delete_folder import delete_folder
from .get_file import get_file
from .list_drive import list_drive
from .list_items import list_items
from .test_connectivity import test_connectivity
from .upload_file import upload_file


def register_app(app: App) -> App:
    """
    Registers all defined actions on to the provided app.

    Args:
        app(App): The app object to register actions on.

    Returns:
        App: The app object with actions registered.
    """

    app.test_connectivity()(test_connectivity)

    app.register_action(
        action=get_file,
        description="Download a file from server and add it to the vault",
        action_type="investigate",
    )
    app.register_action(
        action=list_items,
        description="List of items",
        action_type="investigate",
    )
    app.register_action(
        action=list_drive,
        description="List of Drives",
        action_type="investigate",
    )
    app.register_action(
        action=upload_file,
        description="Upload file",
        action_type="generic",
        read_only=False,
    )
    app.register_action(
        action=delete_file,
        description="Delete file",
        action_type="generic",
        read_only=False,
    )
    app.register_action(
        action=delete_folder,
        description="Delete a folder",
        action_type="generic",
        read_only=False,
    )
    app.register_action(
        action=create_folder,
        description="Create a folder",
        action_type="generic",
        read_only=False,
    )
    return app
