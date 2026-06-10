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
import time
from soar_sdk.abstract import SOARClient
from soar_sdk.app import App
from soar_sdk.auth import AuthorizationCodeFlow, StaticTokenAuth
from soar_sdk import logging
from soar_sdk.webhooks.models import WebhookRequest, WebhookResponse

from .actions import register_app
from .asset import Asset

OAUTH_START_ROUTE = "oauth/start"
OAUTH_CALLBACK_ROUTE = "oauth/callback"
MICROSOFT_LOGIN_BASE_URL = "https://login.microsoftonline.com"
MICROSOFT_GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
MICROSOFT_GRAPH_SCOPE = "files.readwrite.all"
AUTHORIZE_WAIT_TIME = 15
AUTHORIZATION_POLL_ATTEMPTS = 35
AUTHORIZATION_POLL_INTERVAL = 3
AUTHORIZATION_URL_STATE_KEY = "authorization_url"
AUTHORIZATION_ERROR_STATE_KEY = "authorization_error"
REDIRECT_URI_STATE_KEY = "redirect_uri"


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

    @app.webhook("health", allowed_methods=["GET"])
    def health(_request: WebhookRequest) -> WebhookResponse:
        return WebhookResponse.text_response("ok")

    @app.webhook(OAUTH_START_ROUTE, allowed_methods=["GET"])
    def oauth_start(request: WebhookRequest) -> WebhookResponse:
        return WebhookResponse(
            status_code=302,
            headers=[
                ("Location", request.asset.auth_state[AUTHORIZATION_URL_STATE_KEY])
            ],
            content="",
        )

    @app.webhook(OAUTH_CALLBACK_ROUTE, allowed_methods=["GET"])
    def oauth_callback(request: WebhookRequest) -> WebhookResponse:
        tenant_id = request.asset.tenant_id or "common"
        redirect_uri = request.asset.auth_state[REDIRECT_URI_STATE_KEY]
        flow = AuthorizationCodeFlow(
            request.asset.auth_state,
            str(request.asset_id),
            client_id=request.asset.client_id,
            client_secret=request.asset.client_secret,
            authorization_endpoint=f"{MICROSOFT_LOGIN_BASE_URL}/{tenant_id}/oauth2/v2.0/authorize",
            token_endpoint=f"{MICROSOFT_LOGIN_BASE_URL}/{tenant_id}/oauth2/token",
            redirect_uri=redirect_uri,
            scope=MICROSOFT_GRAPH_SCOPE,
            extra_token_params={"scope": MICROSOFT_GRAPH_SCOPE},
            use_pkce=False,
        )

        query = {
            name: values[0] if values else "" for name, values in request.query.items()
        }
        if "error" in query:
            message = f"Error: {query['error']}"
            if query.get("error_description"):
                message = f"{message} Details: {query['error_description']}"
            request.asset.auth_state[AUTHORIZATION_ERROR_STATE_KEY] = message
            return WebhookResponse.text_response(
                f"Server returned {message}",
                status_code=400,
            )

        if query["state"] != str(request.asset_id):
            raise ValueError("OAuth state mismatch.")

        flow.set_authorization_code(query["code"])
        return WebhookResponse.text_response(
            "Code received. Please close this window, the action will continue to get new token."
        )

    @app.test_connectivity()
    def test_connectivity(soar: SOARClient, asset: Asset) -> None:
        tenant_id = asset.tenant_id or "common"
        asset.auth_state.pop(AUTHORIZATION_ERROR_STATE_KEY, None)
        redirect_uri = app.get_webhook_url(OAUTH_CALLBACK_ROUTE)
        flow = AuthorizationCodeFlow(
            asset.auth_state,
            str(soar.get_asset_id()),
            client_id=asset.client_id,
            client_secret=asset.client_secret,
            authorization_endpoint=f"{MICROSOFT_LOGIN_BASE_URL}/{tenant_id}/oauth2/v2.0/authorize",
            token_endpoint=f"{MICROSOFT_LOGIN_BASE_URL}/{tenant_id}/oauth2/token",
            redirect_uri=redirect_uri,
            scope=MICROSOFT_GRAPH_SCOPE,
            extra_auth_params={"state": str(soar.get_asset_id())},
            extra_token_params={"scope": MICROSOFT_GRAPH_SCOPE},
            use_pkce=False,
        )

        phantom_base_url = soar.get("rest/system_info").json()["base_url"].rstrip("/")

        logging.info("Testing connectivity. Connecting...")
        logging.info(f"Using Phantom base URL as: {phantom_base_url}")
        logging.info("Using OAuth URL:")
        logging.info(redirect_uri)
        asset.auth_state[REDIRECT_URI_STATE_KEY] = redirect_uri
        asset.auth_state[AUTHORIZATION_URL_STATE_KEY] = flow.get_authorization_url()
        url_for_authorize_request = (
            f"{app.get_webhook_url(OAUTH_START_ROUTE)}?asset_id={soar.get_asset_id()}&"
        )

        logging.info("Please authorize user in a separate tab using URL")
        logging.info(url_for_authorize_request)  # nosemgrep

        time.sleep(AUTHORIZE_WAIT_TIME)
        authorization_code = None
        for _ in range(AUTHORIZATION_POLL_ATTEMPTS):
            logging.progress("Waiting...")
            if authorization_error := asset.auth_state.get(
                AUTHORIZATION_ERROR_STATE_KEY
            ):
                raise ValueError(authorization_error)
            authorization_code = flow.client.get_authorization_code(force_reload=True)
            if authorization_code:
                logging.info("Authenticated")
                break
            time.sleep(AUTHORIZATION_POLL_INTERVAL)

        if not authorization_code:
            raise TimeoutError("Timeout. Please try again later.")

        logging.info("")
        logging.info("Code Received")
        logging.info("Generating access token")
        token = flow.exchange_code_for_token(authorization_code)
        flow.client._store_token(token)

        logging.info("Getting info about the current user to verify token")
        with httpx.Client(
            base_url=MICROSOFT_GRAPH_BASE_URL,
            auth=StaticTokenAuth(token),
            timeout=30.0,
        ) as graph_client:
            response = graph_client.get("/me")
            response.raise_for_status()

        logging.info("Got current user info successfully")
        logging.info("Test Connectivity Passed")

    return register_app(app)


app: App = create_ms_onedrive_soar_connector_app()


if __name__ == "__main__":
    app.cli()
