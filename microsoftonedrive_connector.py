# File: microsoftonedrive_connector.py
#
# Copyright (c) 2019-2022 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions
# and limitations under the License.
#
#
import json
import os
import sys
import time

import phantom.app as phantom
import phantom.rules as ph_rules
import requests
from bs4 import BeautifulSoup, UnicodeDammit
from django.http import HttpResponse
from phantom.action_result import ActionResult
from phantom.base_connector import BaseConnector
from phantom.vault import Vault

from microsoftonedrive_consts import *

try:
    from urllib.parse import unquote
except:
    from urllib import unquote

DEFAULT_TIMEOUT = 30

def _handle_login_redirect(request, key):
    """ This function is used to redirect login request to Microsoft OneDrive login page.

    :param request: Data given to REST endpoint
    :param key: Key to search in state file
    :return: response authorization_url/admin_consent_url
    """

    asset_id = request.GET.get('asset_id')
    if not asset_id:
        return HttpResponse('ERROR: Asset ID not found in URL', content_type="text/plain", status=400)
    state = _load_app_state(asset_id)
    if not state:
        return HttpResponse('ERROR: Invalid asset_id', content_type="text/plain", status=400)
    url = state.get(key)
    if not url:
        return HttpResponse('App state is invalid, {key} not found.'.format(key=key), content_type="text/plain", status=400)
    response = HttpResponse(status=302)
    response['Location'] = url
    return response


def _load_app_state(asset_id, app_connector=None):
    """ This function is used to load the current state file.

    :param asset_id: asset_id
    :param app_connector: Object of app_connector class
    :return: state: Current state file as a dictionary
    """

    asset_id = str(asset_id)
    if not asset_id or not asset_id.isalnum():
        if app_connector:
            app_connector.debug_print('In _load_app_state: Invalid asset_id')
        return {}

    app_dir = os.path.dirname(os.path.abspath(__file__))
    state_file = '{0}/{1}_state.json'.format(app_dir, asset_id)
    real_state_file_path = os.path.abspath(state_file)
    if not os.path.dirname(real_state_file_path) == app_dir:
        if app_connector:
            app_connector.debug_print('In _load_app_state: Invalid asset_id')
        return {}

    state = {}
    try:
        with open(real_state_file_path, 'r') as state_file_obj:
            state_file_data = state_file_obj.read()
            state = json.loads(state_file_data)
    except Exception as e:
        if app_connector:
            app_connector.debug_print('In _load_app_state: Exception: {0}'.format(str(e)))

    if app_connector:
        app_connector.debug_print('Loaded state: ', state)

    return state


def _save_app_state(state, asset_id, app_connector):
    """ This function is used to save current state in file.

    :param state: Dictionary which contains data to write in state file
    :param asset_id: asset_id
    :param app_connector: Object of app_connector class
    :return: status: phantom.APP_SUCCESS
    """

    asset_id = str(asset_id)
    if not asset_id or not asset_id.isalnum():
        if app_connector:
            app_connector.debug_print('In _save_app_state: Invalid asset_id')
        return {}

    app_dir = os.path.split(__file__)[0]
    state_file = '{0}/{1}_state.json'.format(app_dir, asset_id)

    real_state_file_path = os.path.abspath(state_file)
    if not os.path.dirname(real_state_file_path) == app_dir:
        if app_connector:
            app_connector.debug_print('In _save_app_state: Invalid asset_id')
        return {}

    if app_connector:
        app_connector.debug_print('Saving state: ', state)

    try:
        with open(real_state_file_path, 'w+') as state_file_obj:
            state_file_obj.write(json.dumps(state))
    except Exception as e:
        print('Unable to save state file: {0}'.format(str(e)))

    return phantom.APP_SUCCESS


def _handle_login_response(request):
    """ This function is used to get the login response of authorization request from Microsoft OneDrive login page.

    :param request: Data given to REST endpoint
    :return: HttpResponse. The response displayed on authorization URL page
    """

    asset_id = request.GET.get('state')
    if not asset_id:
        return HttpResponse('ERROR: Asset ID not found in URL\n{}'.format(json.dumps(request.GET)), content_type="text/plain", status=400)

    # Check for error in URL
    error = request.GET.get('error')
    error_description = request.GET.get('error_description')

    # If there is an error in response
    if error:
        message = 'Error: {0}'.format(error)
        if error_description:
            message = '{0} Details: {1}'.format(message, error_description)
        return HttpResponse('Server returned {0}'.format(message), content_type="text/plain", status=400)

    code = request.GET.get('code')

    # If code is not available
    if not code:
        return HttpResponse('Error while authenticating\n{0}'.format(json.dumps(request.GET)), content_type="text/plain", status=400)

    state = _load_app_state(asset_id)
    state['code'] = code
    _save_app_state(state, asset_id, None)

    return HttpResponse('Code received. Please close this window, the action will continue to get new token.', content_type="text/plain")


def _handle_rest_request(request, path_parts):
    """ Handle requests for authorization.

    :param request: Data given to REST endpoint
    :param path_parts: Parts of the URL passed
    :return: Dictionary containing response parameters
    """

    if len(path_parts) < 2:
        return HttpResponse('error: True, message: Invalid REST endpoint request', content_type="text/plain", status=404)

    call_type = path_parts[1]

    # To handle authorize request in test connectivity action
    if call_type == 'start_oauth':
        return _handle_login_redirect(request, 'authorization_url')

    # To handle response from Microsoft OneDrive login page
    if call_type == 'result':
        return_val = _handle_login_response(request)
        asset_id = request.GET.get('state')
        if asset_id and asset_id.isalnum():
            app_dir = os.path.dirname(os.path.abspath(__file__))
            auth_status_file_path = '{0}/{1}_{2}'.format(app_dir, asset_id, MSONEDRIVE_TC_FILE)
            real_auth_status_file_path = os.path.abspath(auth_status_file_path)
            if not os.path.dirname(real_auth_status_file_path) == app_dir:
                return HttpResponse("Error: Invalid asset_id", content_type="text/plain", status=400)
            open(auth_status_file_path, 'w').close()
            try:
                uid = pwd.getpwnam('apache').pw_uid
                gid = grp.getgrnam('phantom').gr_gid
                os.chown(auth_status_file_path, uid, gid)
                os.chmod(auth_status_file_path, '0664')
            except:
                pass

        return return_val
    return HttpResponse('error: Invalid endpoint', content_type="text/plain", status=404)


def _get_dir_name_from_app_name(app_name):
    """ Get name of the directory for the app.

    :param app_name: Name of the application for which directory name is required
    :return: app_name: Name of the directory for the application
    """

    app_name = ''.join([x for x in app_name if x.isalnum()])
    app_name = app_name.lower()
    if not app_name:
        app_name = 'app_for_phantom'
    return app_name


class RetVal(tuple):
    def __new__(cls, val1, val2=None):
        return tuple.__new__(RetVal, (val1, val2))


