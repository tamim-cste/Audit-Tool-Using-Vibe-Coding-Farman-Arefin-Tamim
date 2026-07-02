# SEO Audit Tool

A single-page SEO audit tool. Paste a URL, click **Analyze**, and it loads *exactly that page* with a
real headless browser (Playwright), waits for it to fully render, and audits the **rendered DOM**
(after JavaScript execution) — never the raw server response, and never any other page.

No crawling, no sitemap traversal, no following links. No auth, no user accounts, no Celery/Redis/
background workers — one URL in, one synchronous request, one report out.

---

## What it checks

Meta tags · Heading hierarchy (H1–H6) · Images & alt text · Canonical URL · Robots meta ·
Open Graph · Twitter Card · Structured data (JSON-LD/schema.org) · Internal/external links ·
Broken links (bounded, safe status checks) · SEO-relevant accessibility signals ·
Lighthouse-SEO-inspired best practices · Performance timing (load time, HTML size, HTTP status)

Every finding shown in the report carries: **Status** (Pass/Warning/Fail), **Description**,
**Current Value**, **Affected Element**, **Recommendation**, and **Severity**.

---

## Requirements

- Python 3.11+ (3.12 recommended)
- ~500 MB free disk space (Playwright's bundled Chromium browser)
- Internet access on the machine running this (to audit external URLs, and to download
  Chromium once during setup)

---

## Setup (run these once)

```bash
# 1. Unzip the project, then cd into it
cd seo_audit_tool

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright's Chromium browser binary (separate from the pip package —
#    this downloads the actual browser Playwright drives)
playwright install chromium

# 5. Create the SQLite database
python manage.py migrate
```

## Run it

```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser, paste a URL (e.g. `https://example.com`), and
click **Analyze**. The request will take a few seconds while Playwright loads and renders the
page — that's expected, there's no background job or polling, it's one straightforward request.

---

## Project layout

```
seo_audit_tool/
├── manage.py
├── requirements.txt
├── config/                  # Django project settings, root urls
├── audits/                  # the one Django app
│   ├── models.py            # Audit, AuditIssue
│   ├── forms.py             # URL input validation
│   ├── views.py             # index / analyze / report — the whole synchronous flow
│   ├── services/
│   │   ├── security.py      # SSRF guard (validates the URL before AND after crawling)
│   │   ├── crawler.py       # PlaywrightCrawler — loads exactly one page
│   │   ├── parser.py        # BeautifulSoup/lxml extraction from the rendered HTML
│   │   └── scorer.py        # weighted 0–100 score from the rule findings
│   ├── rules/                # one small file per SEO category, each returns Issue objects
│   ├── templates/audits/     # index.html (search box) + report.html (dashboard)
│   └── static/audits/js/     # small vanilla JS: button state + table filtering
└── media/screenshots/        # saved page screenshots, one PNG per audit
```

---

## Notes on how it works

- **Single page only**: `PlaywrightCrawler.fetch()` calls `page.goto()` exactly once. Popups the
  page's own JS tries to open are closed immediately. Nothing is clicked, nothing is scrolled,
  no second navigation is ever triggered.
- **Rendered DOM, not raw HTML**: the crawler waits for the `load` event, then does a best-effort
  extra wait for `networkidle` (bounded, so JS-heavy sites that poll forever don't hang the
  request), then captures `page.content()` — the DOM *after* JavaScript has run. That's what every
  rule in `audits/rules/` is checked against.
- **SSRF protection**: `services/security.py` validates the submitted URL's resolved IP address
  before it's ever handed to the browser (rejecting private/loopback/link-local ranges), and
  re-checks the *final* URL after any redirect, since a public URL could redirect somewhere
  internal.
- **Broken-link checks** use lightweight HEAD/GET status checks (capped at 20 links, short
  timeout) against links found *on* the submitted page — this never renders or crawls those
  linked pages, it only checks their HTTP status, and each candidate URL passes through the same
  SSRF guard first.
- **No mock data**: every number in the report — score, word count, link counts, meta tag values,
  screenshot — comes from the actual page that was fetched at request time.

---

## Troubleshooting

- **Every URL times out, even simple/fast ones**: this was a known issue in earlier builds of this
  project, now fixed. Chromium tries to auto-detect a system proxy (WPAD) before every navigation,
  and on many Windows machines that lookup alone can take 10-30+ seconds *before the target site is
  even contacted* - which looks exactly like every URL being slow/unreachable. The crawler now
  launches Chromium with `--no-proxy-server` to skip that lookup and force a direct connection. If
  you *do* need to go through a corporate proxy to reach the internet, remove that flag in
  `audits/services/crawler.py` and instead pass Playwright's `proxy={"server": "http://your-proxy:port"}`
  option to `chromium.launch()`.
- **`playwright install chromium` fails or hangs**: check your network/firewall allows downloads
  from Playwright's CDN. Corporate proxies sometimes block this.
- **A specific site returns an error in the report**: some sites block headless browsers or take
  longer than the 20s navigation timeout. The report will show a clear error message rather than
  fabricating a result — try again, or adjust `SEO_AUDIT_NAVIGATION_TIMEOUT_MS` in
  `config/settings.py`.
- **Screenshots not showing**: confirm the `media/screenshots/` folder is writable; Django serves
  it automatically in this dev setup (`DEBUG = True` in `config/settings.py`).
