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
from soar_sdk.webhooks.models import WebhookRequest, WebhookResponse
import hmac

from ..auth import get_auth_code_flow
from ..consts import (
    AUTHORIZATION_ERROR_STATE_KEY,
    AUTHORIZATION_URL_STATE_KEY,
    OAUTH_CALLBACK_ROUTE,
    OAUTH_NONCE_STATE_KEY,
    OAUTH_START_ROUTE,
    REDIRECT_URI_STATE_KEY,
)


def oauth_start(request: WebhookRequest) -> WebhookResponse:
    return WebhookResponse(
        status_code=302,
        headers=[("Location", request.asset.auth_state[AUTHORIZATION_URL_STATE_KEY])],
        content="",
    )


def oauth_callback(request: WebhookRequest) -> WebhookResponse:
    flow = get_auth_code_flow(
        request.asset,
        str(request.asset_id),
        redirect_uri=request.asset.auth_state[REDIRECT_URI_STATE_KEY],
    )

    query = {
        name: values[0] if values else "" for name, values in request.query.items()
    }
    if "error" in query:
        message = f"Error: {query['error']}"
        if query.get("error_description"):
            message = f"{message} Details: {query['error_description']}"
        request.asset.auth_state[AUTHORIZATION_ERROR_STATE_KEY] = message
        request.asset.auth_state.pop(OAUTH_NONCE_STATE_KEY, None)
        return WebhookResponse.text_response(
            f"Server returned {message}",
            status_code=400,
        )

    callback_asset_id, separator, callback_nonce = query.get("state", "").partition(".")
    expected_nonce = request.asset.auth_state.get(OAUTH_NONCE_STATE_KEY, "")
    if (
        not separator
        or callback_asset_id != str(request.asset_id)
        or not expected_nonce
        or not hmac.compare_digest(callback_nonce, expected_nonce)
    ):
        raise ValueError("OAuth state mismatch.")
    if not query.get("code"):
        raise ValueError("OAuth authorization code is missing.")

    request.asset.auth_state.pop(OAUTH_NONCE_STATE_KEY, None)
    flow.set_authorization_code(query["code"])
    return WebhookResponse.text_response(
        "Code received. Please close this window, the action will continue to get new token."
    )


def register_oauth_webhooks(app: App) -> App:
    app.webhook(OAUTH_START_ROUTE, allowed_methods=["GET"])(oauth_start)
    app.webhook(OAUTH_CALLBACK_ROUTE, allowed_methods=["GET"])(oauth_callback)
    return app
