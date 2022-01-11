[comment]: # "Auto-generated SOAR connector documentation"
# Microsoft OneDrive

Publisher: Splunk  
Connector Version: 2\.2\.4  
Product Vendor: Microsoft  
Product Name: Microsoft OneDrive  
Product Version Supported (regex): "\.\*"  
Minimum Product Version: 4\.9\.39220  

This app integrates with Microsoft OneDrive to execute various generic actions

[comment]: # " File: readme.md"
[comment]: # "  Copyright (c) 2019-2022 Splunk Inc."
[comment]: # ""
[comment]: # "Licensed under the Apache License, Version 2.0 (the 'License');"
[comment]: # "you may not use this file except in compliance with the License."
[comment]: # "You may obtain a copy of the License at"
[comment]: # ""
[comment]: # "    http://www.apache.org/licenses/LICENSE-2.0"
[comment]: # ""
[comment]: # "Unless required by applicable law or agreed to in writing, software distributed under"
[comment]: # "the License is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,"
[comment]: # "either express or implied. See the License for the specific language governing permissions"
[comment]: # "and limitations under the License."
[comment]: # ""
## Authentication

This app requires creating a Microsoft Azure Application. To do so, navigate to
<https://portal.azure.com> in a browser and log in with a Microsoft account, then select **Azure
Active Directory** .

1.  Go to **App Registrations** and click on **+ New registration** .
2.  Give the app an appropriate name. The Redirect URI will be populated in a later step.
3.  Select a supported account type (configure the application to be multitenant).
4.  Click on the **Register** .
    -   Under **Certificates & secrets** , add **New client secret** . Note this key somewhere
        secure, as it cannot be retrieved after closing the window.
    -   Under **Authentication** , add the **Redirect URIs** field which will be filled in a later
        step.
    -   Under **API Permissions** , click on **Add a permission** .
    -   Go to **Microsoft Graph Permissions** , the following **Delegated Permissions** need to be
        added:
        -   Group.ReadWrite.All
        -   offline_access
        -   User.ReadWrite.All
    -   Click on the **Add permissions** .

After making these changes, click on **Grant admin consent** .

## Configure the Microsoft OneDrive Phantom app Asset

When creating an asset for the **Microsoft OneDrive** app, place the **Application ID** of the app
created during the previous step in the **Client ID** field and place the password generated during
the app creation process in the **Client Secret** field. Then, click **SAVE** .  
  
After saving, a new field will appear in the **Asset Settings** tab. Take the URL found in the
**POST incoming for Microsoft OneDrive to this location** field and place it in the **Redirect
URIs** field mentioned in a previous step. To this URL, add **/result** . After doing so the URL
should look something like:  
  

https://\<phantom_host>/rest/handler/microsoftonedrive_564fe3f1-b1bb-4196-ba52-9422d0e4d430/\<asset_name>/result

  
Once again, click on Save.

## Method to Run Test Connectivity

After setting up the asset and user, click the **TEST CONNECTIVITY** button. A window should pop up
and display a URL. Navigate to this URL in a separate browser tab. This new tab will redirect to a
Microsoft login page. Log in to a Microsoft account. After logging in, review the requested
permissions listed, then click **Accept** . Finally, close that tab. The test connectivity window
should show a success.  
  
The app should now be ready to use.

## State File Permissions

Please check the permissions for the state file as mentioned below.

#### State Filepath

-   For Non-NRI Instance:
    /opt/phantom/local_data/app_states/a73f6d32-c9d5-4fec-b024-43876700daa6/{asset_id}\_state.json
-   For NRI Instance:
    /\<PHANTOM_HOME_DIRECTORY>/local_data/app_states/a73f6d32-c9d5-4fec-b024-43876700daa6/{asset_id}\_state.json

#### State File Permissions

-   File Rights: rw-rw-r-- (664) (The phantom user should have read and write access for the state
    file)
-   File Owner: appropriate phantom user


### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a Microsoft OneDrive asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**client\_id** |  required  | string | Client ID
**client\_secret** |  required  | password | Client secret