class MicrosoftOnedriveConnector(BaseConnector):

    def __init__(self):

        # Call the BaseConnectors init first
        super(MicrosoftOnedriveConnector, self).__init__()

        self._state = None
        self._client_id = None
        self._client_secret = None
        self._access_token = None
        self._refresh_token = None

    def _process_empty_response(self, response, action_result):
        """ This function is used to process empty response.

        :param response: Response data
        :param action_result: Object of Action Result
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message)
        """

        # 204 is for action like 'delete folder' & 'delete file'
        if response.status_code in [200, 204]:
            return RetVal(phantom.APP_SUCCESS, {})

        return RetVal(action_result.set_status(phantom.APP_ERROR, "Empty response and no information in the header"), None)

    def _process_html_response(self, response, action_result):
        """ This function is used to process html response.

        :param response: Response data
        :param action_result: Object of Action Result
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message)
        """

        # An html response, treat it like an error
        status_code = response.status_code

        if status_code in (200, 204):
            return action_result.set_status(phantom.APP_SUCCESS)

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            # Remove the script, style, footer and navigation part from the HTML message
            for element in soup(["script", "style", "footer", "nav"]):
                element.extract()
            error_text = soup.text
            split_lines = error_text.split('\n')
            split_lines = [x.strip() for x in split_lines if x.strip()]
            error_text = '\n'.join(split_lines)
        except:
            error_text = "Cannot parse error details"

        message = "Status Code: {0}. Data from server:\n{1}\n".format(status_code,
                                                                      self._handle_py_ver_compat_for_input_str(error_text))

        message = message.replace('{', '{{').replace('}', '}}')

        return RetVal(action_result.set_status(phantom.APP_ERROR, message), None)

    def _process_json_response(self, r, action_result):
        """ This function is used to process json response.

        :param r: Response data
        :param action_result: Object of Action Result
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message)
        """

        # Try a json parse
        try:
            resp_json = r.json()
        except Exception as e:
            return RetVal(action_result.set_status(phantom.APP_ERROR, "Unable to parse JSON response. Error: {0}".format(
                self._get_error_message_from_exception(e))), None)

        # Please specify the status codes here
        if 200 <= r.status_code < 399:
            return RetVal(phantom.APP_SUCCESS, resp_json)

        # At this point, it is the error response
        if resp_json.get(MSONEDRIVE_JSON_ERROR_CODES):
            error_code = resp_json.get(MSONEDRIVE_JSON_ERROR_CODES)[0]
            error_message = resp_json.get(MSONEDRIVE_JSON_ERROR_DESCRIPTION)
            error = 'ErrorCode: {0}\nErrorMessage: {1}'.\
                    format(error_code, self._handle_py_ver_compat_for_input_str(error_message))
        elif resp_json.get(MSONEDRIVE_JSON_ERROR):
            error_code = resp_json.get(MSONEDRIVE_JSON_ERROR).get(MSONEDRIVE_JSON_CODE)
            error_message = resp_json.get(MSONEDRIVE_JSON_ERROR).get(MSONEDRIVE_JSON_MESSAGE)

            if error_code == 'UnknownError':
                error = "Unknown error occured"
            else:
                error = 'ErrorCode: {0}\nErrorMessage: {1}'.\
                        format(error_code, self._handle_py_ver_compat_for_input_str(error_message))
        else:
            error = r.text.replace('{', '{{').replace('}', '}}')

        message = "Error from server. Status Code: {0} Data from server: {1}".format(
            r.status_code, self._handle_py_ver_compat_for_input_str(error))

        return RetVal(action_result.set_status(phantom.APP_ERROR, message), None)

    def _process_response(self, r, action_result):
        """ This function is used to process html response.

        :param r: Response data
        :param action_result: Object of Action Result
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message)
        """

        # store the r_text in debug data, it will get dumped in the logs if the action fails
        if hasattr(action_result, 'add_debug_data'):
            action_result.add_debug_data({'r_status_code': r.status_code})
            action_result.add_debug_data({'r_text': r.text})
            action_result.add_debug_data({'r_headers': r.headers})

        # Process each 'Content-Type' of response separately

        # Process a json response
        if 'json' in r.headers.get('Content-Type', ''):
            return self._process_json_response(r, action_result)

        if 'text/javascript' in r.headers.get('Content-Type', ''):
            return self._process_json_response(r, action_result)

        # Process an HTML response, Do this no matter what the API talks.
        # There is a high chance of a PROXY in between phantom and the rest of
        # world, in case of errors, PROXY's return HTML, this function parses
        # the error and adds it to the action_result.
        if 'html' in r.headers.get('Content-Type', ''):
            return self._process_html_response(r, action_result)

        # it's not content-type that is to be parsed, handle an empty response
        if not r.text:
            return self._process_empty_response(r, action_result)

        # everything else is actually an error at this point
        message = "Can't process response from server. Status Code: {0} Data from server: {1}".format(
                r.status_code, self._handle_py_ver_compat_for_input_str(r.text.replace('{', '{{').replace('}', '}}')))

        return RetVal(action_result.set_status(phantom.APP_ERROR, message), None)

    def _handle_py_ver_compat_for_input_str(self, input_str):
        """
        This method returns the encoded|original string based on the Python version.
        :param input_str: Input string to be processed
        :return: input_str (Processed input string based on following logic 'input_str - Python 3; encoded input_str - Python 2')
        """

        try:
            if input_str and self._python_version == 2:
                input_str = UnicodeDammit(input_str).unicode_markup.encode('utf-8')
        except:
            self.debug_print("Error occurred while handling python 2to3 compatibility for the input string")

        return input_str

    def _get_error_message_from_exception(self, e):
        """ This method is used to get appropriate error message from the exception.
        :param e: Exception object
        :return: error message
        """

        error_msg = "Unknown error occurred. Please check the asset configuration and/or action parameters."
        error_code = "Error code unavailable"
        try:
            if hasattr(e, "args"):
                if len(e.args) > 1:
                    error_code = e.args[0]
                    error_msg = e.args[1]
                elif len(e.args) == 1:
                    error_code = "Error code unavailable"
                    error_msg = e.args[0]
            else:
                error_code = "Error code unavailable"
                error_msg = "Unknown error occurred. Please check the asset configuration and/or action parameters."
        except:
            error_code = "Error code unavailable"
            error_msg = "Unknown error occurred. Please check the asset configuration and/or action parameters."

        try:
            error_msg = self._handle_py_ver_compat_for_input_str(error_msg)
        except TypeError:
            error_msg = "Error occurred while connecting to the Microsoft server. "
            error_msg += "Please check the asset configuration and/or the action parameters."
        except:
            error_msg = "Unknown error occurred. Please check the asset configuration and/or action parameters."

        return "Error Code: {0}. Error Message: {1}".format(error_code, error_msg)

    def _make_rest_call_for_get_file(self, endpoint, action_result, headers=None, params=None, data=None, method="get", verify=True):
        """ This function is used to make the REST call.

        :param endpoint: REST URL that needs to be called
        :param action_result: Object of ActionResult class
        :param headers: Request headers
        :param params: Request parameters
        :param data: Request body
        :param method: GET/POST/PUT/DELETE/PATCH (Default will be GET)
        :param verify: Verify server certificate (Default True)
        :return: Status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message),
        response obtained by making an API call
        """

        resp_json = None

        try:
            request_func = getattr(requests, method)
        except AttributeError:
            return RetVal(action_result.set_status(phantom.APP_ERROR, "Invalid method: {0}".format(method)), resp_json)

        try:
            r = request_func(
                            endpoint,
                            data=data,
                            headers=headers,
                            verify=verify,
                            params=params)

            # In case of get_file action store response into temp file
            if self.get_action_identifier() == 'get_file':
                temp_file_path = '{dir}{asset}_temp_get_file'.format(dir=self.get_state_dir(),
                                                                     asset=self.get_asset_id())
                # If API call is success
                if 200 == r.status_code:
                    # Store response into file
                    with open(temp_file_path, 'wb') as temp_file:
                        temp_file.write(r.content)
                    return RetVal(phantom.APP_SUCCESS, {})

        except Exception as e:
            return RetVal(action_result.set_status(phantom.APP_ERROR, "Error Connecting to server. Details: {0}".format(
                self._get_error_message_from_exception(e))), resp_json)

        return self._process_response(r, action_result)

    def _make_rest_call(self, endpoint, action_result, headers=None, params=None, data=None, method="get", verify=True):
        """ This function is used to make the REST call.

        :param endpoint: REST URL that needs to be called
        :param action_result: Object of ActionResult class
        :param headers: Request headers
        :param params: Request parameters
        :param data: Request body
        :param method: GET/POST/PUT/DELETE/PATCH (Default will be GET)
        :param verify: Verify server certificate (Default True)
        :return: Status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message),
        response obtained by making an API call
        """

        resp_json = None

        if headers is None:
            headers = {}

        try:
            request_func = getattr(requests, method)
        except AttributeError:
            return RetVal(action_result.set_status(phantom.APP_ERROR, "Invalid method: {0}".format(method)), resp_json)

        try:
            r = request_func(
                            endpoint,
                            data=data,
                            headers=headers,
                            verify=verify,
                            params=params)
        except Exception as e:
            return RetVal(action_result.set_status(phantom.APP_ERROR, "Error Connecting to server. Details: {0}".format(
                self._get_error_message_from_exception(e))), resp_json)

        return self._process_response(r, action_result)

    def _get_asset_name(self, action_result):
        """ Get name of the asset using Phantom URL.

        :param action_result: object of ActionResult class
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message), asset name
        """

        asset_id = self.get_asset_id()
        rest_endpoint = MSONEDRIVE_PHANTOM_ASSET_INFO_URL.format(asset_id=asset_id)
        url = '{0}{1}{2}'.format(BaseConnector._get_phantom_base_url(), 'rest', rest_endpoint)
        ret_val, resp_json = self._make_rest_call(action_result=action_result, endpoint=url, verify=False)

        if phantom.is_fail(ret_val):
            return ret_val, None

        asset_name = resp_json.get('name')
        if not asset_name:
            return action_result.set_status(phantom.APP_ERROR, 'Asset Name for id: {0} not found.'.format(asset_id),
                                            None)

        return phantom.APP_SUCCESS, asset_name

    def _wait(self, action_result):
        """ This function is used to hold the action till user login.

        :param action_result: Object of ActionResult class
        :return: status (success/failed)
        """

        app_dir = os.path.dirname(os.path.abspath(__file__))
        # file to check whether the request has been granted or not
        auth_status_file_path = '{0}/{1}_{2}'.format(app_dir, self.get_asset_id(), MSONEDRIVE_TC_FILE)
        time_out = False

        # wait-time while request is being granted
        for _ in range(0, 35):
            self.send_progress('Waiting...')
            if os.path.isfile(auth_status_file_path):
                time_out = True
                os.unlink(auth_status_file_path)
                break
            time.sleep(MSONEDRIVE_TC_STATUS_SLEEP)

        if not time_out:
            return action_result.set_status(phantom.APP_ERROR, status_message='Timeout. Please try again later.')
        self.send_progress('Authenticated')
        return phantom.APP_SUCCESS

    def _get_phantom_base_url(self, action_result):
        """ Get base url of phantom.

        :param action_result: object of ActionResult class
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message),
        base url of phantom
        """

        url = '{0}{1}{2}'.format(BaseConnector._get_phantom_base_url(), 'rest', MSONEDRIVE_PHANTOM_SYS_INFO_URL)
        ret_val, resp_json = self._make_rest_call(action_result=action_result, endpoint=url, verify=False)
        if phantom.is_fail(ret_val):
            return ret_val, None

        phantom_base_url = resp_json.get('base_url')
        if not phantom_base_url:
            return action_result.set_status(phantom.APP_ERROR, MSONEDRIVE_BASE_URL_NOT_FOUND_MSG), None
        return phantom.APP_SUCCESS, phantom_base_url.rstrip('/')

    def _get_app_rest_url(self, action_result):
        """ Get URL for making rest calls.

        :param action_result: object of ActionResult class
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message),
        URL to make rest calls
        """

        ret_val, phantom_base_url = self._get_phantom_base_url(action_result)
        if phantom.is_fail(ret_val):
            return action_result.get_status(), None

        ret_val, asset_name = self._get_asset_name(action_result)
        if phantom.is_fail(ret_val):
            return action_result.get_status(), None

        self.save_progress('Using Phantom base URL as: {0}'.format(phantom_base_url))
        app_json = self.get_app_json()
        app_name = app_json['name']

        app_dir_name = _get_dir_name_from_app_name(app_name)
        url_to_app_rest = '{0}/rest/handler/{1}_{2}/{3}'.format(phantom_base_url, app_dir_name, app_json['appid'],
                                                                asset_name)
        return phantom.APP_SUCCESS, url_to_app_rest

    def _generate_new_access_token(self, action_result, data):
        """ This function is used to generate new access token using the code obtained on authorization.

        :param action_result: object of ActionResult class
        :param data: Data to send in REST call
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS
        """

        req_url = '{}{}'.format(MSONEDRIVE_LOGIN_BASE_URL, MSONEDRIVE_SERVER_TOKEN_URL)
        ret_val, resp_json = self._make_rest_call(action_result=action_result, endpoint=req_url,
                                                  data=data, method=MSONEDRIVE_METHOD_POST)
        if phantom.is_fail(ret_val):
            return action_result.get_status()

        # If there is any error while generating access_token, API returns 200 with error and error_description fields
        if not resp_json.get(MSONEDRIVE_ACCESS_TOKEN_STRING):
            if resp_json.get(MSONEDRIVE_JSON_ERROR_DESCRIPTION):
                return action_result.set_status(phantom.APP_ERROR, status_message=resp_json[MSONEDRIVE_JSON_ERROR_DESCRIPTION])

            return action_result.set_status(phantom.APP_ERROR, status_message='Error while generating access_token')

        self._state[MSONEDRIVE_TOKEN_STRING] = resp_json
        self.save_state(self._state)
        _save_app_state(self._state, self.get_asset_id(), self)
        self._state = self.load_state()

        self._access_token = resp_json[MSONEDRIVE_ACCESS_TOKEN_STRING]
        self._refresh_token = resp_json[MSONEDRIVE_REFRESH_TOKEN_STRING]

        # Scenario -
        #
        # If the corresponding state file doesn't have the correct owner, owner group or permissions,
        # the newly generated token is not being saved to state file and automatic workflow for the token has been stopped.
        # So we have to check that token from response and token which is saved to state file
        # after successful generation of the new token are the same or not.

        if self._access_token != self._state.get(MSONEDRIVE_TOKEN_STRING, {}).get(MSONEDRIVE_ACCESS_TOKEN_STRING):
            message = "Error occurred while saving the newly generated access token (in place of the expired token) in the state file."
            message += " Please check the owner, owner group, and the permissions of the state file. The Phantom "
            message += "user should have the correct access rights and ownership for the corresponding state file "
            message += "(refer to the readme file for more information)."
            return action_result.set_status(phantom.APP_ERROR, message)

        return phantom.APP_SUCCESS

    def _update_request(self, action_result, endpoint, headers=None, params=None, data=None, method='get'):
        """ This function is used to update the headers with access_token before making REST call.

        :param endpoint: REST endpoint that needs to appended to the service address
        :param action_result: object of ActionResult class
        :param headers: request headers
        :param params: request parameters
        :param data: request body
        :param method: GET/POST/PUT/DELETE/PATCH (Default will be GET)
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message),
        response obtained by making an API call
        """

        # In pagination, URL of next page contains complete URL
        # So no need to modify them
        if not endpoint.startswith(MSONEDRIVE_MSGRAPH_API_BASE_URL):
            endpoint = '{0}{1}'.format(MSONEDRIVE_MSGRAPH_API_BASE_URL, endpoint)

        if headers is None:
            headers = {}

        token_data = {
            MSONEDRIVE_CONFIG_CLIENT_ID: self._client_id,
            MSONEDRIVE_JSON_SCOPE: MSONEDRIVE_REST_REQUEST_SCOPE,
            MSONEDRIVE_CONFIG_CLIENT_SECRET: self._client_secret,
            MSONEDRIVE_JSON_GRANT_TYPE: MSONEDRIVE_REFRESH_TOKEN_STRING,
            MSONEDRIVE_REFRESH_TOKEN_STRING: self._refresh_token
        }

        if not self._access_token:
            if not self._refresh_token:
                # If none of the access_token and refresh_token is available
                return action_result.set_status(phantom.APP_ERROR, status_message=MSONEDRIVE_TOKEN_NOT_AVAILABLE_MSG), None

            # If refresh_token is available and access_token is not available, generate new access_token
            status = self._generate_new_access_token(action_result=action_result, data=token_data)

            if phantom.is_fail(status):
                return action_result.get_status(), None

        headers.update({'Authorization': 'Bearer {0}'.format(self._access_token)})
        if not headers.get('Content-Type'):
            headers.update({'Content-Type': 'application/json'})

        ret_val, resp_json = self._make_rest_call(action_result=action_result, endpoint=endpoint, headers=headers,
                                                  params=params, data=data, method=method)

        # If token is expired, generate new token
        if MSONEDRIVE_TOKEN_EXPIRED in action_result.get_message():
            status = self._generate_new_access_token(action_result=action_result, data=token_data)

            if phantom.is_fail(status):
                return action_result.get_status(), None

            headers.update({'Authorization': 'Bearer {0}'.format(self._access_token)})
            ret_val, resp_json = self._make_rest_call(action_result=action_result, endpoint=endpoint, headers=headers,
                                                      params=params, data=data, method=method)
        if phantom.is_fail(ret_val):
            return action_result.get_status(), None

        return phantom.APP_SUCCESS, resp_json

    def _handle_test_connectivity(self, param):
        """ This function is used to handle the test connectivity action.

        :param param: Dictionary of input parameters
        :return: Status(phantom.APP_SUCCESS/phantom.APP_ERROR)
        """

        # Add an action result object to self (BaseConnector) to represent the action for this param
        action_result = self.add_action_result(ActionResult(dict(param)))
        self.save_progress(MSONEDRIVE_MAKING_CONNECTION_MSG)
        app_state = {}

        # Get initial REST URL
        ret_val, app_rest_url = self._get_app_rest_url(action_result)
        if phantom.is_fail(ret_val):
            self.save_progress(MSONEDRIVE_REST_URL_NOT_AVAILABLE_MSG.format(error=action_result.get_message()))
            return action_result.get_status()

        # Append /result to create redirect_uri
        redirect_uri = '{0}/result'.format(app_rest_url)
        app_state[MSONEDRIVE_JSON_REDIRECT_URI] = redirect_uri

        self.save_progress(MSONEDRIVE_OAUTH_URL_MSG)
        self.save_progress(redirect_uri)

        # Authorization URL used to make request for getting code which is used to generate access token
        authorization_url = MSONEDRIVE_AUTHORIZE_URL.format(client_id=self._client_id,
                                                            redirect_uri=redirect_uri,
                                                            response_type=MSONEDRIVE_JSON_CODE,
                                                            state=self.get_asset_id(),
                                                            scope=MSONEDRIVE_REST_REQUEST_SCOPE)

        authorization_url = '{}{}'.format(MSONEDRIVE_LOGIN_BASE_URL, authorization_url)
        app_state[MSONEDRIVE_JSON_AUTHORIZATION_URL] = authorization_url

        # URL which would be shown to the user
        url_for_authorize_request = '{0}/start_oauth?asset_id={1}&'.format(app_rest_url, self.get_asset_id())
        _save_app_state(app_state, self.get_asset_id(), self)

        self.save_progress(MSONEDRIVE_AUTHORIZE_USER_MSG)
        self.save_progress(url_for_authorize_request)

        # Wait time for authorization
        time.sleep(MSONEDRIVE_AUTHORIZE_WAIT_TIME)

        # Wait for some while user login to Microsoft
        status = self._wait(action_result=action_result)

        # Empty message to override last message of waiting
        self.send_progress('')
        if phantom.is_fail(status):
            return action_result.get_status()

        self.save_progress(MSONEDRIVE_CODE_RECEIVED_MSG)
        self._state = _load_app_state(self.get_asset_id(), self)

        # if code is not available in the state file
        if not self._state or not self._state.get(MSONEDRIVE_JSON_CODE):
            return action_result.set_status(phantom.APP_ERROR, status_message=MSONEDRIVE_TEST_CONNECTIVITY_FAILED_MSG)

        current_code = self._state[MSONEDRIVE_JSON_CODE]
        self.save_state(self._state)
        _save_app_state(self._state, self.get_asset_id(), self)

        self.save_progress(MSONEDRIVE_GENERATING_ACCESS_TOKEN_MSG)

        data = {
            MSONEDRIVE_CONFIG_CLIENT_ID: self._client_id,
            MSONEDRIVE_JSON_SCOPE: MSONEDRIVE_REST_REQUEST_SCOPE,
            MSONEDRIVE_CONFIG_CLIENT_SECRET: self._client_secret,
            MSONEDRIVE_JSON_GRANT_TYPE: 'authorization_code',
            MSONEDRIVE_JSON_REDIRECT_URI: redirect_uri,
            MSONEDRIVE_JSON_CODE: current_code
        }

        # For first time access, new access token is generated
        ret_val = self._generate_new_access_token(action_result=action_result, data=data)

        if phantom.is_fail(ret_val):
            self.send_progress('')
            self.save_progress(MSONEDRIVE_TEST_CONNECTIVITY_FAILED_MSG)
            return action_result.get_status()

        self.save_progress(MSONEDRIVE_CURRENT_USER_INFO_MSG)

        url = '{}{}'.format(MSONEDRIVE_MSGRAPH_API_BASE_URL, MSONEDRIVE_USER_INFO_ENDPOINT)
        ret_val, response = self._update_request(action_result=action_result, endpoint=url)

        if phantom.is_fail(ret_val):
            self.save_progress(MSONEDRIVE_TEST_CONNECTIVITY_FAILED_MSG)
            return action_result.get_status()

        self.save_progress(MSONEDRIVE_GOT_CURRENT_USER_INFO_MSG)
        self.save_progress(MSONEDRIVE_TEST_CONNECTIVITY_PASSED_MSG)
        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_get_file(self, param):
        """ This function is used to get a file and store it into vault.

        :param param: Dictionary of input parameters
        :return: status success/failure
        """
        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))

        action_result = self.add_action_result(ActionResult(dict(param)))

        summary = action_result.update_summary({})
        drive_id = self._handle_py_ver_compat_for_input_str(param.get(MSONEDRIVE_PARAM_DRIVE_ID, ""))
        file_id = self._handle_py_ver_compat_for_input_str(param.get(MSONEDRIVE_PARAM_FILE_ID, ""))
        file_path = self._handle_py_ver_compat_for_input_str(param.get(MSONEDRIVE_PARAM_FILE_PATH, ""))
        # Any one of the folder_id or folder_path is required to delete that folder
        if not file_id and not file_path:
            return action_result.set_status(phantom.APP_ERROR, MSONEDRIVE_MANDATORY_FILE_ID_OR_PATH_MSG)
        # Strip the folder path for leading and trailing forward and backward slashes if any present
        if file_path:
            file_path = file_path.strip('/\\')
        endpoint = ''
        if drive_id:
            if file_id:
                # Create url with folder_id
                endpoint = MSONEDRIVE_GET_FILE_DRIVE_FILE_ID.format(drive_id=drive_id, file_id=file_id)
            elif file_path:
                # Create url with folder_path
                endpoint = MSONEDRIVE_GET_FILE_DRIVE_FILE_PATH.format(drive_id=drive_id, file_path=file_path)
        else:
            if file_id:
                endpoint = MSONEDRIVE_GET_FILE_FILE_ID.format(file_id=file_id)
            elif file_path:
                endpoint = MSONEDRIVE_GET_FILE_FILE_PATH.format(file_path=file_path)

        # make rest call
        ret_val, response = self._update_request(action_result=action_result, endpoint=endpoint, method='get')

        if phantom.is_fail(ret_val):
            return action_result.get_status()

        # Get file_name & download_url
        filename = self._handle_py_ver_compat_for_input_str(response.get(MSONEDRIVE_JSON_PATH_NAME))
        download_url = response.get(MSONEDRIVE_JSON_PATH_DOWNLOAD_URL)

        if not filename or not download_url:
            return action_result.set_status(phantom.APP_ERROR, MSONEDRIVE_ERROR_FILE_NOT_EXIST_MSG)

        ret_val, response = self._make_rest_call_for_get_file(action_result=action_result, endpoint=download_url, method='get')

        if phantom.is_fail(ret_val):
            return action_result.get_status()

        temp_file_path = '{dir}{asset}_temp_get_file'.format(dir=self.get_state_dir(),
                                                             asset=self.get_asset_id())

        # If file size is zero then delete it and send a message : File has no content
        if not os.path.getsize(temp_file_path):
            # Delete file
            os.unlink(temp_file_path)
            self.debug_print(MSONEDRIVE_NO_DATA_FOUND_MSG)
            return action_result.set_status(phantom.APP_ERROR, status_message=MSONEDRIVE_NO_DATA_FOUND_MSG)
        # invalid_chars = '[]<>/\():;"\'|*()`~!@#$%^&={}?,'
        # Remove special character defined in invalid_chars from filename
        # filename = filename.translate(None, invalid_chars)
        # Replacing the file_name parameter with container_id parameter as
        # the Vault.get_file_info() does not handle URL characters on Phantom v4.8 Python v3

        # The phantom.get_file_info API is defunct. Using the vault_info API instead.
        try:
            success, message, vault_meta_info = ph_rules.vault_info(container_id=self.get_container_id())
            vault_meta_info = list(vault_meta_info)
            if not success or not vault_meta_info:
                error_msg = " Error Details: {}".format(unquote(message)) if message else ''
                return action_result.set_status(phantom.APP_ERROR, "{0},{1}".format(MSONEDRIVE_UNABLE_TO_RETREIVE_VAULT_ITEM_ERR_MSG, error_msg))
        except Exception as e:
            err = self._get_error_message_from_exception(e)
            return action_result.set_status(phantom.APP_ERROR, "{0},{1}".format(MSONEDRIVE_UNABLE_TO_RETREIVE_VAULT_ITEM_ERR_MSG, err))

        # Iterate through files of Vault
        for file in vault_meta_info:
            # If file name and file size are same file is duplicate
            if self._handle_py_ver_compat_for_input_str(file.get('name')) == filename and file.get('size') == os.path.getsize(temp_file_path):
                self.debug_print(MSONEDRIVE_FILE_ALREADY_AVAILABLE)
                vault_file_details = {
                    phantom.APP_JSON_SIZE: file.get('size'),
                    phantom.APP_JSON_VAULT_ID: file.get('vault_id'),
                    'file_name': filename
                }
                summary['vault_id'] = file.get('vault_id')
                # Delete temp file
                os.unlink(temp_file_path)
                action_result.add_data(vault_file_details)
                return action_result.set_status(phantom.APP_SUCCESS)

        vault_file_details = {phantom.APP_JSON_SIZE: os.path.getsize(temp_file_path)}

        # Adding file to vault
        vault_ret_dict = Vault.add_attachment(temp_file_path, container_id=self.get_container_id(),
            file_name=filename, metadata=vault_file_details)

        if not vault_ret_dict['succeeded']:
            self.debug_print(MSONEDRIVE_ADD_FILE_TO_VAULT_ERROR)
            return action_result.set_status(phantom.APP_ERROR, status_message=MSONEDRIVE_ADD_FILE_TO_VAULT_ERROR)

        vault_file_details[phantom.APP_JSON_VAULT_ID] = vault_ret_dict[phantom.APP_JSON_HASH]
        vault_file_details['file_name'] = filename
        action_result.add_data(vault_file_details)

        summary['vault_id'] = vault_file_details['vault_id']
        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_list_items(self, param):
        """ This function is used to handle list items action.

        :param param: Dictionary of input parameters
        :return: status(phantom.APP_SUCCESS/phantom.APP_ERROR)
        """

        list_files = []
        list_folders = []
        list_items = []
        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))
        action_result = self.add_action_result(ActionResult(dict(param)))

        drive_id = self._handle_py_ver_compat_for_input_str(param.get(MSONEDRIVE_PARAM_DRIVE_ID, ""))
        folder_id = self._handle_py_ver_compat_for_input_str(param.get(MSONEDRIVE_PARAM_FOLDER_ID, ""))
        folder_path = self._handle_py_ver_compat_for_input_str(param.get(MSONEDRIVE_PARAM_FOLDER_PATH, ""))

        # Strip the folder path for leading and trailing forward and backward slashes if any present
        if folder_path:
            folder_path = folder_path.strip('/\\')

        # 1. Default URL for fetching all items starting from the root folder of the default drive
        endpoint = MSONEDRIVE_LIST_ITEMS_DEFAULT_ENDPOINT

        if drive_id:
            if folder_id:
                endpoint = MSONEDRIVE_LIST_ITEMS_DRIVE_FOLDER_ID.format(drive_id=drive_id, folder_id=folder_id)
            elif folder_path:
                endpoint = MSONEDRIVE_LIST_ITEMS_DRIVE_FOLDER_PATH.format(drive_id=drive_id, folder_path=folder_path)
            else:
                endpoint = MSONEDRIVE_LIST_ITEMS_DRIVE_ID.format(drive_id=drive_id)
        else:
            if folder_id:
                endpoint = MSONEDRIVE_LIST_ITEMS_FOLDER_ID.format(folder_id=folder_id)
            elif folder_path:
                endpoint = MSONEDRIVE_LIST_ITEMS_FOLDER_PATH.format(folder_path=folder_path)

        # 2. Update global variable 'list_items' representing list of all items
        # within entire hierarchy based on given parameters of drive_id, folder_id and folder_path
        ret_val = self._get_list_items(endpoint, drive_id, action_result, list_files, list_folders, list_items)

        if phantom.is_fail(ret_val):
            return action_result.get_status()

        for item in list_items:
            # Split the parentReference data path to extract folder_path from it for contextual actions
            if item.get(MSONEDRIVE_JSON_PARENT_REFERENCE) and item.get(MSONEDRIVE_JSON_PARENT_REFERENCE).get(MSONEDRIVE_JSON_PATH):
                path_reference_body = item.get(MSONEDRIVE_JSON_PARENT_REFERENCE)
                full_path = path_reference_body.get(MSONEDRIVE_JSON_PATH)
                path_elements = full_path.split(MSONEDRIVE_JSON_ROOT_SPLIT)
                if len(path_elements) > 1:
                    path_reference_body[MSONEDRIVE_JSON_DRIVE_PATH] = '{}{}'.format(path_elements[0], MSONEDRIVE_JSON_ROOT_SPLIT)
                    path_reference_body[MSONEDRIVE_JSON_FOLDER_PATH] = path_elements[1].strip('/\\')
                else:
                    path_reference_body[MSONEDRIVE_JSON_DRIVE_PATH] = path_elements[0]
                    path_reference_body[MSONEDRIVE_JSON_FOLDER_PATH] = ""
                path_reference_body.pop(MSONEDRIVE_JSON_PATH, None)
                item[MSONEDRIVE_JSON_PARENT_REFERENCE] = path_reference_body

            action_result.add_data(item)

        summary = action_result.update_summary({})
        summary['total_items'] = action_result.get_data_size()

        return action_result.set_status(phantom.APP_SUCCESS)

    def _get_list_items(self, endpoint, drive_id, action_result, list_files, list_folders, list_items):
        """ This function is used to update global variables representing list of files, folders, and items
        based on given initial endpoint

        :param endpoint: Endpoint for initial item whose all children items are to be fetched
        :param drive_id: Drive ID
        :param action_result: action_result
        :param list_files: list of all children files
        :param list_folders: list of all children folders
        :param list_items: list of all children items (both files and folders)
        :return: list of items
        """

        # Below implementation follows the Depth First Search Algorithm for fetching all posts from all hierarchy
        # within the root node blog of a given site

        # 1. Fetch the children of current parent endpoint
        list_children = self._get_list_response(endpoint, action_result)

        if list_children is None:
            message = action_result.get_message()
            return action_result.set_status(phantom.APP_ERROR, "{0} {1}".format(message, MSONEDRIVE_LIST_ITEMS_FAILED_MSG))

        # 2. Update the global variables for all the child items and recursively
        # call the same function if child is a folder found at this hierarchy level
        for child in list_children:
            # If the child is a file
            if child.get(MSONEDRIVE_JSON_FILE):
                list_files.append(child)
                list_items.append(child)
                continue

            # If the child is a folder, reiterate to fetch further its children
            list_folders.append(child)
            list_items.append(child)
            if drive_id:
                endpoint = MSONEDRIVE_LIST_ITEMS_DRIVE_FOLDER_ID.format(drive_id=drive_id, folder_id=child.get(MSONEDRIVE_JSON_ID))
            else:
                endpoint = MSONEDRIVE_LIST_ITEMS_FOLDER_ID.format(folder_id=child.get(MSONEDRIVE_JSON_ID))
            ret_val = self._get_list_items(endpoint, drive_id, action_result, list_files, list_folders, list_items)

            if phantom.is_fail(ret_val):
                return action_result.get_status()

        return phantom.APP_SUCCESS

    def _get_list_response(self, url, action_result):
        """ This function is used to fetch list response based on API URL to be fetched,
        pagination and additional params.

        :rtype: list
        :param url: endpoint URL
        :param action_result: action_result
        :return: response list
        """
        response_items_list = []

        # Pagination for api calls
        while True:
            # make rest call
            ret_val, response = self._update_request(action_result=action_result, endpoint=url)

            if phantom.is_fail(ret_val):
                return None

            response_list = response.get(MSONEDRIVE_JSON_VALUE, {})
            response_items_list.extend(response_list)

            if not response.get(MSONEDRIVE_JSON_NEXT_LINK):
                break
            url = response[MSONEDRIVE_JSON_NEXT_LINK]

        return response_items_list

    def _handle_list_drive(self, param):
        """ This function is used to handle list dives action.

        :param param: No input parameter required
        :return: status(phantom.APP_SUCCESS/phantom.APP_ERROR)
        """

        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))

        # Add an action result object to self (BaseConnector) to represent the action for this param
        action_result = self.add_action_result(ActionResult(dict(param)))

        endpoint = '{}{}'.format(MSONEDRIVE_MSGRAPH_API_BASE_URL, MSONEDRIVE_LIST_DRIVES_ENDPOINT)

        list_drive = self._get_list_response(action_result=action_result, url=endpoint)

        if list_drive is None:
            message = action_result.get_message()
            return action_result.set_status(phantom.APP_ERROR, "{0} {1}".format(message, MSONEDRIVE_LIST_DRIVE_FAILED_MSG))

        # Add the response into the data section
        for drive in list_drive:
            action_result.add_data(drive)

        # Add a dictionary that is made up of the most important values from data into the summary
        summary = action_result.update_summary({})
        summary['total_drives'] = action_result.get_data_size()

        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_upload_file(self, param):
        """ This function is used to handle upload file action.

        :param param: Dictionary of input parameters
        :return: status(phantom.APP_SUCCESS/phantom.APP_ERROR)
        """

        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))
        action_result = self.add_action_result(ActionResult(dict(param)))

        vault_id = self._handle_py_ver_compat_for_input_str(param[MSONEDRIVE_PARAM_VAULT_ID])
        drive_id = self._handle_py_ver_compat_for_input_str(param.get(MSONEDRIVE_PARAM_DRIVE_ID, ""))
        file_path = self._handle_py_ver_compat_for_input_str(param[MSONEDRIVE_PARAM_FILE_PATH])
        auto_rename = param.get(MSONEDRIVE_PARAM_AUTO_RENAME, False)

        # Strip the file path for leading and trailing forward and backward slashes if any present
        if file_path:
            file_path = file_path.strip('/\\')

        # The phantom.get_file_info API is defunct. Using the vault_info API instead.

        try:
            success, message, vault_meta_info = ph_rules.vault_info(vault_id=vault_id)
            vault_meta_info = list(vault_meta_info)
            if not success or not vault_meta_info:
                error_msg = " Error Details: {}".format(unquote(message)) if message else ''
                return action_result.set_status(phantom.APP_ERROR, "{0},{1}".format(MSONEDRIVE_UNABLE_TO_RETREIVE_VAULT_ITEM_ERR_MSG, error_msg))
        except Exception as e:
            err = self._get_error_message_from_exception(e)
            return action_result.set_status(phantom.APP_ERROR, "{0},{1}".format(MSONEDRIVE_UNABLE_TO_RETREIVE_VAULT_ITEM_ERR_MSG, err))

        # Find vault path and file size for given vault ID
        vault_path = vault_meta_info[0].get('path')
        file_size = vault_meta_info[0].get(MSONEDRIVE_JSON_SIZE)

        # check if vault path is accessible
        if not vault_path:
            return action_result.set_status(phantom.APP_ERROR, MSONEDRIVE_VAULT_PATH_ABSENT_MSG)

        # check if vault info is accessible
        if not file_size:
            return action_result.set_status(phantom.APP_ERROR, MSONEDRIVE_VAULT_INFO_ABSENT_MSG)

        # Read the content of the file
        file_data = None
        try:
            with open(vault_path, 'rb') as fin:
                file_data = fin.read()
        except:
            return action_result.set_status(phantom.APP_ERROR, MSONEDRIVE_ERROR_READING_VAULT_FILE_MSG)
        finally:
            fin.close()

        # Session based API calls for uploading large files
        if drive_id:
            endpoint = MSONEDRIVE_CREATE_UPLOAD_SESSION_IF_DRIVE_ENDPOINT.format(drive_id=drive_id, file_path=file_path)
        else:
            endpoint = MSONEDRIVE_CREATE_UPLOAD_SESSION_NO_DRIVE_ENDPOINT.format(file_path=file_path)

        data = dict()
        inner_data = dict()
        if auto_rename:
            inner_data[MSONEDRIVE_JSON_CONFLICT_BEHAVIOR] = MSONEDRIVE_JSON_RENAME
        else:
            inner_data[MSONEDRIVE_JSON_CONFLICT_BEHAVIOR] = MSONEDRIVE_JSON_FAIL
        data[MSONEDRIVE_JSON_ITEM] = inner_data

        ret_val, session_response = self._update_request(action_result=action_result, endpoint=endpoint, data=json.dumps(data), method='post')

        if phantom.is_fail(ret_val):
            return action_result.get_status()

        # Upload URL and chunk size (max allowed in single chunk by OneDrive API : 60 MiB)
        # for uploading large files in equal chunk sizes using the pre-created session
        upload_url = session_response[MSONEDRIVE_JSON_UPLOAD_URL]
        chunk_size = 62914560
        content_length = 0

        if file_size <= chunk_size:
            content_length = file_size
        elif file_size > chunk_size:
            content_length = chunk_size
        chunk_start = 0
        content_range = 'bytes {}-{}/{}'.format(chunk_start,
                                                chunk_start + content_length - 1, file_size)
        chunk_cnt = 1

        while True:
            headers = {
                'Content-Length': str(content_length),
                'Content-Range': content_range
            }
            ret_val, resp_status = self._make_rest_call(action_result=action_result, endpoint=upload_url,
                headers=headers, data=file_data[chunk_start:(chunk_start + content_length)], method='put')

            if phantom.is_fail(ret_val):
                return action_result.get_status()

            resp_status_code = 201
            if resp_status.get(MSONEDRIVE_JSON_NEXT_EXPECTED_RANGES):
                resp_status_code = 202

            if resp_status_code == 201:
                # Split the parentReference data path to extract folder_path from it for contextual actions
                if resp_status.get(MSONEDRIVE_JSON_PARENT_REFERENCE) and resp_status.get(
                        MSONEDRIVE_JSON_PARENT_REFERENCE).get(MSONEDRIVE_JSON_PATH):
                    path_reference_body = resp_status.get(MSONEDRIVE_JSON_PARENT_REFERENCE)
                    full_path = path_reference_body.get(MSONEDRIVE_JSON_PATH)
                    path_elements = full_path.split(MSONEDRIVE_JSON_ROOT_SPLIT)
                    if len(path_elements) > 1:
                        path_reference_body[MSONEDRIVE_JSON_DRIVE_PATH] = '{}{}'.format(path_elements[0], MSONEDRIVE_JSON_ROOT_SPLIT)
                        path_reference_body[MSONEDRIVE_JSON_FOLDER_PATH] = path_elements[1].strip('/\\')
                    else:
                        path_reference_body[MSONEDRIVE_JSON_DRIVE_PATH] = path_elements[0]
                        path_reference_body[MSONEDRIVE_JSON_FOLDER_PATH] = ""
                    path_reference_body.pop(MSONEDRIVE_JSON_PATH, None)
                    resp_status[MSONEDRIVE_JSON_PARENT_REFERENCE] = path_reference_body

                action_result.add_data(resp_status)
                return action_result.set_status(phantom.APP_SUCCESS, MSONEDRIVE_UPLOAD_FILE_SUCCESSFUL_MSG)
            elif resp_status_code == 202:
                remaining_chunk = file_size - (chunk_cnt * chunk_size)
                if remaining_chunk <= chunk_size:
                    content_length = file_size - (chunk_cnt * chunk_size)
                    chunk_start = chunk_cnt * chunk_size
                    content_range = 'bytes {}-{}/{}'.format(
                        chunk_start, file_size - 1, file_size)
                    chunk_cnt = chunk_cnt + 1
                elif remaining_chunk > chunk_size:
                    content_length = chunk_size
                    chunk_start = chunk_cnt * chunk_size
                    content_range = 'bytes {}-{}/{}'.format(
                        chunk_start, chunk_start + content_length - 1, file_size)
                    chunk_cnt = chunk_cnt + 1
                continue
            else:
                return action_result.set_status(phantom.APP_ERROR, MSONEDRIVE_UPLOAD_FILE_FAILED_MSG)

        return action_result.set_status(phantom.APP_ERROR, MSONEDRIVE_UPLOAD_FILE_FAILED_MSG)

    def _handle_delete_file(self, param):
        """ This function is used to handle delete file action.

        :param param: Dictionary of input parameters
        :return: status(phantom.APP_SUCCESS/phantom.APP_ERROR)
        """

        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))

        # Add an action result object to self (BaseConnector) to represent the action for this param
        action_result = self.add_action_result(ActionResult(dict(param)))

        # Access action parameters passed in the 'param' dictionary
        id = self._handle_py_ver_compat_for_input_str(param.get('file_id', ''))
        drive_id = self._handle_py_ver_compat_for_input_str(param.get('drive_id', ''))
        path = self._handle_py_ver_compat_for_input_str(param.get('file_path', ''))

        if not id and not path:
            self.save_progress(MSONEDRIVE_MANDATORY_FILE_ID_OR_PATH_MSG)
            return action_result.set_status(phantom.APP_ERROR, MSONEDRIVE_MANDATORY_FILE_ID_OR_PATH_MSG)
        endpoint = ''

        if id and drive_id:
            endpoint = '{}{}'.format(MSONEDRIVE_MSGRAPH_API_BASE_URL, MSONEDRIVE_DELETE_FILE_ID_DRIVE_ID_ENDPOINT.format(
                drive_id=drive_id, file_id=id))
        elif id:
            endpoint = '{}{}'.format(MSONEDRIVE_MSGRAPH_API_BASE_URL, MSONEDRIVE_DELETE_FILE_ID_ENDPOINT.format(file_id=id))
        elif drive_id and path:
            endpoint = '{}{}'.format(MSONEDRIVE_MSGRAPH_API_BASE_URL, MSONEDRIVE_DELETE_FILE_DRIVE_ID_PATH_ENDPOINT.format(
                drive_id=drive_id, file_path=path))
        elif path:
            endpoint = '{}{}'.format(MSONEDRIVE_MSGRAPH_API_BASE_URL, MSONEDRIVE_DELETE_FILE_PATH_ENDPOINT.format(file_path=path))

        # make rest call
        ret_val, response = self._update_request(endpoint=endpoint, action_result=action_result, method='delete', headers=None)

        if phantom.is_fail(ret_val):
            # the call to the 3rd party device or service failed, action result should contain all the error details
            # for now the return is commented out, but after implementation, return from here
            return action_result.get_status()

        # Add the response into the data section
        action_result.add_data(response)

        # Return success, no need to set the message, only the status
        return action_result.set_status(phantom.APP_SUCCESS, MSONEDRIVE_DELETE_FILE_SUCCESS)

    def _handle_delete_folder(self, param):
        """ This function is used to handle delete folder action.

        :param param: Dictionary of input parameters
        :return: status(phantom.APP_SUCCESS/phantom.APP_ERROR)
        """

        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))
        action_result = self.add_action_result(ActionResult(dict(param)))

        drive_id = self._handle_py_ver_compat_for_input_str(param.get(MSONEDRIVE_PARAM_DRIVE_ID, ""))
        folder_id = self._handle_py_ver_compat_for_input_str(param.get(MSONEDRIVE_PARAM_FOLDER_ID, ""))
        folder_path = self._handle_py_ver_compat_for_input_str(param.get(MSONEDRIVE_PARAM_FOLDER_PATH, ""))

        # Any one of the folder_id or folder_path is required to delete that folder
        if not folder_id and not folder_path:
            return action_result.set_status(phantom.APP_ERROR, MSONEDRIVE_MANDATORY_FOLDER_ID_OR_PATH_MSG)

        # Strip the folder path for leading and trailing forward and backward slashes if any present
        if folder_path:
            folder_path = folder_path.strip('/\\')

        endpoint = ''
        if drive_id:
            if folder_id:
                endpoint = MSONEDRIVE_DELETE_FOLDER_DRIVE_FOLDER_ID.format(drive_id=drive_id, folder_id=folder_id)
            elif folder_path:
                endpoint = MSONEDRIVE_DELETE_FOLDER_DRIVE_FOLDER_PATH.format(drive_id=drive_id, folder_path=folder_path)
        else:
            if folder_id:
                endpoint = MSONEDRIVE_DELETE_FOLDER_FOLDER_ID.format(folder_id=folder_id)
            elif folder_path:
                endpoint = MSONEDRIVE_DELETE_FOLDER_FOLDER_PATH.format(folder_path=folder_path)

        ret_val, response = self._update_request(action_result=action_result, endpoint=endpoint, method='delete')

        if phantom.is_fail(ret_val):
            return action_result.get_status()

        return action_result.set_status(phantom.APP_SUCCESS, MSONEDRIVE_DELETE_FOLDER_SUCCESSFUL_MSG)

    def _handle_create_folder(self, param):
        """ This function is used to handle create folder action.

        :param param: Dictionary of input parameters
        :return: status(phantom.APP_SUCCESS/phantom.APP_ERROR)
        """

        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))
        action_result = self.add_action_result(ActionResult(dict(param)))

        drive_id = self._handle_py_ver_compat_for_input_str(param.get(MSONEDRIVE_PARAM_DRIVE_ID, ""))
        folder_id = self._handle_py_ver_compat_for_input_str(param.get(MSONEDRIVE_PARAM_FOLDER_ID, ""))
        folder_path = self._handle_py_ver_compat_for_input_str(param.get(MSONEDRIVE_PARAM_FOLDER_PATH, ""))
        auto_rename = param.get(MSONEDRIVE_PARAM_AUTO_RENAME, False)
        folder_name = self._handle_py_ver_compat_for_input_str(param[MSONEDRIVE_PARAM_FOLDER_NAME])

        # Strip the folder path for leading and trailing forward and backward slashes if any present
        if folder_path:
            folder_path = folder_path.strip('/\\')

        # 1. Default URL for creating folder starting from root folder of default drive
        endpoint = MSONEDRIVE_LIST_ITEMS_DEFAULT_ENDPOINT

        if drive_id:
            if folder_id:
                endpoint = MSONEDRIVE_LIST_ITEMS_DRIVE_FOLDER_ID.format(drive_id=drive_id, folder_id=folder_id)
            elif folder_path:
                endpoint = MSONEDRIVE_LIST_ITEMS_DRIVE_FOLDER_PATH.format(drive_id=drive_id, folder_path=folder_path)
            else:
                endpoint = MSONEDRIVE_LIST_ITEMS_DRIVE_ID.format(drive_id=drive_id)
        else:
            if folder_id:
                endpoint = MSONEDRIVE_LIST_ITEMS_FOLDER_ID.format(folder_id=folder_id)
            elif folder_path:
                endpoint = MSONEDRIVE_LIST_ITEMS_FOLDER_PATH.format(folder_path=folder_path)

        data = {
            MSONEDRIVE_JSON_NAME: folder_name,
            MSONEDRIVE_JSON_FOLDER: {},
        }
        if auto_rename:
            data.update({MSONEDRIVE_JSON_CONFLICT_BEHAVIOR: MSONEDRIVE_JSON_RENAME})

        ret_val, response = self._update_request(action_result=action_result, endpoint=endpoint, data=json.dumps(data), method='post')

        if phantom.is_fail(ret_val):
            return action_result.get_status()

        # Split the parentReference data path to extract folder_path from it for contextual actions
        if response.get(MSONEDRIVE_JSON_PARENT_REFERENCE) and response.get(MSONEDRIVE_JSON_PARENT_REFERENCE).get(MSONEDRIVE_JSON_PATH):
            path_reference_body = response.get(MSONEDRIVE_JSON_PARENT_REFERENCE)
            full_path = path_reference_body.get(MSONEDRIVE_JSON_PATH)
            path_elements = full_path.split(MSONEDRIVE_JSON_ROOT_SPLIT)
            if len(path_elements) > 1:
                path_reference_body[MSONEDRIVE_JSON_DRIVE_PATH] = '{}{}'.format(path_elements[0], MSONEDRIVE_JSON_ROOT_SPLIT)
                path_reference_body[MSONEDRIVE_JSON_FOLDER_PATH] = path_elements[1].strip('/\\')
            else:
                path_reference_body[MSONEDRIVE_JSON_DRIVE_PATH] = path_elements[0]
                path_reference_body[MSONEDRIVE_JSON_FOLDER_PATH] = ""
            path_reference_body.pop(MSONEDRIVE_JSON_PATH, None)
            response[MSONEDRIVE_JSON_PARENT_REFERENCE] = path_reference_body

        action_result.add_data(response)

        folder_created = folder_name
        if response.get(MSONEDRIVE_JSON_NAME):
            folder_created = response.get(MSONEDRIVE_JSON_NAME)

        return action_result.set_status(phantom.APP_SUCCESS, MSONEDRIVE_CREATE_FOLDER_SUCCESSFUL_MSG.format(
            folder_name=self._handle_py_ver_compat_for_input_str(folder_created)))

    def handle_action(self, param):
        """ This function gets current action identifier and calls member function of its own to handle the action.

        :param param: dictionary which contains information about the actions to be executed
        :return: status success/failure
        """

        self.debug_print("action_id", self.get_action_identifier())

        # Mapping each action with its corresponding method in Dictionary
        action_mapping = {
            'test_connectivity': self._handle_test_connectivity,
            'get_file': self._handle_get_file,
            'list_items': self._handle_list_items,
            'list_drive': self._handle_list_drive,
            'upload_file': self._handle_upload_file,
            'delete_file': self._handle_delete_file,
            'delete_folder': self._handle_delete_folder,
            'create_folder': self._handle_create_folder
        }

        action = self.get_action_identifier()
        action_execution_status = phantom.APP_SUCCESS

        if action in list(action_mapping.keys()):
            action_function = action_mapping[action]
            action_execution_status = action_function(param)

        return action_execution_status

    def initialize(self):
        """ This is an optional function that can be implemented by the AppConnector derived class. Since the
        configuration dictionary is already validated by the time this function is called, it's a good place to do any
        extra initialization of any internal modules. This function MUST return a value of either phantom.APP_SUCCESS or
        phantom.APP_ERROR. If this function returns phantom.APP_ERROR, then AppConnector::handle_action will not get
        called.
        """

        self._state = self.load_state()

        try:
            self._python_version = int(sys.version_info[0])
        except:
            return self.set_status(phantom.APP_ERROR, "Error occurred while getting the Phantom server's Python major version.")

        config = self.get_config()

        self._client_id = self._handle_py_ver_compat_for_input_str(config[MSONEDRIVE_CONFIG_CLIENT_ID])
        self._client_secret = config[MSONEDRIVE_CONFIG_CLIENT_SECRET]
        self._access_token = self._state.get(MSONEDRIVE_TOKEN_STRING, {}).get(MSONEDRIVE_ACCESS_TOKEN_STRING)
        self._refresh_token = self._state.get(MSONEDRIVE_TOKEN_STRING, {}).get(MSONEDRIVE_REFRESH_TOKEN_STRING)

        return phantom.APP_SUCCESS

    def finalize(self):
        """ This function gets called once all the param dictionary elements are looped over and no more handle_action
        calls are left to be made. It gives the AppConnector a chance to loop through all the results that were
        accumulated by multiple handle_action function calls and create any summary if required. Another usage is
        cleanup, disconnect from remote devices, etc.

        :return: status (success/failure)
        """

        # Save the state, this data is saved across actions and app upgrades
        self.save_state(self._state)
        _save_app_state(self._state, self.get_asset_id(), self)
        return phantom.APP_SUCCESS


