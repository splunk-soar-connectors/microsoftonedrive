## Authentication

This app requires creating a Microsoft Azure Application. To do so, navigate to
<https://portal.azure.com> in a browser and log in with a Microsoft account, then select **Azure
Active Directory** .

1. Go to **App Registrations** and click on **+ New registration** .
1. Give the app an appropriate name. The Redirect URI will be populated in a later step.
1. Select a supported account type (configure the application to be multitenant).
1. Click on the **Register** .
   - Under **Certificates & secrets** , add **New client secret** . Note this key somewhere
     secure, as it cannot be retrieved after closing the window.
   - Under **Authentication** , add the **Redirect URIs** field which will be filled in a later
     step.
   - Under **API Permissions** , click on **Add a permission** .
   - Go to **Microsoft Graph Permissions** , the following **Delegated Permissions** need to be
     added:
     - Group.ReadWrite.All
     - offline_access
     - User.ReadWrite.All
   - Click on the **Add permissions** .

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

- For Non-NRI Instance:
  /opt/phantom/local_data/app_states/a73f6d32-c9d5-4fec-b024-43876700daa6/{asset_id}\_state.json
- For NRI Instance:
  /\<PHANTOM_HOME_DIRECTORY>/local_data/app_states/a73f6d32-c9d5-4fec-b024-43876700daa6/{asset_id}\_state.json

#### State File Permissions

- File Rights: rw-rw-r-- (664) (The phantom user should have read and write access for the state
  file)
- File Owner: appropriate phantom user
