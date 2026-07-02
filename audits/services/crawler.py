"""
PlaywrightCrawler: loads exactly one URL and returns its fully-rendered
HTML, plus basic navigation metadata.

Constraints this module enforces (per project requirements):
  - Only ONE page.goto() call is ever made, on the exact submitted URL.
  - We never click anything, never scroll, never call goto() a second time.
  - Any popup / new tab the target page tries to open is closed immediately
    (page.on("popup", ...)) so a second document never gets rendered or
    analyzed.
  - We wait for "domcontentloaded" first (fires quickly and reliably, even
    on pages with slow-loading third-party trackers/ads), then make two
    further best-effort, independently-bounded attempts to wait for "load"
    and "networkidle" so JS-rendered content has a chance to settle. None of
    these extra waits can hang the request - each has its own timeout and a
    failure just means we analyze the DOM as it stood at that point.
  - The final rendered DOM (page.content(), i.e. after JS execution) is
    what gets returned - this is what every downstream SEO check runs
    against, not the raw server response body.

A redirect that the *browser itself* follows while loading the submitted
URL (e.g. http -> https, or a 301) is not a second page - it's normal URL
resolution for the one page being opened. We record both the submitted and
final URL so that's transparent in the report, but we never navigate
anywhere ourselves.
"""

import time

from django.conf import settings
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 SEOAuditToolBot/1.0"
)


class CrawlerError(Exception):
    """Raised when the target page could not be loaded/rendered."""


class PlaywrightCrawler:
    def __init__(self):
        self.navigation_timeout_ms = getattr(
            settings, "SEO_AUDIT_NAVIGATION_TIMEOUT_MS", 20000
        )
        self.network_idle_timeout_ms = getattr(
            settings, "SEO_AUDIT_NETWORK_IDLE_TIMEOUT_MS", 8000
        )

    def fetch(self, url: str, screenshot_path: str | None = None) -> dict:
        """Opens `url` in a headless browser, waits for it to fully render,
        and returns a dict with the rendered HTML and navigation metadata.
        Optionally saves a screenshot of the same page load to
        `screenshot_path` - no extra navigation is performed for this."""

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-gpu",
                        "--disable-dev-shm-usage",
                        # Chromium normally tries to auto-detect a proxy (WPAD) before
                        # every navigation. On many Windows machines this lookup can
                        # take 10-30+ seconds PER PAGE LOAD even when no proxy is
                        # actually in use - which reads exactly like "every URL times
                        # out, even simple ones". Forcing a direct connection skips
                        # that lookup entirely.
                        "--no-proxy-server",
                        "--disable-features=OutOfBlinkCors,AutoDetectProxySettings",
                    ],
                )
                try:
                    context = browser.new_context(
                        viewport={"width": 1366, "height": 900},
                        user_agent=DEFAULT_USER_AGENT,
                    )

                    # Close any popup/new-tab the page's own JS tries to
                    # open. We never let a second document get rendered.
                    def _close_popup(popup_page):
                        try:
                            popup_page.close()
                        except PlaywrightError:
                            pass

                    page = context.new_page()
                    page.on("popup", _close_popup)

                    start = time.monotonic()
                    response = page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=self.navigation_timeout_ms,
                    )

                    # Best-effort: let remaining resources (images, fonts, analytics
                    # beacons) finish, but never let a single slow resource hang the
                    # whole request - each wait has its own bounded timeout and a
                    # failure here just means we analyze the DOM as it stood.
                    try:
                        page.wait_for_load_state(
                            "load", timeout=self.navigation_timeout_ms
                        )
                    except PlaywrightTimeoutError:
                        pass
                    try:
                        page.wait_for_load_state(
                            "networkidle", timeout=self.network_idle_timeout_ms
                        )
                    except PlaywrightTimeoutError:
                        pass

                    load_time_ms = int((time.monotonic() - start) * 1000)

                    # Final rendered DOM, after JS execution - this is what
                    # every SEO rule runs against.
                    html = page.content()
                    final_url = page.url
                    status_code = response.status if response else None

                    if screenshot_path:
                        try:
                            page.screenshot(path=screenshot_path)
                        except PlaywrightError:
                            pass
                finally:
                    browser.close()

        except PlaywrightTimeoutError as exc:
            raise CrawlerError(
                f"The page took too long to load ({self.navigation_timeout_ms // 1000}s timeout). "
                f"If this happens for every URL you try (including simple/fast sites), it's "
                f"usually an environment issue rather than the target site - see the "
                f"Troubleshooting section in README.md."
            ) from exc
        except PlaywrightError as exc:
            msg = str(exc)
            if "Executable doesn't exist" in msg or "playwright install" in msg:
                raise CrawlerError(
                    "The Chromium browser binary isn't installed. Run "
                    "\"playwright install chromium\" in your virtual environment, then try again."
                ) from exc
            raise CrawlerError(f"Could not load the page: {msg}") from exc

        return {
            "html": html,
            "final_url": final_url,
            "status_code": status_code,
            "load_time_ms": load_time_ms,
        }
