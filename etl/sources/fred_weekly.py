"""Weekly FRED series. Uses the FRED API when FRED_API_KEY is set, else the public graph CSV.

The graph CSV needs no key but can time out from cloud runners such as GitHub Actions; the API is
built for automated use. Free key: https://fredaccount.stlouisfed.org/apikeys
"""

import datetime as dt

from common import env, get_csv, get_json, parse_date

KEY = None  # optional: without FRED_API_KEY the graph CSV is used, so this never falls back to sample data
API_URL = "https://api.stlouisfed.org/fred/series/observations"
CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

SERIES = [
    {"id": "wei", "order": 3, "title": "Economic Index", "group": "Jobs & economy",
     "description": "NY Fed weekly read on national growth, scaled to annual GDP growth. A falling index means a slowing economy.",
     "unit": "pct", "decimals": 2, "freq": "weekly", "agg": "last", "higher_is_worse": False, "weight": 1,
     "geo": "United States", "source": "Federal Reserve Bank of New York (FRED: WEI)",
     "source_url": "https://fred.stlouisfed.org/series/WEI", "fred_id": "WEI",
     "sample": {"base": 2.2, "vol": 0.12, "spike": -0.8}},
]


def _api(fred_id, start):
    resp = get_json(API_URL, params={"series_id": fred_id, "api_key": env("FRED_API_KEY"),
                                     "file_type": "json", "observation_start": start})
    return [(parse_date(o["date"]), o["value"]) for o in resp["observations"]]


def _csv(fred_id, start):
    rows = get_csv(CSV_URL, params={"id": fred_id, "cosd": start})
    date_col = next(iter(rows[0]))  # "observation_date" now, "DATE" in older files
    return [(parse_date(r[date_col]), r.get(fred_id, "")) for r in rows]


def fetch():
    start = (dt.date.today() - dt.timedelta(days=4 * 365)).isoformat()
    pull = _api if env("FRED_API_KEY") else _csv
    out = {}
    for s in SERIES:
        out[s["id"]] = [(d, float(v)) for d, v in pull(s["fred_id"], start)
                        if str(v).strip() not in ("", ".")]
    return out
