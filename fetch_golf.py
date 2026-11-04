"""
Fetch Garmin Connect golf data for ONE round and probe the shot endpoint.

Credentials: your PASSWORD is never stored. On the first run you'll be prompted
(password + MFA hidden). After a successful login, only the expiring Garmin
OAuth *session token* is cached in ./.garmin_tokens/ so later runs skip the
login (this avoids Garmin's IP rate-limiting / 429s). Delete that folder to
force a fresh login.

Run it yourself:
    cd C:\\Users\\jonathan.garnier\\Documents\\garmin_golf
    python fetch_golf.py

Saves raw JSON to ./garmin_out/ for inspection.
"""
import getpass
import json
import os
import sys

from garminconnect import Garmin

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "garmin_out")
TOKENS = os.path.join(HERE, ".garmin_tokens")
os.makedirs(OUT, exist_ok=True)


def save(name, obj):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, default=str)
    print(f"  saved -> {path}")


def _seed_token_from_env():
    """In CI, materialize the token file from the GARMIN_TOKEN_B64 secret."""
    b64 = os.environ.get("GARMIN_TOKEN_B64")
    if not b64:
        return
    import base64
    os.makedirs(TOKENS, exist_ok=True)
    with open(os.path.join(TOKENS, "garmin_tokens.json"), "wb") as f:
        f.write(base64.b64decode(b64))


def make_client():
    """Resume from cached token if possible; otherwise prompt and cache.

    Headless mode: set GARMIN_HEADLESS=1 (and provide GARMIN_TOKEN_B64) to run
    without any prompt — used by the GitHub Action. On token failure it exits
    with a clear message instead of blocking on input().
    """
    _seed_token_from_env()
    headless = os.environ.get("GARMIN_HEADLESS") == "1"

    client = Garmin()
    if os.path.isdir(TOKENS) and os.listdir(TOKENS):
        try:
            print("Resuming session from cached token ...")
            client.login(TOKENS)
            print("Resumed OK (no password needed).\n")
            return client
        except Exception as e:
            print(f"  cached token unusable ({e}).")
            if headless:
                sys.exit("Headless login failed — the Garmin token has likely "
                         "expired. Re-run fetch_golf.py locally to refresh it, "
                         "then update the GARMIN_TOKEN_B64 secret.")
            print("  doing fresh login.\n")

    if headless:
        sys.exit("Headless mode but no usable token. Set the GARMIN_TOKEN_B64 "
                 "secret from a local .garmin_tokens/garmin_tokens.json.")

    print("Fresh login — password is not stored.")
    email = input("Garmin email: ").strip()
    password = getpass.getpass("Garmin password: ")
    client = Garmin(
        email, password,
        prompt_mfa=lambda: input("MFA code (check email/authenticator): ").strip(),
    )
    print("\nLogging in ...")
    client.login(TOKENS)          # caches OAuth token to TOKENS on success
    print("Login OK (token cached for next time).\n")
    return client


def fetch_round(client, sid, force=False):
    """Fetch + cache detail and per-hole shots for one scorecard."""
    detail_path = os.path.join(OUT, f"scorecard_{sid}.json")
    shots_path = os.path.join(OUT, f"shots_{sid}.json")
    if not force and os.path.exists(detail_path) and os.path.exists(shots_path):
        print(f"  id={sid}: already cached, skipping.")
        return

    detail = client.get_golf_scorecard(sid)
    save(f"scorecard_{sid}.json", detail)

    sd = detail["scorecardDetails"][0]
    all_nums = [h["number"] for h in sd["scorecard"]["holes"]]
    shot_counts = sd.get("shotCounts") or []
    holes_with_shots = [all_nums[i] for i, c in enumerate(shot_counts)
                        if i < len(all_nums) and c]
    print(f"  id={sid}: holes={all_nums} shotCounts={shot_counts} "
          f"-> fetching shots for {holes_with_shots}")

    # The shot endpoint accepts ONE hole at a time; loop and merge.
    merged = {"scorecardId": sid, "holeShots": [], "clubDetails": None}
    for n in holes_with_shots:
        try:
            res = client.get_golf_shot_data(sid, hole_numbers=str(n))
            merged["holeShots"].extend(res.get("holeShots", []))
            if merged["clubDetails"] is None and res.get("clubDetails"):
                merged["clubDetails"] = res["clubDetails"]
        except Exception as e:
            print(f"    FAILED hole {n}: {e}")
    save(f"shots_{sid}.json", merged)


def main():
    force = "--force" in sys.argv
    client = make_client()

    print("Fetching golf summary ...")
    summary = client.get_golf_summary()
    save("golf_summary.json", summary)
    cards = summary if isinstance(summary, list) else next(
        (v for v in summary.values() if isinstance(v, list) and v), [])
    if not cards:
        print("No scorecards found; inspect golf_summary.json.")
        return

    print(f"\nBackfilling {len(cards)} round(s) "
          f"({'force re-fetch' if force else 'skipping cached'}):")
    for c in cards:
        sid = c.get("id") or c.get("scorecardId")
        print(f"\n* {c.get('startTime')}  {c.get('courseName')}")
        try:
            fetch_round(client, sid, force=force)
        except Exception as e:
            print(f"  ERROR on id={sid}: {e}")

    print("\nDone. All rounds cached in garmin_out/. Tell Claude to load them.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
