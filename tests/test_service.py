from datetime import datetime

from doonsec_push.config import SHANGHAI_TZ
from doonsec_push.models import Article, Category, Slot
from doonsec_push.service import apply_successful_run, calculate_window, render_markdown, select_articles_for_window
from doonsec_push.state import State


def build_article(hour: int, minute: int, title: str, author: str = "测试作者", link_suffix: str = "a") -> Article:
    return Article(
        title=title,
        link=f"https://mp.weixin.qq.com/s/{link_suffix}",
        author=author,
        published_at=datetime(2026, 4, 23, hour, minute, tzinfo=SHANGHAI_TZ),
    )


def test_calculate_morning_window_spans_previous_afternoon() -> None:
    anchor = datetime(2026, 4, 23, 9, 40, tzinfo=SHANGHAI_TZ)
    window = calculate_window(Slot.MORNING, anchor)
    assert window.start.isoformat() == "2026-04-22T16:05:00+08:00"
    assert window.end.isoformat() == "2026-04-23T09:40:00+08:00"


def test_first_run_only_sends_current_window_articles() -> None:
    articles = [
        Article("旧文章", "https://mp.weixin.qq.com/s/old", "测试安全", datetime(2026, 4, 22, 15, 0, tzinfo=SHANGHAI_TZ)),
        Article("Flowise fetch-links ssrf漏洞", "https://mp.weixin.qq.com/s/new", "测试安全", datetime(2026, 4, 23, 9, 39, tzinfo=SHANGHAI_TZ)),
    ]
    window = calculate_window(Slot.MORNING, datetime(2026, 4, 23, 9, 40, tzinfo=SHANGHAI_TZ))
    state = State(version=1, initialized=False, seen_ids=[], sent_ids=[], last_successful_windows={Slot.MORNING: None, Slot.AFTERNOON: None})

    result = select_articles_for_window(articles, window, state)

    assert len(result.classified) == 1
    assert result.classified[0].category == Category.VULNERABILITY
    assert "https://mp.weixin.qq.com/s/old" not in result.sent_ids
    assert "https://mp.weixin.qq.com/s/old" in state.seen_ids


def test_render_markdown_groups_articles_by_category() -> None:
    window = calculate_window(Slot.MORNING, datetime(2026, 4, 23, 9, 40, tzinfo=SHANGHAI_TZ))
    state = State(version=1, initialized=True, seen_ids=[], sent_ids=[], last_successful_windows={Slot.MORNING: None, Slot.AFTERNOON: None})
    articles = [
        build_article(9, 30, "Flowise fetch-links ssrf漏洞", link_suffix="vuln"),
        build_article(9, 31, "WolfShell内存级WebShell管理工具", link_suffix="tool"),
    ]
    result = select_articles_for_window(articles, window, state)
    markdown = render_markdown(result.classified)
    assert "### 漏洞预警与风险通报" in markdown
    assert "### 安全工具与工程实践" in markdown
    assert "[Flowise fetch-links ssrf漏洞 - 测试作者](https://mp.weixin.qq.com/s/vuln)" in markdown


def test_apply_successful_run_updates_state() -> None:
    state = State(version=1, initialized=False, seen_ids=[], sent_ids=[], last_successful_windows={Slot.MORNING: None, Slot.AFTERNOON: None})
    articles = [build_article(9, 35, "Flowise fetch-links ssrf漏洞", link_suffix="vuln")]
    window = calculate_window(Slot.MORNING, datetime(2026, 4, 23, 9, 40, tzinfo=SHANGHAI_TZ))
    result = select_articles_for_window(articles, window, state)

    apply_successful_run(state, Slot.MORNING, result)

    assert state.initialized is True
    assert "https://mp.weixin.qq.com/s/vuln" in state.sent_ids
    assert state.last_successful_windows["morning"]["end"] == "2026-04-23T09:40:00+08:00"
