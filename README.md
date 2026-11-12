# SF Bay Area Leading Indicators

Weekly leading indicators of household economic pressure in the San Francisco Bay Area:
prices, jobs and housing. GitHub Actions pulls each source, scores anomalies, renders
`site/index.html` and publishes it to GitHub Pages.

## Indicators

| Group | Indicator | Geography | Source | Secret |
|---|---|---|---|---|
| Demand signals | Searches for "food bank" | SF-Oakland-San Jose DMA | Google Trends API (alpha), same query as `hungersearchindex`; Google's 0-100 score, full 3-year series replaced each run | `GOOGLE_TRENDS_SA_KEY` |
| Fuel prices | Gas prices | San Francisco | EIA weekly retail | `EIA_API_KEY` |
| Fuel prices | Diesel prices | California | EIA weekly retail | `EIA_API_KEY` |
| Food staple prices | Egg prices | California | USDA AMS report 2844 | `USDA_AMS_API_KEY` |
| Food staple prices | Chicken prices | Western U.S. | USDA AMS report 3646 | `USDA_AMS_API_KEY` |
| Food staple prices | Beef prices | U.S. | USDA AMS report 2453 | `USDA_AMS_API_KEY` |
| Jobs & economy | Unemployment claims | SF + Marin | EDD weekly claims by county (dashboard xlsx) | none |
| Jobs & economy | WARN layoff notices | Bay Area | EDD WARN xlsx + backfill from FY24-25 and FY25-26 PDFs (`data/backfill/`) | none |
| Jobs & economy | Weekly Economic Index | U.S. | NY Fed via FRED `WEI` (FRED API; public CSV if no key) | recommended `FRED_API_KEY` |
| Housing stress | Eviction notices | San Francisco | DataSF `5cei-gny5` | optional `SOCRATA_APP_TOKEN` |
| Housing stress | Rents | SF metro | Zillow ZORI (monthly) | none |
| Jobs & economy | Inflation (CPI), all items | SF-Oakland-Hayward | BLS `CUURS49BSA0` (every other month) | optional `BLS_API_KEY` |
| Food staple prices | Food inflation (CPI), food at home | SF-Oakland-Hayward | BLS `CUURS49BSAF11` (every other month) | optional `BLS_API_KEY` |
| Jobs & economy | Unemployment rate | SF + Marin | BLS LAUS county data (unemployed ÷ labor force) | optional `BLS_API_KEY` |

A source whose secret is missing shows **sample data**, labelled on the dashboard. Add the
secret under Settings > Secrets and variables > Actions and the next run switches it to live.

**Google Trends:** a Google Cloud service account in the project that has Trends alpha access. Put the whole JSON
key file in the `GOOGLE_TRENDS_SA_KEY` secret. No user sign-in, so it does not expire; rotate the key by creating a new
one in Google Cloud, updating the secret, then deleting the old key. Without the secret the card keeps its stored
history and is flagged as not updating. It is shown on its own and not counted in the General Indicator (`weight: 0`).

## Schedule

- **GitHub Actions** (`.github/workflows/etl.yml`) fetches every source, rebuilds `site/index.html` and deploys it
  to GitHub Pages daily at about 3am Pacific. It also runs on pushes that change `etl/`, `templates/` or the workflow,
  and can be run by hand from the Actions tab.
- GitHub Pages must be set to deploy from **GitHub Actions** (Settings > Pages > Source).

## How it works

- `etl/sources/<name>.py`: one module per source. Each declares `KEY`, `SERIES` metadata and `fetch()`.
- `etl/build.py`: runs every source, merges results into `data/series/<id>.json` (history
  accumulates, which matters for WARN since EDD only publishes the current fiscal year),
  scores anomalies and writes `data/dashboard.json` and `site/index.html`.
- A failed source keeps its last good data and is flagged on the dashboard; it never blocks the others.

**Anomaly levels:** each period's z-score against the trailing 52 weeks (24 months for monthly
data), signed so higher always means more pressure on households. Level 1/2/3 = 1/2/3+ SD.
**General Indicator:** weighted mean of those signed z-scores per week (weights in each module).

## Run locally

```
pip install -r requirements.txt
LI_FORCE_SAMPLE=1 python etl/build.py   # all sample data, no network
python etl/build.py                     # live where keys are set in the environment
```

## Adding an indicator

Copy a module in `etl/sources/`, fill in `SERIES` (see the field list at the top of
`etl/build.py`) and `fetch()`, and add any secret to `.github/workflows/etl.yml`.
