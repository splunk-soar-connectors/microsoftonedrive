# Microsoft OneDrive

Publisher: Splunk <br>
Connector Version: 3.1.0 <br>
Product Vendor: Microsoft <br>
Product Name: Microsoft OneDrive <br>
Minimum Product Version: 7.0.0

This app integrates with Microsoft OneDrive to execute various generic actions

## Authentication

This app supports two Microsoft Graph authentication methods.

- **Delegated** is the default and preserves the legacy browser-based OAuth flow. A user signs in
  to Microsoft during test connectivity, and actions run with the delegated permissions granted to
  that signed-in user.
- **Client Credentials** is non-interactive. The app uses the Azure application client secret to get
  an application token and runs actions against the configured target user.

## Create a Microsoft Azure application

Create an app registration in Microsoft Entra ID.

1. Go to <https://portal.azure.com>.
1. Open **Microsoft Entra ID**.
1. Open **App registrations** and select **New registration**.
1. Give the application a name.
1. Select the supported account type required by your environment. For delegated auth with the
   default `common` tenant behavior, use an account type that allows the users who will authorize the
   app.
1. Create a client secret under **Certificates & secrets** and keep the value available for the SOAR
   asset configuration.
1. Add Microsoft Graph API permissions for the authentication method you will use.

For **Delegated** auth, add delegated Microsoft Graph permissions for the actions you plan to run.
The legacy OneDrive connector requested the `files.readwrite.all` OAuth scope and the app commonly
uses these delegated permissions:

- Files.ReadWrite.All
- offline_access
- User.Read
- User.ReadWrite.All
- Group.ReadWrite.All

For **Client Credentials** auth, add Microsoft Graph **Application** permissions and grant admin
consent. The OneDrive actions require access to the configured target user's drive, so the app
registration must have application permissions that allow file access, such as:

- Files.ReadWrite.All

After adding or changing permissions, select **Grant admin consent** for the tenant.

## Configure delegated authentication

Use delegated authentication when you want the connector to behave like the legacy app.

1. Create or edit a Microsoft OneDrive asset in Splunk SOAR.
1. Set **Auth Method** to **Delegated** or leave it unset.
1. Set **Client ID** to the Azure application client ID.
1. Set **Client Secret** to the Azure application client secret.
1. Set **Tenant ID** only when you want to force authorization through a specific tenant. If omitted,
   the app uses `common`.
1. Enable webhooks for the asset.

The SDK app uses webhook routes for OAuth. The Microsoft redirect URI must point to the callback
route, not to the authorization-start route. During test connectivity, the app logs the callback URL
under **Using OAuth URL:**. Add that exact URL as a web redirect URI in the Azure application.

The callback URL commonly has this shape:

```text
https://<soar_host>:<webhook_port>/webhook/microsoftonedrive_<app_instance_id>/<asset_id>/oauth/callback
```

The app also logs a second URL under **Please authorize user in a separate tab using URL**. Open that
URL in a browser to start Microsoft authorization. That URL routes to the app's `oauth/start`
webhook, which redirects the browser to Microsoft. After Microsoft redirects back to `oauth/callback`
and the app receives the authorization code, test connectivity exchanges the code for a token and
verifies the token by calling Microsoft Graph.

## Configure client credentials authentication

Use client credentials authentication when browser interaction is not desired.

1. Create or edit a Microsoft OneDrive asset in Splunk SOAR.
1. Set **Auth Method** to **Client Credentials**.
1. Set **Client ID** to the Azure application client ID.
1. Set **Client Secret** to the Azure application client secret.
1. Set **Tenant ID** to the concrete tenant ID or tenant domain. Do not use `common` for client
   credentials.
1. Set **Target User ID** to the user principal name, email address, or Microsoft Graph user ID of
   the user whose OneDrive should be used when an action does not receive an explicit drive ID.

Client credentials test connectivity does not open a browser and does not use the OAuth webhook
routes. It gets an application token and verifies access by reading:

```text
/users/<target_user_id>/drive/root
```

## Action behavior by authentication method

Most action parameters are the same for both authentication methods.

In **Delegated** mode, actions use Microsoft Graph delegated routes such as `/me/drive`. The signed-in
Microsoft user determines which OneDrive data is available.

