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

# Used by src/app.py to pass the user-facing authorization route into test
# connectivity and by src/webhooks/oauth.py to register the redirect route.
OAUTH_START_ROUTE = "oauth/start"

# Used by src/app.py to pass the Microsoft redirect URI route into test
# connectivity and by src/webhooks/oauth.py to register the callback route.
OAUTH_CALLBACK_ROUTE = "oauth/callback"

# Used by src/test_connectivity.py to store the generated Microsoft
# authorization URL and by src/webhooks/oauth.py to redirect /oauth/start.
AUTHORIZATION_URL_STATE_KEY = "authorization_url"

# Used by src/test_connectivity.py to fail polling when Microsoft returns an
# authorization error and by src/webhooks/oauth.py to store that error.
AUTHORIZATION_ERROR_STATE_KEY = "authorization_error"

# Used by src/test_connectivity.py to store the callback URL generated in action
# context and by src/webhooks/oauth.py to rebuild the callback flow.
REDIRECT_URI_STATE_KEY = "redirect_uri"
