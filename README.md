[comment]: # "Auto-generated SOAR connector documentation"
# Microsoft OneDrive

Publisher: Splunk  
Connector Version: 2.3.1  
Product Vendor: Microsoft  
Product Name: Microsoft OneDrive  
Product Version Supported (regex): ".\*"  
Minimum Product Version: 6.2.2  

This app integrates with Microsoft OneDrive to execute various generic actions

[comment]: # " File: README.md"
[comment]: # "  Copyright (c) 2019-2024 Splunk Inc."
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
**client_id** |  required  | string | Client ID
**client_secret** |  required  | password | Client secret
**tenant_id** |  optional  | string | Tenant ID

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
**file_id** |  optional  | ID of file | string |  `msonedrive file id` 
**drive_id** |  optional  | Drive ID | string |  `msonedrive drive id` 
**file_path** |  optional  | Path of file | string |  `file path` 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.parameter.drive_id | string |  `msonedrive drive id`  |   b!gy8xut3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q 
action_result.parameter.file_id | string |  `msonedrive file id`  |   01FMDEUQZPP6VBB2PJQRF3AQRCTXQVAWMO 
action_result.parameter.file_path | string |  `file path`  |   newsample 1/filetxt.txt 
action_result.data | string |  |  
action_result.data.\*.file_name | string |  |   filetxt.txt 
action_result.data.\*.size | numeric |  `file size`  |   4 
action_result.data.\*.vault_id | string |  `vault id`  |   7110eda4d09e062aa5e4a390b0a572ac0d2c0220 
action_result.summary.vault_id | string |  `vault id`  |   7110eda4d09e062aa5e4a390b0a572ac0d2c0220 
action_result.message | string |  |  
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'list items'
List of items

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**drive_id** |  optional  | Parent drive ID | string |  `msonedrive drive id` 
**folder_id** |  optional  | Parent folder ID | string |  `msonedrive folder id` 
**folder_path** |  optional  | Parent folder path | string |  `msonedrive folder path` 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.parameter.drive_id | string |  `msonedrive drive id`  |   b!gy8xut3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q 
action_result.parameter.folder_id | string |  `msonedrive folder id`  |   01TEST123TEST123TEST123U3KTTEST123 
action_result.parameter.folder_path | string |  `msonedrive folder path`  |   Test/child_1/child_1_1 
action_result.data.\*.@microsoft.graph.downloadUrl | string |  `url`  |   https://test-my.abc.com/test/test_xyz_com/_layouts/00/download.aspx?UniqueId=test&ApiVersion=2.0 
action_result.data.\*.cTag | string |  |   "c:{2test123-1234-1234-1234-test123test1},0" 
action_result.data.\*.createdBy.application.displayName | string |  |   Test_One-drive 
action_result.data.\*.createdBy.application.id | string |  |   ba56100c-856c-469f-b6a0-a4335614c502 
action_result.data.\*.createdBy.user.displayName | string |  `user name`  |   Test User 
action_result.data.\*.createdBy.user.email | string |  `email`  |   test@test.test.com 
action_result.data.\*.createdBy.user.id | string |  |   17b006d0-35ed-4881-ab62-d2eb73c2ebe3 
action_result.data.\*.createdDateTime | string |  |   2018-09-01T09:21:24Z 
action_result.data.\*.currentUserRole.blocksDownload | boolean |  |   True  False 
action_result.data.\*.currentUserRole.readOnly | boolean |  |   True  False 
action_result.data.\*.eTag | string |  |   "{2test123-1234-1234-1234-test123test1},1" 
action_result.data.\*.file.hashes.quickXorHash | string |  |   fio2VWDQgVGaX34LXedeos6Y6/s= 
action_result.data.\*.file.mimeType | string |  |   image/png 
action_result.data.\*.fileSystemInfo.createdDateTime | string |  |   2018-09-01T09:21:24Z 
action_result.data.\*.fileSystemInfo.lastModifiedDateTime | string |  |   2018-09-01T09:21:24Z 
action_result.data.\*.folder.childCount | numeric |  |   17 
action_result.data.\*.id | string |  `msonedrive file id`  `msonedrive folder id`  |   01TEST123TEST123TEST123U3KTTEST123 
action_result.data.\*.image.height | numeric |  |   183 
action_result.data.\*.image.width | numeric |  |   275 
action_result.data.\*.lastModifiedBy.application.displayName | string |  |   Test_One-drive 
action_result.data.\*.lastModifiedBy.application.id | string |  |   ba56002c-856c-469f-b6a0-a4335614c502 
action_result.data.\*.lastModifiedBy.user.displayName | string |  `user name`  |   Test User 
action_result.data.\*.lastModifiedBy.user.email | string |  `email`  |   test@test.xyz.com 
action_result.data.\*.lastModifiedBy.user.id | string |  |   17be00d0-35ed-4881-ab62-d2eb73c2ebe3 
action_result.data.\*.lastModifiedDateTime | string |  |   2018-09-01T10:37:09Z 
action_result.data.\*.name | string |  |   test file 
action_result.data.\*.package.type | string |  |   oneNote 
action_result.data.\*.parentReference.driveId | string |  `msonedrive drive id`  |   b!gyx8tu3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q 
action_result.data.\*.parentReference.drivePath | string |  |   /drive/root:/ 
action_result.data.\*.parentReference.driveType | string |  |   business 
action_result.data.\*.parentReference.folderPath | string |  `msonedrive folder path`  |   Test/child 
action_result.data.\*.parentReference.id | string |  `msonedrive drive id`  `msonedrive folder id`  |   01FMDEUQ56Y2GOVW7725BZO354PWSELRRZ 
action_result.data.\*.size | numeric |  `file size`  |   359666 
action_result.data.\*.webUrl | string |  `url`  |   https://test-my.test.com/personal/test_abc_com/Documents/Test 
action_result.summary.total_items | numeric |  |   20 
action_result.message | string |  |   Total items: 20 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'list drive'
List of Drives

