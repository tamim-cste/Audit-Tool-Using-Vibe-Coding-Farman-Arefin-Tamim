"""
parse_page(): pure function turning rendered HTML into a plain dict of
facts. Has zero knowledge of scoring or pass/fail rules - it only extracts
what's actually in the document. The rule modules in audits/rules/ do all
the judgment calls.

Runs against the *rendered* HTML (post-JavaScript), as returned by
PlaywrightCrawler - never the raw server response body.
"""

import json
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


def parse_page(html: str, final_url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    base_domain = _normalize_domain(urlparse(final_url).netloc)

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    meta_description_tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    meta_description = (meta_description_tag.get("content") or "").strip() if meta_description_tag else ""

    canonical_tag = soup.find("link", attrs={"rel": _rel_contains("canonical")})
    canonical_url = (canonical_tag.get("href") or "").strip() if canonical_tag else ""

    robots_tag = soup.find("meta", attrs={"name": re.compile("^robots$", re.I)})
    robots_meta = (robots_tag.get("content") or "").strip() if robots_tag else ""

    html_tag = soup.find("html")
    lang = (html_tag.get("lang") or "").strip() if html_tag else ""

    charset = _extract_charset(soup)

    viewport_tag = soup.find("meta", attrs={"name": re.compile("^viewport$", re.I)})
    viewport = (viewport_tag.get("content") or "").strip() if viewport_tag else ""

    favicon_tag = soup.find("link", attrs={"rel": _rel_contains("icon")})
    favicon = (favicon_tag.get("href") or "").strip() if favicon_tag else ""

    headings = [
        {"tag": tag.name, "text": tag.get_text(strip=True)[:200]}
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    ]
    h1_count = sum(1 for h in headings if h["tag"] == "h1")

    images = [
        {"src": (img.get("src") or "").strip(), "alt": img.get("alt")}
        for img in soup.find_all("img")
    ]
    images_missing_alt = [img for img in images if not img.get("alt")]

    links = _extract_links(soup, final_url, base_domain)
    internal_links = [l for l in links if l["is_internal"] is True]
    external_links = [l for l in links if l["is_internal"] is False]
    nofollow_links = [l for l in links if "nofollow" in [r.lower() for r in l["rel"]]]

    og_tags = {
        tag.get("property"): (tag.get("content") or "")
        for tag in soup.find_all("meta", attrs={"property": re.compile("^og:", re.I)})
        if tag.get("property")
    }
    twitter_tags = {
        tag.get("name"): (tag.get("content") or "")
        for tag in soup.find_all("meta", attrs={"name": re.compile("^twitter:", re.I)})
        if tag.get("name")
    }

    json_ld_blocks = _extract_json_ld(soup)

    hreflang_links = [
        {"hreflang": tag.get("hreflang"), "href": (tag.get("href") or "").strip()}
        for tag in soup.find_all("link", attrs={"rel": re.compile("alternate", re.I), "hreflang": True})
    ]

    body_text = soup.get_text(separator=" ", strip=True)
    word_count = len(body_text.split())
    html_size_bytes = len(html.encode("utf-8"))
    text_html_ratio = round((len(body_text) / html_size_bytes) * 100, 2) if html_size_bytes else 0.0

    return {
        "final_url": final_url,
        "title": title,
        "meta_description": meta_description,
        "canonical_url": canonical_url,
        "robots_meta": robots_meta,
        "lang": lang,
        "charset": charset,
        "viewport": viewport,
        "favicon": favicon,
        "headings": headings,
        "h1_count": h1_count,
        "images": images,
        "image_count": len(images),
        "images_missing_alt": images_missing_alt,
        "links": links,
        "internal_links": internal_links,
        "external_links": external_links,
        "nofollow_links": nofollow_links,
        "og_tags": og_tags,
        "twitter_tags": twitter_tags,
        "json_ld_blocks": json_ld_blocks,
        "hreflang_links": hreflang_links,
        "word_count": word_count,
        "text_html_ratio": text_html_ratio,
        "html_size_kb": round(html_size_bytes / 1024, 1),
        "html_size_bytes": html_size_bytes,
    }


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _normalize_domain(netloc: str) -> str:
    netloc = netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def _rel_contains(needle: str):
    def matcher(value):
        if not value:
            return False
        values = value if isinstance(value, list) else str(value).split()
        return any(needle in v.lower() for v in values)
    return matcher


def _extract_charset(soup) -> str:
    charset_tag = soup.find("meta", attrs={"charset": True})
    if charset_tag:
        return charset_tag.get("charset", "")
    ct_tag = soup.find("meta", attrs={"http-equiv": re.compile("^content-type$", re.I)})
    if ct_tag:
        match = re.search(r"charset=([\w-]+)", ct_tag.get("content", ""), re.I)
        if match:
            return match.group(1)
    return ""


def _extract_links(soup, final_url, base_domain):
    links = []
    for a in soup.find_all("a"):
        href = (a.get("href") or "").strip()
        text = a.get_text(strip=True)
        rel = a.get("rel") or []
        if isinstance(rel, str):
            rel = rel.split()

        is_internal = None
        resolved = ""
        if href and not href.lower().startswith(("mailto:", "tel:", "javascript:")) and href != "#":
            resolved = urljoin(final_url, href)
            link_domain = _normalize_domain(urlparse(resolved).netloc)
            is_internal = (link_domain == base_domain) or link_domain == ""

        links.append({
            "href": href,
            "text": text,
            "rel": rel,
            "is_internal": is_internal,
            "resolved": resolved,
        })
    return links


def _extract_json_ld(soup):
    blocks = []
    for script in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)}):
        raw = (script.string or script.get_text() or "").strip()
        entry = {"raw": raw, "valid": False, "types": []}
        if raw:
            try:
                data = json.loads(raw)
                entry["valid"] = True
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict) and "@type" in item:
                        t = item["@type"]
                        entry["types"].extend(t if isinstance(t, list) else [t])
            except (json.JSONDecodeError, TypeError):
                pass
        blocks.append(entry)
    return blocks
