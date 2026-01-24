# Secrets Rotation Runbook

This runbook covers rotating third-party vendor keys (SendGrid, Stripe, Twilio) and updating repository and Container App secrets.

## Principles
- **Rotate first, then purge**: Create new keys in vendor dashboards, update CI and runtime secrets, verify, then revoke old keys.
- **Avoid storing secrets in repo**: Use GitHub Secrets + Container App secretRefs or Key Vault references.

---

## 1) SendGrid

Manual (recommended):
- Log in to SendGrid dashboard → Settings → API Keys → Create API Key (Full Access or Restricted with Mail Send).
- Copy new key.
- Update repo secret: `gh secret set SENDGRID_API_KEY --body '<new-key>'`.
- Update Container App secret: `az containerapp secret set -g <rg> -n <app> --secrets sendgrid-api-key='<new-key>'` and set `SENDGRID_API_KEY` env to `secretRef:sendgrid-api-key`.
- Verify: send a test email using backend integration.
- Revoke old key in SendGrid dashboard after verification.

API automation (if you can provide an existing admin key):
- Use SendGrid Web API to create new key programmatically: `POST https://api.sendgrid.com/v3/api_keys` with Authorization header using an admin key. Save new key and proceed as above.

---

## 2) Stripe

Manual (recommended):
- Sign in to Stripe Dashboard → Developers → API keys → Create restricted key with required scopes (if possible).
- Update repo secret: `gh secret set STRIPE_SECRET_KEY --body '<new-key>'`.
- Update Container App secret and verify test payments in staging.
- Revoke old key after verification.

Automation note: Stripe key creation is primary via the dashboard; some API endpoints exist but require existing key with required scopes.

---

## 3) Twilio (if used)

Manual:
- Twilio Console → Project → API Keys → Create API Key (Standard or Main Account SID).
- Update `GH secret` and container/app secrets, then verify by sending an SMS in staging.
- Revoke old keys.

---

## 4) Azure Communication Services (Email) — recommended replacement for SendGrid

Provision ACS Email:
- Create an ACS resource (Portal / Bicep / CLI). Example script in `scripts/setup_acs.sh` automates deploying the ACS resource and setting the GitHub secret `AZURE_COMMUNICATION_CONNECTION_STRING` (call: `./scripts/setup_acs.sh kraftdintel-rg kraftd-comm uaenorth`).
- Get the connection string via `az resource invoke-action --action listKeys --ids <resourceId> --api-version 2021-10-01` (the script does this), then add to GH secrets.
- Set Container App secret: `az containerapp secret set -g <rg> -n <app> --secrets azure-comm-conn='<connection-string>'` and update the app env var to reference `secretRef:azure-comm-conn`.
- Replace SendGrid SDK usage with ACS Email SDK in code and add a smoke test for sending email.

Verification & rollout:
- Configure DNS (SPF/DKIM) for sending domain.
- Run a staging smoke test and verify deliverability.
- Revoke old SendGrid keys after verification.

Notes:
- The ACS approach keeps everything inside Azure and integrates with KeyVault and managed identities if required. Use `scripts/setup_acs.sh` to create and set the GH secret automatically.

---

## 4) Verification steps (common)
- Run smoke tests and integration tests that exercise the relevant integration.
- Check application logs for authentication errors.
- Confirm in vendor dashboards that new keys are being used (monitor usage/requests).

---

## 5) Update procedure to complete rotation
1. Create PR to remove/redact in-repo literals (done). Merge PR.
2. Rotate vendor keys (create new keys) and update GH secrets (action: `gh secret set ...`).
3. Update Container App secrets: `az containerapp secret set --resource-group <rg> --name <app> --secrets sendgrid-api-key='<val>'`.
4. Trigger new Container App revision (update image or run update) to pick secrets up.
5. Verify; revoke old keys.
6. Re-run `gitleaks` & `detect-secrets` to confirm no remaining exposures.

---

## 6) If you'd like me to proceed
- Provide admin-access to vendor dashboards or temporary admin API keys (recommended), OR
- Approve manual rotation and I will prepare exact commands and PRs; then you or a teammate can perform dashboard rotations and send back new keys to set as GitHub Secrets.

---

If you authorize, I can rotate SendGrid and Stripe keys now (if you provide credentials) and then automatically update the repository and Container App secrets and verify. Otherwise I will prepare the exact commands and PRs for you to run.
