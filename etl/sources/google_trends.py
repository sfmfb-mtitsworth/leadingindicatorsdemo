"""Google searches for "food bank" in the San Francisco-Oakland-San Jose DMA (Google Trends API alpha).

Same query as the California Hunger Signal project (hungersearchindex): term "food bank", BROAD
match, DMA 807, weekly. Auth is a Google Cloud service account in the project that has Trends
alpha access; its JSON key goes in the GOOGLE_TRENDS_SA_KEY secret (the whole file's contents).

KEY is None on purpose: without the secret the fetch fails and the dashboard keeps the stored
history (backfilled from hungersearchindex) flagged as not updating, instead of sample data.
"""

import datetime as dt
import json
import time

from common import env

KEY = None
BASE = "https://searchtrends.googleapis.com/v1alpha"
SCOPES = ["https://www.googleapis.com/auth/searchtrends"]
DMA = "807"  # San Francisco-Oakland-San Jose

SERIES = [
    {"id": "searches_bay", "order": 1, "title": "Searches for \"Food Bank\"", "group": "Demand signals",
     "description": "How often people in the SF-Oakland-San Jose media market search Google for \"food bank\". A relative index, not a count of searches. More searches suggest more people looking for help.",
     "unit": "index", "decimals": 0, "freq": "weekly", "agg": "mean", "higher_is_worse": True, "weight": 0,
     "geo": "SF-Oakland-San Jose DMA", "source": "Google Trends API (alpha)",
     "source_url": "https://trends.google.com/trends/explore?geo=US-CA-807&q=food%20bank",
     "sample": {"base": 15000, "vol": 0.15, "season": 0.15, "integer": True}},
]


def _session():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2 import service_account
    if not env("GOOGLE_TRENDS_SA_KEY"):
        raise RuntimeError("Google Trends credentials not set: GOOGLE_TRENDS_SA_KEY")
    info = json.loads(env("GOOGLE_TRENDS_SA_KEY"))
    return AuthorizedSession(service_account.Credentials.from_service_account_info(info, scopes=SCOPES))


def fetch():
    s = _session()
    end = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=3)  # the API's last few days are unreliable
    start = end - dt.timedelta(days=3 * 365)
    spec = {"spec": {
        "expression": {"terms": [{"value": "food bank", "type": "BROAD"}]},
        "geo": {"type": "GEO_TYPE_DESIGNATED_MARKET_AREA", "code": DMA},
        "timeRange": {"startTime": {"seconds": int(start.timestamp())}, "endTime": {"seconds": int(end.timestamp())}},
        "timeResolution": "WEEK",
    }}
    r = s.post(f"{BASE}:fetchTimeSeries", json=spec, timeout=60)
    r.raise_for_status()
    op = r.json()
    for _ in range(30):  # long-running operation
        if op.get("done"):
            break
        time.sleep(2)
        r = s.get(f"{BASE}/operations/{op['name']}", timeout=60)
        r.raise_for_status()
        op = r.json()
    else:
        raise TimeoutError("Google Trends operation did not finish")
    pts = []
    for p in op["response"]["timeSeries"]["points"]:
        if p.get("isPartial"):
            continue
        # Trends weeks start on Sunday; +1 day keys each to the Monday week the dashboard uses.
        d = dt.date.fromisoformat(p["timeRange"]["startTime"][:10]) + dt.timedelta(days=1)
        pts.append((d, float(p["searchInterest"])))
    return {"searches_bay": pts}
