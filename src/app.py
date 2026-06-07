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

from .actions import register_app
from .asset import Asset


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
    return register_app(app)


app: App = create_ms_onedrive_soar_connector_app()


if __name__ == "__main__":
    app.cli()
