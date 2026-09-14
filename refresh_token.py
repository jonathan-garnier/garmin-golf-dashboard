"""Refresh the Garmin session token and print it as base64 for the
GARMIN_TOKEN_B64 GitHub secret.

Run this locally when the "Update golf data" workflow fails with
"Headless login failed / token expired". It logs you in (prompting for
email + password + MFA, since the old token is dead), writes a fresh token to
.garmin_tokens/, and prints the base64 to copy into the GitHub secret.

    python refresh_token.py
"""
import base64
import os

from fetch_golf import make_client, TOKENS

# make_client resumes if the token is still valid, otherwise prompts for a
# fresh interactive login and caches a new token.
make_client()

with open(os.path.join(TOKENS, "garmin_tokens.json"), "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

print("\n" + "=" * 70)
print("GARMIN_TOKEN_B64 — copy the single line below into the GitHub secret:")
print("  (repo > Settings > Secrets and variables > Actions > GARMIN_TOKEN_B64)")
print("=" * 70)
print(b64)
