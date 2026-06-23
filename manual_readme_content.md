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