if __name__ == '__main__':

    import argparse

    import pudb

    pudb.set_trace()

    argparser = argparse.ArgumentParser()

    argparser.add_argument('input_test_json', help='Input Test JSON file')
    argparser.add_argument('-u', '--username', help='username', required=False)
    argparser.add_argument('-p', '--password', help='password', required=False)
    argparser.add_argument('-v', '--verify', action='store_true', help='verify', required=False, default=False)

    args = argparser.parse_args()
    session_id = None

    username = args.username
    password = args.password
    verify = args.verify

    if username is not None and password is None:

        # User specified a username but not a password, so ask
        import getpass
        password = getpass.getpass("Password: ")

    if username and password:
        login_url = BaseConnector._get_phantom_base_url() + "login"
        try:
            print("Accessing the Login page")
            r = requests.get(login_url, verify=verify, timeout=DEFAULT_TIMEOUT)
            csrftoken = r.cookies['csrftoken']

            data = dict()
            data['username'] = username
            data['password'] = password
            data['csrfmiddlewaretoken'] = csrftoken

            headers = dict()
            headers['Cookie'] = 'csrftoken={0}'.format(csrftoken)
            headers['Referer'] = login_url

            print("Logging into Platform to get the session id")
            r2 = requests.post(login_url, verify=verify, timeout=DEFAULT_TIMEOUT, data=data, headers=headers)
            session_id = r2.cookies['sessionid']
        except Exception as e:
            print("Unable to get session id from the platform. Error: {0}".format(str(e)))
            sys.exit(1)

    with open(args.input_test_json) as f:
        in_json = f.read()
        in_json = json.loads(in_json)
        print(json.dumps(in_json, indent=4))

        connector = MicrosoftOnedriveConnector()
        connector.print_progress_message = True

        if session_id is not None:
            in_json['user_session_token'] = session_id
            connector._set_csrf_info(csrftoken, headers['Referer'])

        ret_val = connector._handle_action(json.dumps(in_json), None)
        print(json.dumps(json.loads(ret_val), indent=4))

    sys.exit(0)
