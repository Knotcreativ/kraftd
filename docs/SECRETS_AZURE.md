Azure Secrets and GitHub Actions login troubleshooting

Purpose
- Document required Azure secrets for GitHub Actions and how to validate them.

Required Secrets (preferred)
- AZURE_CLIENT_ID -> Service Principal appId
- AZURE_TENANT_ID -> tenantId
- AZURE_CLIENT_SECRET -> password (secret) of the SP
- AZURE_SUBSCRIPTION_ID -> target subscription id
- FUNCTION_APP_NAME -> name of Function App (for deploy-functions workflow)

Optional
- AZURE_CREDENTIALS -> full JSON returned by `az ad sp create-for-rbac --sdk-auth` (only needed if you use `creds:` input)

Common Issues & Fixes
- Error: "Content is not a valid JSON object." when using `creds: ${{ secrets.AZURE_CREDENTIALS }}`
  - Cause: the secret value is not valid JSON (extra newlines, incorrect escaping, trimmed fields)
  - Fix: Use separate `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_SUBSCRIPTION_ID` secrets and use those in the workflow instead of `creds:`. If you must use `AZURE_CREDENTIALS`, ensure the secret's content is exactly the JSON produced by `az ad sp create-for-rbac --sdk-auth` (no extra whitespace or newline at the end).

Validation tips
- Locally create SP JSON: az ad sp create-for-rbac --name "http://my-sp" --role "Contributor" --scopes "/subscriptions/<sub>/resourceGroups/<rg>" --sdk-auth > sp.json
- Validate JSON: cat sp.json | jq .  (or use python -m json.tool)
- If using GitHub Secrets UI, paste the raw JSON into the secret value field; avoid editing it in an editor that could add BOM or trailing characters.

Debugging in Actions
- Add a "Verify Azure Login" step after `azure/login` that runs `az account show --query '{name:name,id:id,tenantId:tenantId}' -o json` to confirm successful sign in.
- Check Actions run logs for errors and the exact message from `azure/login`.

Recommended workflow setup
- Prefer separate secrets (client-id/tenant-id/subscription-id/client-secret) for stability.
- Limit SP scope to required resource group(s) for least privilege.

DEPRECATION NOTE
- **Avoid using** `AZURE_CREDENTIALS` in new workflows. Using the explicit per-field secrets reduces the risk of JSON parsing errors in Actions and is easier to validate.

- **Security note:** The sample `azure-credentials.json` file has been removed from the repository to prevent accidental leakage of secrets. Do **not** commit SP JSON files to the repo; use GitHub Secrets instead. If you previously committed sensitive credentials, rotate them immediately and remove them from history.

---

## Secret scanning & incident runbook
If a secret is accidentally committed or a secret-scan reports a finding, follow these steps immediately:

1. **Rotate** the exposed credential (rotate client secrets, keys, tokens) — do this first before changing repo history.
2. **Remove the secret from repo history** (use `git filter-repo` or BFG). Example using `git filter-repo`:

   - Install: `pip install git-filter-repo` (or use BFG jar)
   - Remove: `git filter-repo --path "path/to/file/with/secret" --invert-paths`
   - Force-push the cleaned history to the remote (`git push --force --all` and `git push --force --tags`).

3. **Invalidate/rotate** any credentials that may have been exposed and update their replacements in GitHub Secrets.
4. **Ensure CI secrets** are rotated and re-seeded securely in repository Settings → Secrets.
5. **Notify stakeholders** and document the incident in `docs/SECURITY_INCIDENTS.md` (create one if needed).

Tools we added to the repo:
- `.pre-commit-config.yaml` includes `detect-secrets` to block accidental commits containing secrets.
- `.github/workflows/secret-scan.yml` runs `gitleaks` and `detect-secrets` on push and PRs (and daily by schedule).
- `scripts/scan_secrets.sh` is a helper to run scans locally (gitleaks + detect-secrets).

If you want, I can run a one-off `gitleaks` scan across the repo and open a PR with any follow-up fixes if something is found.


Quick check workflow
- A manual workflow `.github/workflows/check-azure-secrets.yml` is included to validate the presence of required repository secrets. Run it from the Actions tab (workflow: "Check Azure secrets").

If issues persist, recreate the Service Principal and update the secrets from fresh output.