In **Client Credentials** mode, actions use the configured **Target User ID** when no explicit drive
ID is supplied. If an action receives a drive ID, it can address that drive directly.

For the **make request** action:

- Provide only a Microsoft Graph path, such as `/v1.0/me/drive/root` or
  `/v1.0/users/<user_id>/drive/root`. Do not include `https://graph.microsoft.com`.
- Use `/v1.0/me/...` for delegated auth.
- Use `/v1.0/users/<target_user_id>/...` or `/v1.0/drives/<drive_id>/...` for client credentials
  auth.

## OAuth state

The SDK app stores OAuth state through the SDK asset auth state. The legacy connector documented a
manual state file path and file permissions; that legacy state file path does not apply to normal
SDK app operation.

### Configuration variables

This table lists the configuration variables required to operate Microsoft OneDrive. These variables are specified when configuring a Microsoft OneDrive asset in Splunk SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**client_id** | required | string | Client ID |
**client_secret** | required | password | Client secret |
**tenant_id** | optional | string | Tenant ID |
**auth_method** | optional | string | Authentication method |
**target_user_id** | optional | string | User ID or user principal name for client credentials mode |

### Supported Actions

[test connectivity](#action-test-connectivity) - test connectivity <br>
[make request](#action-make-request) - Make an arbitrary Microsoft Graph request using this asset's authentication. <br>
[get file](#action-get-file) - Download a file from server and add it to the vault <br>
[list items](#action-list-items) - List of items <br>
[list drive](#action-list-drive) - List of Drives <br>
[search file](#action-search-file) - Search for files or folders by name or content <br>
[upload file](#action-upload-file) - Upload file <br>
[delete file](#action-delete-file) - Delete file <br>
[delete folder](#action-delete-folder) - Delete a folder <br>
[create folder](#action-create-folder) - Create a folder

## action: 'test connectivity'

test connectivity

Type: **test** <br>
Read only: **True**

Basic test for app.

#### Action Parameters

No parameters are required for this action

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'make request'

Make an arbitrary Microsoft Graph request using this asset's authentication.

Type: **generic** <br>
Read only: **False**

'make request' action for the app. Used to handle arbitrary HTTP requests with the app's asset

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**http_method** | required | The HTTP method to use for the request. | string | |
**endpoint** | required | Microsoft Graph endpoint to call, appended to the API base URL. Example: '/v1.0/me/drive/root' or '/beta/users/{id}/drive/root' | string | |
**headers** | optional | The headers to send with the request (JSON object). An example is {'Content-Type': 'application/json'} | string | |
**query_parameters** | optional | Parameters to append to the URL (JSON object or query string). An example is ?key=value&key2=value2 | string | |
**body** | optional | The body to send with the request (JSON object). An example is {'key': 'value', 'key2': 'value2'} | string | |
**timeout** | optional | The timeout for the request in seconds. | numeric | |
**verify_ssl** | optional | Whether to verify the SSL certificate. | boolean | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.http_method | string | | |
action_result.parameter.endpoint | string | | |
action_result.parameter.headers | string | | |
action_result.parameter.query_parameters | string | | |
action_result.parameter.body | string | | |
action_result.parameter.timeout | numeric | | |
action_result.parameter.verify_ssl | boolean | | |
action_result.data.\*.status_code | numeric | | 200 404 500 |
action_result.data.\*.response_body | string | | {"key": "value"} |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'get file'

Download a file from server and add it to the vault

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**file_id** | optional | ID of file | string | `msonedrive file id` |
**drive_id** | optional | Drive ID | string | `msonedrive drive id` |
**file_path** | optional | Path of file | string | `file path` |
**force_infected_download** | optional | Download a file that Microsoft has flagged as infected by sending the Prefer: forceInfectedDownload header | boolean | |
**target_user_id** | optional | User ID or user principal name that overrides the asset Target User ID for this action in Client Credentials mode | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.file_id | string | `msonedrive file id` | |
action_result.parameter.drive_id | string | `msonedrive drive id` | |
action_result.parameter.file_path | string | `file path` | |
action_result.parameter.force_infected_download | boolean | | |
action_result.parameter.target_user_id | string | | |
action_result.data.\*.file_name | string | | filetxt.txt |
action_result.data.\*.vault_id | string | `vault id` | example-vault-id |
action_result.data.\*.size | numeric | `file size` | 4 |
action_result.data.\*.force_infected_download | boolean | | True False |
action_result.data.\*.malware_flagged | boolean | | True False |
action_result.summary.vault_id | string | `vault id` | example-vault-id |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'list items'

List of items

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**drive_id** | optional | Parent drive ID | string | `msonedrive drive id` |
**folder_id** | optional | Parent folder ID | string | `msonedrive folder id` |
**folder_path** | optional | Parent folder path | string | `msonedrive folder path` |
**max_results** | optional | Maximum number of items to return, capped at 200 | numeric | |
**target_user_id** | optional | User ID or user principal name that overrides the asset Target User ID for this action in Client Credentials mode | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.drive_id | string | `msonedrive drive id` | |
action_result.parameter.folder_id | string | `msonedrive folder id` | |
action_result.parameter.folder_path | string | `msonedrive folder path` | |
action_result.parameter.max_results | numeric | | |
action_result.parameter.target_user_id | string | | |
action_result.data.\*.drive_id | string | `msonedrive drive id` | example-drive-id |
action_result.data.\*.folder_id | string | `msonedrive folder id` | example-folder-id |
action_result.data.\*.folder_path | string | `msonedrive folder path` | Test/child |
action_result.data.\*.@microsoft.graph.downloadUrl | string | `url` | https://test-my.abc.com/test/test_xyz_com/\_layouts/00/download.aspx?UniqueId=test&ApiVersion=2.0 |
action_result.data.\*.cTag | string | | "c:{2test123-1234-1234-1234-test123test1},0" |
action_result.data.\*.createdBy.application.displayName | string | | Test_One-drive |
action_result.data.\*.createdBy.application.id | string | | ba56002c-856c-469f-b6a0-a4335614c502 |
action_result.data.\*.createdBy.user.displayName | string | `user name` | Test User |
action_result.data.\*.createdBy.user.email | string | `email` | test@test.xyz.com |
action_result.data.\*.createdBy.user.id | string | | 17be00d0-35ed-4881-ab62-d2eb73c2ebe3 |
action_result.data.\*.createdDateTime | string | | 2018-09-01T09:21:24Z |
action_result.data.\*.currentUserRole.blocksDownload | boolean | | True False |
action_result.data.\*.currentUserRole.readOnly | boolean | | True False |
action_result.data.\*.eTag | string | | "{2test123-1234-1234-1234-test123test1},1" |
action_result.data.\*.file.hashes.quickXorHash | string | | fio2VWDQgVGaX34LXedeos6Y6/s= |
action_result.data.\*.file.mimeType | string | | image/png |
action_result.data.\*.fileSystemInfo.createdDateTime | string | | 2018-09-01T09:21:24Z |
action_result.data.\*.fileSystemInfo.lastModifiedDateTime | string | | 2018-09-01T09:21:24Z |
action_result.data.\*.folder.childCount | numeric | | 17 |
action_result.data.\*.id | string | `msonedrive file id` `msonedrive folder id` | 01TEST123TEST123TEST123U3KTTEST123 |
action_result.data.\*.image.height | numeric | | 183 |
action_result.data.\*.image.width | numeric | | 275 |
action_result.data.\*.lastModifiedBy.application.displayName | string | | Test_One-drive |
action_result.data.\*.lastModifiedBy.application.id | string | | ba56002c-856c-469f-b6a0-a4335614c502 |
action_result.data.\*.lastModifiedBy.user.displayName | string | `user name` | Test User |
action_result.data.\*.lastModifiedBy.user.email | string | `email` | test@test.xyz.com |
action_result.data.\*.lastModifiedBy.user.id | string | | 17be00d0-35ed-4881-ab62-d2eb73c2ebe3 |
action_result.data.\*.lastModifiedDateTime | string | | 2018-09-01T10:37:09Z |
action_result.data.\*.name | string | | test file |
action_result.data.\*.package.type | string | | oneNote |
action_result.data.\*.parentReference.driveId | string | `msonedrive drive id` | example-drive-id |
action_result.data.\*.parentReference.drivePath | string | | /drive/root:/ |
action_result.data.\*.parentReference.driveType | string | | business |
action_result.data.\*.parentReference.folderPath | string | `msonedrive folder path` | Test/child |
action_result.data.\*.parentReference.id | string | `msonedrive drive id` `msonedrive folder id` | example-parent-reference-id |
action_result.data.\*.size | numeric | `file size` | 359666 |
action_result.data.\*.webUrl | string | `url` | https://test-my.test.com/personal/test_abc_com/Documents/Test |
action_result.summary.total_items | numeric | | |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'list drive'

List of Drives

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**target_user_id** | optional | User ID or user principal name that overrides the asset Target User ID for this action in Client Credentials mode | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.target_user_id | string | | |
action_result.data.\*.name | string | | OneDrive |
action_result.data.\*.driveType | string | | business |
action_result.data.\*.id | string | `msonedrive drive id` | b!test123_TESTzTEST123faTEST123LTEST-7TEST123-MTEST123RJQb3TEST123 |
action_result.data.\*.owner.user.displayName | string | `user name` | Test User |
action_result.data.\*.owner.user.email | string | `email` | test@test.abc.com |
action_result.data.\*.owner.user.id | string | | 17be76d0-35ed-4881-ab62-d2eb73c2ebe3 |
action_result.data.\*.lastModifiedDateTime | string | | 2018-09-21T05:40:10Z |
action_result.data.\*.lastModifiedBy.user.displayName | string | `user name` | Test User |
action_result.data.\*.lastModifiedBy.user.email | string | `email` | test@test.abc.com |
action_result.data.\*.lastModifiedBy.user.id | string | | 17be76d0-35ed-4881-ab62-d2eb73c2ebe3 |
action_result.data.\*.createdDateTime | string | | 2018-09-04T01:34:10Z |
action_result.data.\*.createdBy.user.displayName | string | `user name` | Test User |
action_result.data.\*.createdBy.user.email | string | `email` | test@test.abc.com |
action_result.data.\*.createdBy.user.id | string | | 17be76d0-35ed-4881-ab62-d2eb73c2ebe3 |
action_result.data.\*.webUrl | string | `url` | https://test-my.abc.com/personal/test_test_xyz_com/Documents |
action_result.data.\*.description | string | | |
action_result.data.\*.quota.deleted | numeric | | 2555167314 |
action_result.data.\*.quota.remaining | numeric | | 1097114685696 |
action_result.data.\*.quota.state | string | | normal |
action_result.data.\*.quota.total | numeric | | 1099511627776 |
action_result.data.\*.quota.used | numeric | | 355597522 |
action_result.summary.total_drives | numeric | | 1 |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'search file'

Search for files or folders by name or content

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**search_text** | required | Text to search for in file or folder names and content | string | |
**drive_id** | optional | Drive ID | string | `msonedrive drive id` |
**folder_id** | optional | Folder ID to limit search scope | string | `msonedrive folder id` |
**max_results** | optional | Maximum number of matching items to return, capped at 200 | numeric | |
**fallback_to_filename_scan** | optional | In Client Credentials mode, recursively scan file and folder names when Microsoft Graph search is forbidden or returns no results. The scan stops after 100 Microsoft Graph requests | boolean | |
**target_user_id** | optional | User ID or user principal name that overrides the asset Target User ID for this action in Client Credentials mode | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.search_text | string | | |
action_result.parameter.drive_id | string | `msonedrive drive id` | |
action_result.parameter.folder_id | string | `msonedrive folder id` | |
action_result.parameter.max_results | numeric | | |
action_result.parameter.fallback_to_filename_scan | boolean | | |
action_result.parameter.target_user_id | string | | |
action_result.data.\*.drive_id | string | `msonedrive drive id` | example-drive-id |
action_result.data.\*.is_folder | boolean | | True False |
action_result.data.\*.@microsoft.graph.downloadUrl | string | `url` | https://test-my.abc.com/test/test_xyz_com/\_layouts/00/download.aspx?UniqueId=test&ApiVersion=2.0 |
action_result.data.\*.createdBy.application.displayName | string | | Test_One-drive |
action_result.data.\*.createdBy.application.id | string | | ba56002c-856c-469f-b6a0-a4335614c502 |
action_result.data.\*.createdBy.user.displayName | string | `user name` | Test User |
action_result.data.\*.createdBy.user.email | string | `email` | test@test.xyz.com |
action_result.data.\*.createdBy.user.id | string | | 17be00d0-35ed-4881-ab62-d2eb73c2ebe3 |
action_result.data.\*.createdDateTime | string | | 2018-09-01T09:21:24Z |
action_result.data.\*.file.hashes.quickXorHash | string | | fio2VWDQgVGaX34LXedeos6Y6/s= |
action_result.data.\*.file.hashes.sha1Hash | string | | example-sha1 |
action_result.data.\*.file.hashes.sha256Hash | string | | example-sha256 |
action_result.data.\*.file.mimeType | string | | image/png |
action_result.data.\*.folder.childCount | numeric | | 17 |
action_result.data.\*.id | string | `msonedrive file id` `msonedrive folder id` | 01TEST123TEST123TEST123U3KTTEST123 |
action_result.data.\*.lastModifiedBy.application.displayName | string | | Test_One-drive |
action_result.data.\*.lastModifiedBy.application.id | string | | ba56002c-856c-469f-b6a0-a4335614c502 |
action_result.data.\*.lastModifiedBy.user.displayName | string | `user name` | Test User |
action_result.data.\*.lastModifiedBy.user.email | string | `email` | test@test.xyz.com |
action_result.data.\*.lastModifiedBy.user.id | string | | 17be00d0-35ed-4881-ab62-d2eb73c2ebe3 |
action_result.data.\*.lastModifiedDateTime | string | | 2018-09-01T10:37:09Z |
action_result.data.\*.name | string | | test file |
action_result.data.\*.parentReference.driveId | string | `msonedrive drive id` | example-drive-id |
action_result.data.\*.parentReference.driveType | string | | business |
action_result.data.\*.parentReference.id | string | `msonedrive drive id` `msonedrive folder id` | example-parent-reference-id |
action_result.data.\*.parentReference.path | string | | /drive/root:/Test |
action_result.data.\*.size | numeric | `file size` | 359666 |
action_result.data.\*.webUrl | string | `url` | https://test-my.test.com/personal/test_abc_com/Documents/Test |
action_result.summary.total_items_found | numeric | | 1 |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'upload file'

Upload file

Type: **generic** <br>
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**drive_id** | optional | Parent drive ID | string | `msonedrive drive id` |
**vault_id** | required | Vault ID | string | `vault id` `sha1` |
**file_path** | required | File path with file name | string | `file path` |
**auto_rename** | optional | Auto rename file | boolean | |
**target_user_id** | optional | User ID or user principal name that overrides the asset Target User ID for this action in Client Credentials mode | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.drive_id | string | `msonedrive drive id` | |
action_result.parameter.vault_id | string | `vault id` `sha1` | |
action_result.parameter.file_path | string | `file path` | |
action_result.parameter.auto_rename | boolean | | |
action_result.parameter.target_user_id | string | | |
action_result.data.\*.@content.downloadUrl | string | `url` | https://test-my.abc.com/test/test_xyz_com/\_layouts/00/download.aspx?UniqueId=test&ApiVersion=2.0 |
action_result.data.\*.@odata.context | string | `url` | https://test-my.abc.com/personal/test_abc_com/\_api/v2.0/$metadata#items/$entity |
action_result.data.\*.@odata.editLink | string | | drives/b!gy8xtu3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q/items/01FMDEUQ532OAQOAAUFVCL6MDY7H3CUEKN |
action_result.data.\*.@odata.id | string | `url` | https://test-my.abc.com/personal/test_abc_com/\_api/v2.0/drives/b!test123_TESTzTEST123faTEST123LTEST-7TEST123-MTEST123RJQb3TEST123/items/01TEST123TEST123TEST123U3KTTEST123 |
action_result.data.\*.@odata.type | string | | #oneDrive.item |
action_result.data.\*.file.irmEnabled | boolean | | True False |
action_result.data.\*.file.hashes.quickXorHash | string | | AAAAAAAAAAAAAAAAAIwPCgAAAAA= |
action_result.data.\*.file.mimeType | string | | text/plain |
action_result.data.\*.cTag | string | | "c:{2test123-1234-1234-1234-test123test1},2" |
action_result.data.\*.createdBy.application.displayName | string | | Test_One-drive |
action_result.data.\*.createdBy.application.id | string | | ba56122c-856c-469f-b6a0-a4335614c502 |
action_result.data.\*.createdBy.user.displayName | string | `user name` | Test User |
action_result.data.\*.createdBy.user.email | string | `email` | test@test.xyz.com |
action_result.data.\*.createdBy.user.id | string | | 17be76d0-35ed-4881-ab62-d2eb73c2ebe3 |
action_result.data.\*.createdDateTime | string | | 2018-09-21T12:22:02Z |
action_result.data.\*.eTag | string | | "{2test123-1234-1234-1234-test123test1},3" |
action_result.data.\*.fileSystemInfo.createdDateTime | string | | 2018-09-01T12:22:02Z |
action_result.data.\*.fileSystemInfo.lastModifiedDateTime | string | | 2018-09-01T12:23:03Z |
action_result.data.\*.id | string | `msonedrive file id` | 01TEST123TEST123TEST123U3KTTEST123 |
action_result.data.\*.lastModifiedBy.application.displayName | string | | Test_One-drive |
action_result.data.\*.lastModifiedBy.application.id | string | | ba56122c-856c-469f-b6a0-a4335614c502 |
action_result.data.\*.lastModifiedBy.user.displayName | string | `user name` | Test User |
action_result.data.\*.lastModifiedBy.user.email | string | `email` | test@test.xyz.com |
action_result.data.\*.lastModifiedBy.user.id | string | | 17be76d0-35ed-4881-ab62-d2eb73c2ebe3 |
action_result.data.\*.lastModifiedDateTime | string | | 2018-09-01T12:23:03Z |
action_result.data.\*.name | string | | test135 3.txt |
action_result.data.\*.parentReference.driveId | string | `msonedrive drive id` | b!gy8xtu3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q |
action_result.data.\*.parentReference.drivePath | string | | /drives/b!test123_TESTzTEST123faTEST123LTEST-7TEST123-MTEST123RJQb3TEST123/root:/ |
action_result.data.\*.parentReference.driveType | string | | business |
action_result.data.\*.parentReference.folderPath | string | `msonedrive folder path` | TestParent/child |
action_result.data.\*.parentReference.id | string | `msonedrive drive id` `msonedrive folder id` | 01FMDEUQZDNXCWNB3JIZCIM2A27DHROBE2 |
action_result.data.\*.size | numeric | `file size` | 168791040 |
action_result.data.\*.webUrl | string | `url` | https://test-my.TEST.com/personal/test_xyz_com/Documents/Test/abc135%203.txt |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'delete file'

Delete file

Type: **generic** <br>
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**file_id** | optional | File id | string | `msonedrive file id` |
**drive_id** | optional | Drive id | string | `msonedrive drive id` |
**file_path** | optional | Path of file | string | `file path` |
**target_user_id** | optional | User ID or user principal name that overrides the asset Target User ID for this action in Client Credentials mode | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.file_id | string | `msonedrive file id` | |
action_result.parameter.drive_id | string | `msonedrive drive id` | |
action_result.parameter.file_path | string | `file path` | |
action_result.parameter.target_user_id | string | | |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'delete folder'

Delete a folder

Type: **generic** <br>
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**drive_id** | optional | Parent drive ID | string | `msonedrive drive id` |
**folder_id** | optional | Folder ID | string | `msonedrive folder id` |
**folder_path** | optional | Folder path | string | `msonedrive folder path` |
**target_user_id** | optional | User ID or user principal name that overrides the asset Target User ID for this action in Client Credentials mode | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.drive_id | string | `msonedrive drive id` | |
action_result.parameter.folder_id | string | `msonedrive folder id` | |
action_result.parameter.folder_path | string | `msonedrive folder path` | |
action_result.parameter.target_user_id | string | | |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'create folder'

Create a folder

Type: **generic** <br>
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**drive_id** | optional | Parent drive ID | string | `msonedrive drive id` |
**folder_id** | optional | Parent folder ID | string | `msonedrive folder id` |
**folder_path** | optional | Parent folder path | string | `msonedrive folder path` |
**folder_name** | required | Folder name | string | `msonedrive folder name` |
**auto_rename** | optional | Auto rename folder | boolean | |
**target_user_id** | optional | User ID or user principal name that overrides the asset Target User ID for this action in Client Credentials mode | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.drive_id | string | `msonedrive drive id` | |
action_result.parameter.folder_id | string | `msonedrive folder id` | |
action_result.parameter.folder_path | string | `msonedrive folder path` | |
action_result.parameter.folder_name | string | `msonedrive folder name` | |
action_result.parameter.auto_rename | boolean | | |
action_result.parameter.target_user_id | string | | |
action_result.data.\*.parentReference.driveId | string | `msonedrive drive id` | b!gy8txu3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q |
action_result.data.\*.parentReference.drivePath | string | | /drives/b!test123_TESTzTEST123faTEST123LTEST-7TEST123-MTEST123RJQb3TEST123/root:/ |
action_result.data.\*.parentReference.driveType | string | | business |
action_result.data.\*.parentReference.folderPath | string | `msonedrive folder path` | Test |
action_result.data.\*.parentReference.id | string | `msonedrive drive id` `msonedrive folder id` | 01FMDUEQY3MRPCRFEYX5FJPU3KT7J24LJB |
action_result.data.\*.id | string | `msonedrive folder id` | 01TEST123TEST123TEST123U3KTTEST123 |
action_result.data.\*.name | string | `msonedrive folder name` | Test_1 1 |
action_result.data.\*.webUrl | string | `url` | https://test-my.test.com/personal/test_xyz_com/Documents/Test/Test_1%201 |
action_result.data.\*.size | numeric | `file size` | 0 |
action_result.data.\*.createdBy.application.displayName | string | | Test_One-drive |
action_result.data.\*.createdBy.application.id | string | | ba56002c-856c-469f-b6a0-a4335614c502 |
action_result.data.\*.createdBy.user.displayName | string | `user name` | Test User |
action_result.data.\*.createdBy.user.email | string | `email` | test@test.xyz.com |
action_result.data.\*.createdBy.user.id | string | | 17be00d0-35ed-4881-ab62-d2eb73c2ebe3 |
action_result.data.\*.createdDateTime | string | | 2018-09-01T08:49:18Z |
action_result.data.\*.@odata.context | string | `url` | https://abc.test.com/v1.0/$metadata#users(01TEST123TEST123TEST123U3KTTEST123)/drive/items(01TEST123TEST123TEST123U3KTTEST123)/children/$entity |
action_result.data.\*.cTag | string | | "c:{2test123-1234-1234-1234-test123test1},0" |
action_result.data.\*.eTag | string | | "{2test123-1234-1234-1234-test123test1},1" |
action_result.data.\*.fileSystemInfo.createdDateTime | string | | 2018-09-01T08:49:18Z |
action_result.data.\*.fileSystemInfo.lastModifiedDateTime | string | | 2018-09-01T08:49:18Z |
action_result.data.\*.folder.childCount | numeric | | 0 |
action_result.data.\*.lastModifiedBy.application.displayName | string | | Test_One-drive |
action_result.data.\*.lastModifiedBy.application.id | string | | ba56002c-856c-469f-b6a0-a4335614c502 |
action_result.data.\*.lastModifiedBy.user.displayName | string | `user name` | Test User |
action_result.data.\*.lastModifiedBy.user.email | string | `email` | test@test.xyz.com |
action_result.data.\*.lastModifiedBy.user.id | string | | 17be00d0-35ed-4881-ab62-d2eb73c2ebe3 |
action_result.data.\*.lastModifiedDateTime | string | | 2018-09-01T08:49:18Z |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

______________________________________________________________________

Auto-generated Splunk SOAR Connector documentation.

Copyright 2026 Splunk Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.
