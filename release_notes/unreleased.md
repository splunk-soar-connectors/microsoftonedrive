**Unreleased**

* Encode Microsoft Graph identifiers and paths before building action endpoints.
* Reject exact dot identifiers before Microsoft Graph endpoint construction.
* Escape connector-controlled values rendered in the list-items action widget.
* Reject unsafe destinations in pre-authenticated OneDrive download URLs.
* Restrict pre-authenticated file downloads to trusted OneDrive and SharePoint hosts.
* Validate forced-download redirect destinations before following them.
* Bind delegated OAuth callbacks to their initiating connectivity flow with a single-use nonce.
* Bound list-items pagination and recursive traversal with a capped result limit.
* Bound list-drive pagination and reject repeated continuation URLs.
* Bound Graph JSON response sizes and retained drive results.
* Remove credential-bearing state left by pre-SDK releases and keep OAuth tokens in the SDK's encrypted authentication partition.
* Require the pending-flow nonce before returning the delegated OAuth authorization URL.
