from urllib.error import URLError

import pytest

from doonsec_push import rss
from doonsec_push.rss import fetch_rss_text, normalize_link, parse_pub_date, parse_rss


def test_parse_rss_extracts_required_fields() -> None:
    rss_text = """<?xml version="1.0" encoding="utf-8"?>
    <rss version="2.0">
      <channel>
        <item>
          <title>测试标题</title>
          <link>https://mp.weixin.qq.com/s/abc#frag</link>
          <author>测试作者</author>
          <pubDate>2026-04-23T13:46:36</pubDate>
        </item>
      </channel>
    </rss>
    """

    articles = parse_rss(rss_text)

    assert len(articles) == 1
    assert articles[0].title == "测试标题"
    assert articles[0].link == "https://mp.weixin.qq.com/s/abc"
    assert articles[0].author == "测试作者"
    assert articles[0].published_at.isoformat() == "2026-04-23T13:46:36+08:00"


def test_normalize_link_drops_fragment() -> None:
    assert normalize_link("https://Example.com/a/b?x=1#frag") == "https://example.com/a/b?x=1"


def test_parse_pub_date_adds_shanghai_timezone_for_naive_timestamp() -> None:
    parsed = parse_pub_date("2026-04-23T09:40:00")
    assert parsed.isoformat() == "2026-04-23T09:40:00+08:00"


def test_fetch_rss_text_retries_transient_fetch_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
            return None

        def read(self) -> bytes:
            return b"<rss></rss>"

    calls = 0

    def fake_urlopen(request: object, timeout: int) -> FakeResponse:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise URLError("ssl handshake timed out")
        return FakeResponse()

    sleep_delays: list[int] = []
    monkeypatch.setattr(rss, "urlopen", fake_urlopen)
    monkeypatch.setattr(rss.time, "sleep", sleep_delays.append)

    result = fetch_rss_text("https://wechat.doonsec.com/rss.xml", attempts=2, timeout=1)

    assert result == "<rss></rss>"
    assert calls == 2
    assert sleep_delays == [10]


def test_fetch_rss_text_raises_after_retry_exhaustion(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request: object, timeout: int) -> object:
        raise URLError("ssl handshake timed out")

    sleep_delays: list[int] = []
    monkeypatch.setattr(rss, "urlopen", fake_urlopen)
    monkeypatch.setattr(rss.time, "sleep", sleep_delays.append)

    with pytest.raises(RuntimeError, match="RSS fetch failed after 3 attempts"):
        fetch_rss_text("https://wechat.doonsec.com/rss.xml", attempts=3, timeout=1)

    assert sleep_delays == [10, 30]