Type: **investigate**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.data.\*.createdBy.user.displayName | string |  `user name`  |   System Account 
action_result.data.\*.createdDateTime | string |  |   2018-09-04T01:34:10Z 
action_result.data.\*.description | string |  |  
action_result.data.\*.driveType | string |  |   business 
action_result.data.\*.id | string |  `msonedrive drive id`  |   b!test123_TESTzTEST123faTEST123LTEST-7TEST123-MTEST123RJQb3TEST123 
action_result.data.\*.lastModifiedBy.user.displayName | string |  `user name`  |   Test User 
action_result.data.\*.lastModifiedBy.user.email | string |  `email`  |   test@test.xyz.com 
action_result.data.\*.lastModifiedBy.user.id | string |  |   17be76d0-35ed-4881-ab62-d2eb73c2ebe3 
action_result.data.\*.lastModifiedDateTime | string |  |   2018-09-21T05:40:10Z 
action_result.data.\*.name | string |  |   OneDrive 
action_result.data.\*.owner.user.displayName | string |  `user name`  |   Test User 
action_result.data.\*.owner.user.email | string |  `email`  |   test@test.abc.com 
action_result.data.\*.owner.user.id | string |  |   17be76d0-35ed-4881-ab62-d2eb73c2ebe3 
action_result.data.\*.quota.deleted | numeric |  |   2555167314 
action_result.data.\*.quota.remaining | numeric |  |   1097114685696 
action_result.data.\*.quota.state | string |  |   normal 
action_result.data.\*.quota.total | numeric |  |   1099511627776 
action_result.data.\*.quota.used | numeric |  |   355597522 
action_result.data.\*.webUrl | string |  `url`  |   https://test-my.abc.com/personal/test_test_xyz_com/Documents 
action_result.summary.total_drives | numeric |  |   1 
action_result.message | string |  |   Total drives: 1 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'upload file'
Upload file

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**drive_id** |  optional  | Parent drive ID | string |  `msonedrive drive id` 
**vault_id** |  required  | Vault ID | string |  `vault id`  `sha1` 
**file_path** |  required  | File path with file name | string |  `file path` 
**auto_rename** |  optional  | Auto rename file | boolean | 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.parameter.auto_rename | boolean |  |   True  False 
action_result.parameter.drive_id | string |  `msonedrive drive id`  |   b!gy8xuu3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q 
action_result.parameter.file_path | string |  `file path`  |   Test/test135.txt 
action_result.parameter.vault_id | string |  `vault id`  `sha1`  |   c46f17281437ff7906b5c6779a2fb7c3f002b786 
action_result.data.\*.@content.downloadUrl | string |  `url`  |   https://test-my.abc.com/test/test_xyz_com/_layouts/00/download.aspx?UniqueId=test&ApiVersion=2.0 
action_result.data.\*.file.irmEnabled | boolean |  |   True  False 
action_result.data.\*.@odata.context | string |  `url`  |   https://test-my.abc.com/personal/test_abc_com/_api/v2.0/$metadata#items/$entity 
action_result.data.\*.@odata.editLink | string |  |   drives/b!gy8xtu3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q/items/01FMDEUQ532OAQOAAUFVCL6MDY7H3CUEKN 
action_result.data.\*.@odata.id | string |  `url`  |   https://test-my.abc.com/personal/test_abc_com/_api/v2.0/drives/b!test123_TESTzTEST123faTEST123LTEST-7TEST123-MTEST123RJQb3TEST123/items/01TEST123TEST123TEST123U3KTTEST123 
action_result.data.\*.@odata.type | string |  |   #oneDrive.item 
action_result.data.\*.cTag | string |  |   "c:{2test123-1234-1234-1234-test123test1},2" 
action_result.data.\*.createdBy.application.displayName | string |  |   Test_One-drive 
action_result.data.\*.createdBy.application.id | string |  |   ba56122c-856c-469f-b6a0-a4335614c502 
action_result.data.\*.createdBy.user.displayName | string |  `user name`  |   Test User 
action_result.data.\*.createdBy.user.email | string |  `email`  |   test@test.test.com 
action_result.data.\*.createdBy.user.id | string |  |   17be76d0-35ed-4881-ab62-d2eb73c2ebe3 
action_result.data.\*.createdDateTime | string |  |   2018-09-21T12:22:02Z 
action_result.data.\*.eTag | string |  |   "{2test123-1234-1234-1234-test123test1},3" 
action_result.data.\*.file.hashes.quickXorHash | string |  |   AAAAAAAAAAAAAAAAAIwPCgAAAAA= 
action_result.data.\*.file.mimeType | string |  |   text/plain 
action_result.data.\*.fileSystemInfo.createdDateTime | string |  |   2018-09-01T12:22:02Z 
action_result.data.\*.fileSystemInfo.lastModifiedDateTime | string |  |   2018-09-01T12:23:03Z 
action_result.data.\*.id | string |  `msonedrive file id`  |   01TEST123TEST123TEST123U3KTTEST123 
action_result.data.\*.lastModifiedBy.application.displayName | string |  |   Test_One-drive 
action_result.data.\*.lastModifiedBy.application.id | string |  |   ba56122c-856c-469f-b6a0-a4335614c502 
action_result.data.\*.lastModifiedBy.user.displayName | string |  `user name`  |   Test User 
action_result.data.\*.lastModifiedBy.user.email | string |  `email`  |   test@test.xyz.com 
action_result.data.\*.lastModifiedBy.user.id | string |  |   17be76d0-35ed-4881-ab62-d2eb73c2ebe3 
action_result.data.\*.lastModifiedDateTime | string |  |   2018-09-01T12:23:03Z 
action_result.data.\*.name | string |  |   test135 3.txt 
action_result.data.\*.parentReference.driveId | string |  `msonedrive drive id`  |   b!gy8xtu3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q 
action_result.data.\*.parentReference.drivePath | string |  |   /drives/b!test123_TESTzTEST123faTEST123LTEST-7TEST123-MTEST123RJQb3TEST123/root:/ 
action_result.data.\*.parentReference.driveType | string |  |   business 
action_result.data.\*.parentReference.folderPath | string |  `msonedrive folder path`  |   TestParent/child 
action_result.data.\*.parentReference.id | string |  `msonedrive drive id`  `msonedrive folder id`  |   01FMDEUQZDNXCWNB3JIZCIM2A27DHROBE2 
action_result.data.\*.size | numeric |  `file size`  |   168791040 
action_result.data.\*.webUrl | string |  `url`  |   https://test-my.TEST.com/personal/test_xyz_com/Documents/Test/abc135%203.txt 
action_result.summary | string |  |  
action_result.message | string |  |   The file is uploaded successfully 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'delete file'
Delete file

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**file_id** |  optional  | File id | string |  `msonedrive file id` 
**drive_id** |  optional  | Drive id | string |  `msonedrive drive id` 
**file_path** |  optional  | Path of file | string |  `file path` 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.parameter.drive_id | string |  `msonedrive drive id`  |   b!gy8xtu3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q 
action_result.parameter.file_id | string |  `msonedrive file id`  |   01FMDEUQYMRSDNYGDC3NB3KAX7M2UWFZLA 
action_result.parameter.file_path | string |  `file path`  |   /Test/a.txt 
action_result.data | string |  |  
action_result.summary | string |  |  
action_result.message | string |  |   File is deleted successfully 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'delete folder'
Delete a folder

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**drive_id** |  optional  | Parent drive ID | string |  `msonedrive drive id` 
**folder_id** |  optional  | Folder ID | string |  `msonedrive folder id` 
**folder_path** |  optional  | Folder path | string |  `msonedrive folder path` 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.parameter.drive_id | string |  `msonedrive drive id`  |   b!gy8txu3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q 
action_result.parameter.folder_id | string |  `msonedrive folder id`  |   01TEST123TEST123TEST123U3KTTEST123 
action_result.parameter.folder_path | string |  `msonedrive folder path`  |   Test/child/test1234567 
action_result.data | string |  |  
action_result.summary | string |  |  
action_result.message | string |  |   Either Folder ID or Folder Path is mandatory 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'create folder'
Create a folder

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**drive_id** |  optional  | Parent drive ID | string |  `msonedrive drive id` 
**folder_id** |  optional  | Parent folder ID | string |  `msonedrive folder id` 
**folder_path** |  optional  | Parent folder path | string |  `msonedrive folder path` 
**folder_name** |  required  | Folder name | string |  `msonedrive folder name` 
**auto_rename** |  optional  | Auto rename folder | boolean | 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.parameter.auto_rename | boolean |  |   True  False 
action_result.parameter.drive_id | string |  `msonedrive drive id`  |   b!gy8xu3t_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q 
action_result.parameter.folder_id | string |  `msonedrive folder id`  |   01TEST123TEST123TEST123U3KTTEST123 
action_result.parameter.folder_name | string |  `msonedrive folder name`  |   Test_1 
action_result.parameter.folder_path | string |  `msonedrive folder path`  |   TestParentFolder/child 
action_result.data.\*.@odata.context | string |  `url`  |   https://abc.test.com/v1.0/$metadata#users(01TEST123TEST123TEST123U3KTTEST123)/drive/items(01TEST123TEST123TEST123U3KTTEST123)/children/$entity 
action_result.data.\*.cTag | string |  |   "c:{2test123-1234-1234-1234-test123test1},0" 
action_result.data.\*.createdBy.application.displayName | string |  |   Test_One-drive 
action_result.data.\*.createdBy.application.id | string |  |   ba56002c-856c-469f-b6a0-a4335614c502 
action_result.data.\*.createdBy.user.displayName | string |  `user name`  |   Test User 
action_result.data.\*.createdBy.user.email | string |  `email`  |   test@test.test.com 
action_result.data.\*.createdBy.user.id | string |  |   17be00d0-35ed-4881-ab62-d2eb73c2ebe3 
action_result.data.\*.createdDateTime | string |  |   2018-09-01T08:49:18Z 
action_result.data.\*.eTag | string |  |   "{2test123-1234-1234-1234-test123test1},1" 
action_result.data.\*.fileSystemInfo.createdDateTime | string |  |   2018-09-01T08:49:18Z 
action_result.data.\*.fileSystemInfo.lastModifiedDateTime | string |  |   2018-09-01T08:49:18Z 
action_result.data.\*.folder.childCount | numeric |  |   0 
action_result.data.\*.id | string |  `msonedrive folder id`  |   01TEST123TEST123TEST123U3KTTEST123 
action_result.data.\*.lastModifiedBy.application.displayName | string |  |   Test_One-drive 
action_result.data.\*.lastModifiedBy.application.id | string |  |   ba56002c-856c-469f-b6a0-a4335614c502 
action_result.data.\*.lastModifiedBy.user.displayName | string |  `file path`  |   Test User 
action_result.data.\*.lastModifiedBy.user.email | string |  `email`  |   test@test.xyz.com 
action_result.data.\*.lastModifiedBy.user.id | string |  |   17be00d0-35ed-4881-ab62-d2eb73c2ebe3 
action_result.data.\*.lastModifiedDateTime | string |  |   2018-09-01T08:49:18Z 
action_result.data.\*.name | string |  `msonedrive folder name`  |   Test_1 1 
action_result.data.\*.parentReference.driveId | string |  `msonedrive drive id`  |   b!gy8txu3_CUGGzSNOtUDsfa7hXaCCfLxItT-7xwy5GBi-M3iaikaERJQb3tinpt9q 
action_result.data.\*.parentReference.drivePath | string |  |   /drives/b!test123_TESTzTEST123faTEST123LTEST-7TEST123-MTEST123RJQb3TEST123/root:/ 
action_result.data.\*.parentReference.driveType | string |  |   business 
action_result.data.\*.parentReference.folderPath | string |  `msonedrive folder path`  |   Test 
action_result.data.\*.parentReference.id | string |  `msonedrive drive id`  `msonedrive folder id`  |   01FMDUEQY3MRPCRFEYX5FJPU3KT7J24LJB 
action_result.data.\*.size | numeric |  `file size`  |   0 
action_result.data.\*.webUrl | string |  `url`  |   https://test-my.test.com/personal/test_xyz_com/Documents/Test/Test_1%201 
action_result.summary | string |  |  
action_result.message | string |  |   The folder: Test_1 is created successfully 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1 