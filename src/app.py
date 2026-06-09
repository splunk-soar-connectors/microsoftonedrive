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
import httpx
from soar_sdk.abstract import SOARClient
from soar_sdk.app import App
from soar_sdk.auth import AuthorizationCodeFlow, OAuthBearerAuth
from soar_sdk.logging import progress
from soar_sdk.webhooks.models import WebhookRequest, WebhookResponse

from .actions import register_app
from .asset import Asset

OAUTH_CALLBACK_ROUTE = "oauth/callback"
MICROSOFT_LOGIN_BASE_URL = "https://login.microsoftonline.com"
MICROSOFT_GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
MICROSOFT_GRAPH_SCOPE = "Files.ReadWrite.All User.Read"


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

    app.enable_webhooks(default_requires_auth=False)

    @app.webhook(OAUTH_CALLBACK_ROUTE, allowed_methods=["GET"])
    def oauth_callback(request: WebhookRequest) -> WebhookResponse:
        tenant_id = request.asset.tenant_id or "common"
        redirect_uri = app.get_webhook_url(OAUTH_CALLBACK_ROUTE)
        flow = AuthorizationCodeFlow(
            request.asset.auth_state,
            str(request.asset_id),
            client_id=request.asset.client_id,
            client_secret=request.asset.client_secret,
            authorization_endpoint=f"{MICROSOFT_LOGIN_BASE_URL}/{tenant_id}/oauth2/v2.0/authorize",
            token_endpoint=f"{MICROSOFT_LOGIN_BASE_URL}/{tenant_id}/oauth2/v2.0/token",
            redirect_uri=redirect_uri,
            scope=MICROSOFT_GRAPH_SCOPE,
            extra_token_params={"scope": MICROSOFT_GRAPH_SCOPE},
            use_pkce=False,
        )

        query = {
            name: values[0] if values else "" for name, values in request.query.items()
        }
        if "error" in query:
            raise ValueError(query["error_description"])

        pending_session = flow.client.get_pending_session()
        if pending_session and pending_session.state != query["state"]:
            raise ValueError("OAuth state mismatch.")

        flow.set_authorization_code(query["code"])
        return WebhookResponse.text_response(
            "Authorization complete. Return to Splunk SOAR to finish test connectivity."
        )

    @app.test_connectivity()
    def test_connectivity(soar: SOARClient, asset: Asset) -> None:
        tenant_id = asset.tenant_id or "common"
        redirect_uri = app.get_webhook_url(OAUTH_CALLBACK_ROUTE)
        flow = AuthorizationCodeFlow(
            asset.auth_state,
            str(soar.get_asset_id()),
            client_id=asset.client_id,
            client_secret=asset.client_secret,
            authorization_endpoint=f"{MICROSOFT_LOGIN_BASE_URL}/{tenant_id}/oauth2/v2.0/authorize",
            token_endpoint=f"{MICROSOFT_LOGIN_BASE_URL}/{tenant_id}/oauth2/v2.0/token",
            redirect_uri=redirect_uri,
            scope=MICROSOFT_GRAPH_SCOPE,
            extra_token_params={"scope": MICROSOFT_GRAPH_SCOPE},
            use_pkce=False,
            poll_timeout=300,
            poll_interval=3,
        )

        progress("Testing connectivity. Connecting...")
        progress("Using OAuth callback URL:")
        progress(redirect_uri)
        progress("Please authorize user in a separate tab using URL")
        progress(flow.get_authorization_url())  # nosemgrep

        flow.wait_for_authorization(
            on_progress=lambda _iteration: progress("Waiting...")
        )

        progress("Getting info about the current user to verify token")
        with httpx.Client(
            base_url=MICROSOFT_GRAPH_BASE_URL,
            auth=OAuthBearerAuth(flow.client),
            timeout=30.0,
        ) as graph_client:
            response = graph_client.get("/me")
            response.raise_for_status()

        progress("Got current user info successfully")
        progress("Test Connectivity Passed")

    return register_app(app)


app: App = create_ms_onedrive_soar_connector_app()


if __name__ == "__main__":
    app.cli()
