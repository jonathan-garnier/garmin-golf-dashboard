/* Garmin golf data export — runs in your browser, using your logged-in session.
 *
 * WHY: Garmin changed their login (Sept 2026) and now blocks the Python
 * libraries. Your browser session is still trusted, so we fetch through it.
 *
 * HOW TO USE:
 *   1. Log in at https://connect.garmin.com in Chrome/Edge/Firefox.
 *   2. Open DevTools (F12) -> Console tab.
 *   3. If the console warns about pasting, type: allow pasting  (then Enter).
 *   4. Paste this ENTIRE file, press Enter, and wait.
 *   5. It downloads "garmin-golf-export.json". Move it into the repo folder and run:
 *        python import_browser_data.py garmin-golf-export.json
 *
 * If it errors, copy the red console output and send it to Claude — the exact
 * auth path may need a small tweak.
 */
(async () => {
  const tag = "%c[golf]";
  const css = "color:#34c759;font-weight:bold";
  const log = (...a) => console.log(tag, css, ...a);
  const err = (...a) => console.error("[golf]", ...a);

  const G = "/gcs-golfcommunity/api/v2";

  // --- 1. get an access token from the logged-in session ---
  async function getBearer() {
    // The Garmin Connect web app mints a short-lived access token here.
    const r = await fetch("https://connect.garmin.com/modern/di-oauth/exchange", {
      method: "POST",
      credentials: "include",
    });
    if (!r.ok) throw new Error("token exchange HTTP " + r.status);
    const j = await r.json();
    if (!j.access_token) throw new Error("no access_token in exchange response");
    return j.access_token;
  }

  let bearer;
  try {
    bearer = await getBearer();
    log("got access token OK");
  } catch (e) {
    err("Could not get an access token:", e.message);
    err("Make sure you're logged in at connect.garmin.com in THIS tab, then retry.");
    return;
  }

  const headers = { Authorization: "Bearer " + bearer, NK: "NT" };
  const api = async (path) => {
    const r = await fetch("https://connectapi.garmin.com" + path, {
      headers,
      credentials: "include",
    });
    if (!r.ok) throw new Error(path + " -> HTTP " + r.status);
    return r.json();
  };

  // --- 2. scorecard summary ---
  let summary;
  try {
    summary = await api(`${G}/scorecard/summary?per-page=200&start=0`);
  } catch (e) {
    err("Summary fetch failed:", e.message);
    err("If this is 401/403, the token path differs — send Claude this message.");
    return;
  }
  const cards = Array.isArray(summary)
    ? summary
    : Object.values(summary).find((v) => Array.isArray(v)) || [];
  log(`found ${cards.length} scorecard(s)`);

  // --- 3. per-round detail + per-hole shots ---
  const out = { summary, scorecards: {}, shots: {} };
  for (const c of cards) {
    const id = c.id || c.scorecardId;
    try {
      const detail = await api(
        `${G}/scorecard/detail?scorecard-ids=${id}&include-longest-shot-distance=true`
      );
      out.scorecards[id] = detail;

      const sd = detail.scorecardDetails && detail.scorecardDetails[0];
      const nums = ((sd && sd.scorecard && sd.scorecard.holes) || []).map((h) => h.number);
      const counts = (sd && sd.shotCounts) || [];
      const withShots = nums.filter((n, i) => counts[i]);

      const merged = { scorecardId: id, holeShots: [], clubDetails: null };
      for (const n of withShots) {
        // The shot endpoint accepts ONE hole per call.
        const res = await api(`${G}/shot/scorecard/${id}/hole?hole-numbers=${n}`);
        (res.holeShots || []).forEach((hs) => merged.holeShots.push(hs));
        if (!merged.clubDetails && res.clubDetails) merged.clubDetails = res.clubDetails;
      }
      out.shots[id] = merged;
      log(`round ${id}: ${c.courseName || "?"} — ${withShots.length} hole(s) with shots`);
    } catch (e) {
      err(`round ${id} failed:`, e.message);
    }
  }

  // --- 4. download ---
  const blob = new Blob([JSON.stringify(out)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "garmin-golf-export.json";
  document.body.appendChild(a);
  a.click();
  a.remove();
  log(`DONE — downloaded garmin-golf-export.json (${cards.length} rounds).`);
  log("Next: python import_browser_data.py garmin-golf-export.json");
})();