### Supported Actions  
[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity using supplied configuration  
[get file](#action-get-file) - Download a file from server and add it to the vault  
[list items](#action-list-items) - List of items  
[list drive](#action-list-drive) - List of Drives  
[upload file](#action-upload-file) - Upload file  
[delete file](#action-delete-file) - Delete file  
[delete folder](#action-delete-folder) - Delete a folder  
[create folder](#action-create-folder) - Create a folder  

## action: 'test connectivity'
Validate the asset configuration for connectivity using supplied configuration

Type: **test**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
No Output  

## action: 'get file'
Download a file from server and add it to the vault

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**file\_id** |  optional  | ID of file | string |  `msonedrive file id` 
**drive\_id** |  optional  | Drive ID | string |  `msonedrive drive id` 
**file\_path** |  optional  | Path of file | string |  `file path` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.drive\_id | string |  `msonedrive drive id` 
action\_result\.parameter\.file\_id | string |  `msonedrive file id` 
action\_result\.parameter\.file\_path | string |  `file path` 
action\_result\.data | string | 
action\_result\.data\.\*\.file\_name | string | 
action\_result\.data\.\*\.size | numeric |  `file size` 
action\_result\.data\.\*\.vault\_id | string |  `vault id` 
action\_result\.summary\.vault\_id | string |  `vault id` 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'list items'
List of items

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**drive\_id** |  optional  | Parent drive ID | string |  `msonedrive drive id` 
**folder\_id** |  optional  | Parent folder ID | string |  `msonedrive folder id` 
**folder\_path** |  optional  | Parent folder path | string |  `msonedrive folder path` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.drive\_id | string |  `msonedrive drive id` 
action\_result\.parameter\.folder\_id | string |  `msonedrive folder id` 
action\_result\.parameter\.folder\_path | string |  `msonedrive folder path` 
action\_result\.data\.\*\.\@microsoft\.graph\.downloadUrl | string |  `url` 
action\_result\.data\.\*\.cTag | string | 
action\_result\.data\.\*\.createdBy\.application\.displayName | string | 
action\_result\.data\.\*\.createdBy\.application\.id | string | 
action\_result\.data\.\*\.createdBy\.user\.displayName | string |  `user name` 
action\_result\.data\.\*\.createdBy\.user\.email | string |  `email` 
action\_result\.data\.\*\.createdBy\.user\.id | string | 
action\_result\.data\.\*\.createdDateTime | string | 
action\_result\.data\.\*\.currentUserRole\.blocksDownload | boolean | 
action\_result\.data\.\*\.currentUserRole\.readOnly | boolean | 
action\_result\.data\.\*\.eTag | string | 
action\_result\.data\.\*\.file\.hashes\.quickXorHash | string | 
action\_result\.data\.\*\.file\.mimeType | string | 
action\_result\.data\.\*\.fileSystemInfo\.createdDateTime | string | 
action\_result\.data\.\*\.fileSystemInfo\.lastModifiedDateTime | string | 
action\_result\.data\.\*\.folder\.childCount | numeric | 
action\_result\.data\.\*\.id | string |  `msonedrive file id`  `msonedrive folder id` 
action\_result\.data\.\*\.image\.height | numeric | 
action\_result\.data\.\*\.image\.width | numeric | 
action\_result\.data\.\*\.lastModifiedBy\.application\.displayName | string | 
action\_result\.data\.\*\.lastModifiedBy\.application\.id | string | 
action\_result\.data\.\*\.lastModifiedBy\.user\.displayName | string |  `user name` 
action\_result\.data\.\*\.lastModifiedBy\.user\.email | string |  `email` 
action\_result\.data\.\*\.lastModifiedBy\.user\.id | string | 
action\_result\.data\.\*\.lastModifiedDateTime | string | 
action\_result\.data\.\*\.name | string | 
action\_result\.data\.\*\.package\.type | string | 
action\_result\.data\.\*\.parentReference\.driveId | string |  `msonedrive drive id` 
action\_result\.data\.\*\.parentReference\.drivePath | string | 
action\_result\.data\.\*\.parentReference\.driveType | string | 
action\_result\.data\.\*\.parentReference\.folderPath | string |  `msonedrive folder path` 
action\_result\.data\.\*\.parentReference\.id | string |  `msonedrive drive id`  `msonedrive folder id` 
action\_result\.data\.\*\.size | numeric |  `file size` 
action\_result\.data\.\*\.webUrl | string |  `url` 
action\_result\.summary\.total\_items | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'list drive'
List of Drives

Type: **investigate**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.data\.\*\.createdBy\.user\.displayName | string |  `user name` 
action\_result\.data\.\*\.createdDateTime | string | 
action\_result\.data\.\*\.description | string | 
action\_result\.data\.\*\.driveType | string | 
action\_result\.data\.\*\.id | string |  `msonedrive drive id` 
action\_result\.data\.\*\.lastModifiedBy\.user\.displayName | string |  `user name` 
action\_result\.data\.\*\.lastModifiedBy\.user\.email | string |  `email` 
action\_result\.data\.\*\.lastModifiedBy\.user\.id | string | 
action\_result\.data\.\*\.lastModifiedDateTime | string | 
action\_result\.data\.\*\.name | string | 
action\_result\.data\.\*\.owner\.user\.displayName | string |  `user name` 
action\_result\.data\.\*\.owner\.user\.email | string |  `email` 
action\_result\.data\.\*\.owner\.user\.id | string | 
action\_result\.data\.\*\.quota\.deleted | numeric | 
action\_result\.data\.\*\.quota\.remaining | numeric | 
action\_result\.data\.\*\.quota\.state | string | 
action\_result\.data\.\*\.quota\.total | numeric | 
action\_result\.data\.\*\.quota\.used | numeric | 
action\_result\.data\.\*\.webUrl | string |  `url` 
action\_result\.summary\.total\_drives | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'upload file'
Upload file

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**drive\_id** |  optional  | Parent drive ID | string |  `msonedrive drive id` 
**vault\_id** |  required  | Vault ID | string |  `vault id`  `sha1` 
**file\_path** |  required  | File path with file name | string |  `file path` 
**auto\_rename** |  optional  | Auto rename file | boolean | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.auto\_rename | boolean | 
action\_result\.parameter\.drive\_id | string |  `msonedrive drive id` 
action\_result\.parameter\.file\_path | string |  `file path` 
action\_result\.parameter\.vault\_id | string |  `vault id`  `sha1` 
action\_result\.data\.\*\.\@content\.downloadUrl | string |  `url` 
action\_result\.data\.\*\.file\.irmEnabled | boolean | 
action\_result\.data\.\*\.\@odata\.context | string |  `url` 
action\_result\.data\.\*\.\@odata\.editLink | string | 
action\_result\.data\.\*\.\@odata\.id | string |  `url` 
action\_result\.data\.\*\.\@odata\.type | string | 
action\_result\.data\.\*\.cTag | string | 
action\_result\.data\.\*\.createdBy\.application\.displayName | string | 
action\_result\.data\.\*\.createdBy\.application\.id | string | 
action\_result\.data\.\*\.createdBy\.user\.displayName | string |  `user name` 
action\_result\.data\.\*\.createdBy\.user\.email | string |  `email` 
action\_result\.data\.\*\.createdBy\.user\.id | string | 
action\_result\.data\.\*\.createdDateTime | string | 
action\_result\.data\.\*\.eTag | string | 
action\_result\.data\.\*\.file\.hashes\.quickXorHash | string | 
action\_result\.data\.\*\.file\.mimeType | string | 
action\_result\.data\.\*\.fileSystemInfo\.createdDateTime | string | 
action\_result\.data\.\*\.fileSystemInfo\.lastModifiedDateTime | string | 
action\_result\.data\.\*\.id | string |  `msonedrive file id` 
action\_result\.data\.\*\.lastModifiedBy\.application\.displayName | string | 
action\_result\.data\.\*\.lastModifiedBy\.application\.id | string | 
action\_result\.data\.\*\.lastModifiedBy\.user\.displayName | string |  `user name` 
action\_result\.data\.\*\.lastModifiedBy\.user\.email | string |  `email` 
action\_result\.data\.\*\.lastModifiedBy\.user\.id | string | 
action\_result\.data\.\*\.lastModifiedDateTime | string | 
action\_result\.data\.\*\.name | string | 
action\_result\.data\.\*\.parentReference\.driveId | string |  `msonedrive drive id` 
action\_result\.data\.\*\.parentReference\.drivePath | string | 
action\_result\.data\.\*\.parentReference\.driveType | string | 
action\_result\.data\.\*\.parentReference\.folderPath | string |  `msonedrive folder path` 
action\_result\.data\.\*\.parentReference\.id | string |  `msonedrive drive id`  `msonedrive folder id` 
action\_result\.data\.\*\.size | numeric |  `file size` 
action\_result\.data\.\*\.webUrl | string |  `url` 
action\_result\.summary | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'delete file'
Delete file

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**file\_id** |  optional  | File id | string |  `msonedrive file id` 
**drive\_id** |  optional  | Drive id | string |  `msonedrive drive id` 
**file\_path** |  optional  | Path of file | string |  `file path` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.drive\_id | string |  `msonedrive drive id` 
action\_result\.parameter\.file\_id | string |  `msonedrive file id` 
action\_result\.parameter\.file\_path | string |  `file path` 
action\_result\.data | string | 
action\_result\.summary | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'delete folder'
Delete a folder

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**drive\_id** |  optional  | Parent drive ID | string |  `msonedrive drive id` 
**folder\_id** |  optional  | Folder ID | string |  `msonedrive folder id` 
**folder\_path** |  optional  | Folder path | string |  `msonedrive folder path` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.drive\_id | string |  `msonedrive drive id` 
action\_result\.parameter\.folder\_id | string |  `msonedrive folder id` 
action\_result\.parameter\.folder\_path | string |  `msonedrive folder path` 
action\_result\.data | string | 
action\_result\.summary | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'create folder'
Create a folder

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**drive\_id** |  optional  | Parent drive ID | string |  `msonedrive drive id` 
**folder\_id** |  optional  | Parent folder ID | string |  `msonedrive folder id` 
**folder\_path** |  optional  | Parent folder path | string |  `msonedrive folder path` 
**folder\_name** |  required  | Folder name | string |  `msonedrive folder name` 
**auto\_rename** |  optional  | Auto rename folder | boolean | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.auto\_rename | boolean | 
action\_result\.parameter\.drive\_id | string |  `msonedrive drive id` 
action\_result\.parameter\.folder\_id | string |  `msonedrive folder id` 
action\_result\.parameter\.folder\_name | string |  `msonedrive folder name` 
action\_result\.parameter\.folder\_path | string |  `msonedrive folder path` 
action\_result\.data\.\*\.\@odata\.context | string |  `url` 
action\_result\.data\.\*\.cTag | string | 
action\_result\.data\.\*\.createdBy\.application\.displayName | string | 
action\_result\.data\.\*\.createdBy\.application\.id | string | 
action\_result\.data\.\*\.createdBy\.user\.displayName | string |  `user name` 
action\_result\.data\.\*\.createdBy\.user\.email | string |  `email` 
action\_result\.data\.\*\.createdBy\.user\.id | string | 
action\_result\.data\.\*\.createdDateTime | string | 
action\_result\.data\.\*\.eTag | string | 
action\_result\.data\.\*\.fileSystemInfo\.createdDateTime | string | 
action\_result\.data\.\*\.fileSystemInfo\.lastModifiedDateTime | string | 
action\_result\.data\.\*\.folder\.childCount | numeric | 
action\_result\.data\.\*\.id | string |  `msonedrive folder id` 
action\_result\.data\.\*\.lastModifiedBy\.application\.displayName | string | 
action\_result\.data\.\*\.lastModifiedBy\.application\.id | string | 
action\_result\.data\.\*\.lastModifiedBy\.user\.displayName | string |  `file path` 
action\_result\.data\.\*\.lastModifiedBy\.user\.email | string |  `email` 
action\_result\.data\.\*\.lastModifiedBy\.user\.id | string | 
action\_result\.data\.\*\.lastModifiedDateTime | string | 
action\_result\.data\.\*\.name | string |  `msonedrive folder name` 
action\_result\.data\.\*\.parentReference\.driveId | string |  `msonedrive drive id` 
action\_result\.data\.\*\.parentReference\.drivePath | string | 
action\_result\.data\.\*\.parentReference\.driveType | string | 
action\_result\.data\.\*\.parentReference\.folderPath | string |  `msonedrive folder path` 
action\_result\.data\.\*\.parentReference\.id | string |  `msonedrive drive id`  `msonedrive folder id` 
action\_result\.data\.\*\.size | numeric |  `file size` 
action\_result\.data\.\*\.webUrl | string |  `url` 
action\_result\.summary | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric | 