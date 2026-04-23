from __future__ import annotations

import json
import sys

from .classifier import MiniMaxClient
from .config import parse_args, resolve_slot
from .dingtalk import send_markdown
from .rss import fetch_rss_text, parse_rss
from .service import apply_successful_run, calculate_window, render_markdown, select_articles_for_window
from .state import load_state, save_state


def main() -> int:
    config = parse_args()
    slot, anchor = resolve_slot(config.now, config.slot)
    state = load_state(config.state_file)
    articles = parse_rss(fetch_rss_text(config.rss_url))
    minimax_client = MiniMaxClient(config.minimax_api_key, config.minimax_base_url)

    window = calculate_window(slot, anchor)
    result = select_articles_for_window(articles, window, state, minimax_client=minimax_client)
    markdown = render_markdown(result.classified)

    if not config.dry_run and markdown:
        if not (config.dingtalk_webhook and config.dingtalk_secret):
            raise RuntimeError("DINGTALK_WEBHOOK and DINGTALK_SECRET are required for non-dry-run execution.")
        send_markdown(config.dingtalk_webhook, config.dingtalk_secret, markdown)

    if not config.dry_run:
        apply_successful_run(state, slot, result, trigger=config.trigger, started_at=config.now)
        save_state(config.state_file, state)

    summary = {
        "slot": slot,
        "dry_run": config.dry_run,
        "window_start": result.window.start.isoformat(),
        "window_end": result.window.end.isoformat(),
        "classified_count": len(result.classified),
        "sent_count": len(result.sent_ids),
        "trigger": config.trigger,
    }
    print(json.dumps(summary, ensure_ascii=False))
    if markdown:
        print(markdown)
    else:
        print("No new articles to send.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
