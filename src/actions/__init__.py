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
from .get_file import get_file


def register_app(app: App) -> App:
    """
    Resgisters all defined actions on to the provided app.

    Args:
        app(App): The app object to register actions on.

    Returns:
        App: The app object with actions registered.
    """

    app.register_action(
        action=get_file,
        description="Download a file from server and add it to the vault",
        action_type="investigate",
    )
    return app
