from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from soar_sdk.webhooks.models import WebhookRequest

from src.auth import get_auth_code_flow
from src.consts import (
    AUTHORIZATION_ERROR_STATE_KEY,
    OAUTH_NONCE_STATE_KEY,
    REDIRECT_URI_STATE_KEY,
)
from src.webhooks.oauth import oauth_callback


def _asset(nonce: str = "expected-nonce") -> SimpleNamespace:
    return SimpleNamespace(
        auth_state={
            OAUTH_NONCE_STATE_KEY: nonce,
            REDIRECT_URI_STATE_KEY: "https://soar.example/oauth/callback",
        },
        tenant_id="common",
        client_id="client-id",
        client_secret="client-secret",
    )


def _request(asset, query: dict[str, list[str]]) -> WebhookRequest:
    return WebhookRequest.model_construct(
        method="GET",
        headers={},
        path_parts=[],
        query=query,
        body=None,
        asset=asset,
        soar_base_url="https://soar.example",
        soar_auth_token="token",
        asset_id=42,
    )


def test_authorization_flow_includes_asset_and_nonce_in_state() -> None:
    asset = _asset()

    with patch("src.auth.AuthorizationCodeFlow") as flow_factory:
        get_auth_code_flow(
            asset,
            "42",
            redirect_uri="https://soar.example/oauth/callback",
        )

    assert flow_factory.call_args.kwargs["extra_auth_params"] == {
        "state": "42.expected-nonce"
    }


def test_oauth_callback_accepts_and_consumes_matching_nonce() -> None:
    asset = _asset()
    flow = MagicMock()

    with patch("src.webhooks.oauth.get_auth_code_flow", return_value=flow):
        response = oauth_callback(
            _request(asset, {"state": ["42.expected-nonce"], "code": ["code"]})
        )

    assert response.status_code == 200
    flow.set_authorization_code.assert_called_once_with("code")
    assert OAUTH_NONCE_STATE_KEY not in asset.auth_state


def test_oauth_callback_rejects_mismatch_without_consuming_valid_nonce() -> None:
    asset = _asset()

    with (
        patch("src.webhooks.oauth.get_auth_code_flow"),
        pytest.raises(ValueError, match="state mismatch"),
    ):
        oauth_callback(_request(asset, {"state": ["42.attacker"], "code": ["code"]}))

    assert asset.auth_state[OAUTH_NONCE_STATE_KEY] == "expected-nonce"


def test_oauth_callback_rejects_replay() -> None:
    asset = _asset()
    request = _request(asset, {"state": ["42.expected-nonce"], "code": ["code"]})

    with patch("src.webhooks.oauth.get_auth_code_flow"):
        oauth_callback(request)
        with pytest.raises(ValueError, match="state mismatch"):
            oauth_callback(request)


def test_oauth_provider_error_consumes_nonce_without_storing_code() -> None:
    asset = _asset()
    flow = MagicMock()

    with patch("src.webhooks.oauth.get_auth_code_flow", return_value=flow):
        response = oauth_callback(
            _request(
                asset,
                {
                    "error": ["access_denied"],
                    "error_description": ["User declined"],
                    "state": ["42.expected-nonce"],
                },
            )
        )

    assert response.status_code == 400
    assert asset.auth_state[AUTHORIZATION_ERROR_STATE_KEY].startswith(
        "Error: access_denied"
    )
    assert OAUTH_NONCE_STATE_KEY not in asset.auth_state
    flow.set_authorization_code.assert_not_called()
