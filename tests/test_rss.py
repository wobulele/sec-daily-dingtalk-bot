from doonsec_push.rss import normalize_link, parse_pub_date, parse_rss


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

