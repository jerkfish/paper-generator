# Cloudflare token scopes

There are two different credentials. Do not use one in place of the other.

## 1. R2 upload credential (needed now)

`scripts/r2_sync.py` uses the **R2 S3 API**, not the general Cloudflare API.
Create this in the dashboard:

**R2 object storage -> Account Details -> Manage API Tokens -> Create API token**

| Setting | Value |
|---|---|
| Token name | `papergen-r2-sync` |
| Permissions | **Object Read & Write** |
| Bucket scope | **Only `exampapers`** |
| TTL | 1 year or shorter |
| Optional | IP allowlist for the machine that uploads |

This produces:

- Access Key ID -> `R2_ACCESS_KEY_ID`
- Secret Access Key -> `R2_SECRET_ACCESS_KEY`
- Endpoint -> `https://<account-id>.r2.cloudflarestorage.com`

None of the account/zone permissions in the general Cloudflare API token list
are needed for this upload. A general Cloudflare API token will not work as an
S3 access key.

Store the values only in `.env` (gitignored) or the process environment:

```text
R2_ACCOUNT_ID=<account id>
R2_BUCKET=exampapers
R2_ACCESS_KEY_ID=<access key id>
R2_SECRET_ACCESS_KEY=<secret access key>
```

## 2. Deployment credential (later, for Workers/Pages)

Only create this when deploying a Worker or Pages project. Use a **separate**
token, scoped to the one account and, where possible, the one zone.

Essential for the planned deployment:

| Permission | Why |
|---|---|
| Account: Workers Scripts:Edit | Deploy/update the Worker |
| Account: Workers R2 Storage:Read | Read bucket metadata for the binding |
| Account: Workers KV Storage:Edit | Phase 2 gallery index, if KV is used |
| Account: D1:Edit | Phase 2 gallery index, if D1 is used instead |
| Zone: Workers Routes:Edit | Route the Worker on the domain |
| Zone: Zone:Read | Resolve the zone for the route |
| Account: Turnstile Sites:Edit | Phase 3 Turnstile widget |
| Account: Account Analytics:Read | Optional usage/quota monitoring |
| Account: Pages:Edit | Only if using Pages instead of a Worker |

Remove these from any general token:

- DNS Write, Zone Write, SSL and Certificates Write, WAF Write
- Cache Purge, Cache Settings Write
- Access/Zero Trust, Email, Logs, Magic, Load Balancers, Stream, Images
- Account API Tokens Read/Write
- Billing Read/Write
- Access: Keys Read/Write
- Workers Admin
- All AI/AI Gateway/Vectorize/AI Search permissions
- Every other permission not listed above

## Rules

- Never put a token or access key in a tracked file, the public bundle or a log.
- Never use one token for both upload and deployment.
- Rotate the R2 token if it is ever pasted into chat, a commit or an issue.
- The account ID and bucket name are identifiers, not secrets. The Access Key
  ID and Secret Access Key are secrets.
