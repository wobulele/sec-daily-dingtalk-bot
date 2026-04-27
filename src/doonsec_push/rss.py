from __future__ import annotations

import hashlib
import sys
import time
from datetime import datetime
from urllib.error import URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from .config import SHANGHAI_TZ
from .models import Article


USER_AGENT = "Mozilla/5.0 (compatible; DoonsecDingTalkBot/1.0)"
DEFAULT_FETCH_ATTEMPTS = 4
DEFAULT_FETCH_TIMEOUT = 45
DEFAULT_RETRY_DELAYS = (10, 30, 60)


def fetch_rss_text(url: str, attempts: int = DEFAULT_FETCH_ATTEMPTS, timeout: int = DEFAULT_FETCH_TIMEOUT) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8")
        except (TimeoutError, URLError, OSError) as exc:
            last_error = exc
            if attempt == attempts:
                break

            delay = DEFAULT_RETRY_DELAYS[min(attempt - 1, len(DEFAULT_RETRY_DELAYS) - 1)]
            print(
                f"RSS fetch failed on attempt {attempt}/{attempts}: {exc}. Retrying in {delay}s.",
                file=sys.stderr,
                flush=True,
            )
            time.sleep(delay)

    raise RuntimeError(f"RSS fetch failed after {attempts} attempts: {last_error}") from last_error


def normalize_link(link: str) -> str:
    parsed = urlsplit(link.strip())
    netloc = parsed.netloc.lower()
    return urlunsplit((parsed.scheme or "https", netloc, parsed.path, parsed.query, ""))


def article_id(article: Article) -> str:
    normalized_link = normalize_link(article.link)
    if normalized_link:
        return normalized_link
    return article_fallback_id(article)


def article_fallback_id(article: Article) -> str:
    digest = hashlib.sha256(
        f"{article.title}|{article.author}|{article.published_at.isoformat()}".encode("utf-8")
    ).hexdigest()
    return digest


def parse_pub_date(raw_value: str) -> datetime:
    value = raw_value.strip()
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=SHANGHAI_TZ)
    return parsed.astimezone(SHANGHAI_TZ)


def parse_rss(text: str) -> list[Article]:
    root = ElementTree.fromstring(text)
    items = root.findall("./channel/item")
    articles: list[Article] = []

    for item in items:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        author = (item.findtext("author") or "").strip() or "未知发布者"
        pub_date = (item.findtext("pubDate") or "").strip()
        if not (title and link and pub_date):
            continue

        articles.append(
            Article(
                title=title,
                link=normalize_link(link),
                author=author,
                published_at=parse_pub_date(pub_date),
            )
        )

    articles.sort(key=lambda article: article.published_at)
    return articles
