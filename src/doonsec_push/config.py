from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from .models import Slot


SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
DEFAULT_RSS_URL = "https://wechat.doonsec.com/rss.xml"
DEFAULT_MINIMAX_BASE_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"
DEFAULT_STATE_FILE = "data/sent_state.json"


@dataclass(slots=True, frozen=True)
class Config:
    rss_url: str
    state_file: str
    dingtalk_webhook: str | None
    dingtalk_secret: str | None
    minimax_api_key: str | None
    minimax_base_url: str
    slot: str
    dry_run: bool
    now: datetime


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Fetch Doonsec RSS and push to DingTalk.")
    parser.add_argument("--slot", choices=["morning", "afternoon", "auto"], default="auto")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--now", help="Override current time with an ISO-8601 datetime.")
    args = parser.parse_args()

    now = datetime.now(tz=SHANGHAI_TZ)
    if args.now:
        parsed = datetime.fromisoformat(args.now)
        now = parsed if parsed.tzinfo else parsed.replace(tzinfo=SHANGHAI_TZ)
        now = now.astimezone(SHANGHAI_TZ)

    return Config(
        rss_url=os.getenv("RSS_URL") or DEFAULT_RSS_URL,
        state_file=os.getenv("STATE_FILE") or DEFAULT_STATE_FILE,
        dingtalk_webhook=os.getenv("DINGTALK_WEBHOOK") or None,
        dingtalk_secret=os.getenv("DINGTALK_SECRET") or None,
        minimax_api_key=os.getenv("MINIMAX_API_KEY") or None,
        minimax_base_url=normalize_minimax_url(os.getenv("MINIMAX_BASE_URL") or DEFAULT_MINIMAX_BASE_URL),
        slot=args.slot,
        dry_run=args.dry_run,
        now=now,
    )


def resolve_slot(now: datetime, requested_slot: str) -> tuple[Slot, datetime]:
    if requested_slot == Slot.MORNING:
        return Slot.MORNING, now
    if requested_slot == Slot.AFTERNOON:
        return Slot.AFTERNOON, now

    current = now.astimezone(SHANGHAI_TZ)
    morning_cutoff = current.replace(hour=9, minute=40, second=0, microsecond=0)
    afternoon_cutoff = current.replace(hour=16, minute=5, second=0, microsecond=0)

    if current >= afternoon_cutoff:
        return Slot.AFTERNOON, current
    if current >= morning_cutoff:
        return Slot.MORNING, current
    return Slot.AFTERNOON, current - timedelta(days=1)


def normalize_minimax_url(raw_url: str) -> str:
    trimmed = raw_url.rstrip("/")
    parsed = urlparse(trimmed)
    path = parsed.path.rstrip("/")

    if path.endswith("/v1/text/chatcompletion_v2"):
        return trimmed
    if path.endswith("/v1"):
        return f"{trimmed}/text/chatcompletion_v2"
    if parsed.scheme and parsed.netloc:
        return f"{trimmed}/v1/text/chatcompletion_v2"
    return DEFAULT_MINIMAX_BASE_URL
