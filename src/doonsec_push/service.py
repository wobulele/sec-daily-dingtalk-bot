from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

from .classifier import ClassificationDecision, MiniMaxClient, classify_article
from .config import SHANGHAI_TZ
from .models import CATEGORY_ORDER, Article, Category, ClassifiedArticle, Slot
from .rss import article_fallback_id, article_id
from .state import State


@dataclass(slots=True, frozen=True)
class Window:
    start: datetime
    end: datetime


@dataclass(slots=True)
class RunResult:
    window: Window
    classified: list[ClassifiedArticle]
    sent_ids: list[str]
    seen_ids: list[str]
    initialized_state: bool


def calculate_window(slot: Slot, anchor: datetime) -> Window:
    current = anchor.astimezone(SHANGHAI_TZ)
    if slot == Slot.MORNING:
        end = current.replace(hour=9, minute=40, second=0, microsecond=0)
        start = (end - timedelta(days=1)).replace(hour=16, minute=0, second=0, microsecond=0)
        return Window(start=start, end=end)

    end = current.replace(hour=16, minute=0, second=0, microsecond=0)
    start = current.replace(hour=9, minute=40, second=0, microsecond=0)
    return Window(start=start, end=end)


def select_articles_for_window(
    articles: list[Article],
    window: Window,
    state: State,
    minimax_client: MiniMaxClient | None = None,
) -> RunResult:
    seen = set(state.seen_ids)
    sent = set(state.sent_ids)
    current_window_articles = [article for article in articles if window.start <= article.published_at < window.end]

    if not state.initialized:
        older_ids = [article_id(article) for article in articles if article.published_at < window.start]
        for older_id in older_ids:
            if older_id not in seen:
                state.seen_ids.append(older_id)
                seen.add(older_id)

    classified: list[ClassifiedArticle] = []
    processed_ids: list[str] = []

    for article in current_window_articles:
        current_id = article_id(article)
        fallback_id = article_fallback_id(article)
        processed_ids.extend([current_id, fallback_id])
        if current_id in sent or fallback_id in sent:
            continue

        decision = classify_article(article, minimax_client=minimax_client)
        if decision.keep and decision.category:
            classified.append(ClassifiedArticle(article=article, category=decision.category))

    return RunResult(
        window=window,
        classified=classified,
        sent_ids=[key for item in classified for key in (article_id(item.article), article_fallback_id(item.article))],
        seen_ids=processed_ids,
        initialized_state=True,
    )


def apply_successful_run(
    state: State,
    slot: Slot,
    result: RunResult,
    trigger: str = "local",
    started_at: datetime | None = None,
) -> None:
    seen = set(state.seen_ids)
    sent = set(state.sent_ids)

    for item in result.seen_ids:
        if item not in seen:
            state.seen_ids.append(item)
            seen.add(item)

    for item in result.sent_ids:
        if item not in sent:
            state.sent_ids.append(item)
            sent.add(item)

    state.initialized = result.initialized_state
    state.last_successful_windows[slot] = {
        "start": result.window.start.isoformat(),
        "end": result.window.end.isoformat(),
    }
    state.last_runs[slot] = {
        "trigger": trigger,
        "dry_run": False,
        "started_at": (started_at or datetime.now(tz=SHANGHAI_TZ)).astimezone(SHANGHAI_TZ).isoformat(),
        "window_start": result.window.start.isoformat(),
        "window_end": result.window.end.isoformat(),
        "classified_count": len(result.classified),
        "sent_count": len(result.sent_ids),
    }


def render_markdown(classified_articles: list[ClassifiedArticle]) -> str:
    grouped: dict[Category, list[ClassifiedArticle]] = defaultdict(list)
    for item in classified_articles:
        grouped[item.category].append(item)

    sections: list[str] = []
    for category in CATEGORY_ORDER:
        entries = grouped.get(category)
        if not entries:
            continue

        lines = [f"### {category.value}", ""]
        for entry in entries:
            lines.append(f"- [{entry.article.title} - {entry.article.author}]({entry.article.link})")
        sections.append("\n".join(lines))

    return "\n\n".join(sections)
