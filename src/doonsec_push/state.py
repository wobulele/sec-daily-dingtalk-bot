from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .models import Slot


MAX_IDS = 4000


@dataclass(slots=True)
class State:
    version: int
    initialized: bool
    seen_ids: list[str]
    sent_ids: list[str]
    last_successful_windows: dict[str, dict[str, str] | None]
    last_runs: dict[str, dict[str, object] | None]


def load_state(path: str) -> State:
    state_path = Path(path)
    if not state_path.exists():
        return State(
            version=1,
            initialized=False,
            seen_ids=[],
            sent_ids=[],
            last_successful_windows={Slot.MORNING: None, Slot.AFTERNOON: None},
            last_runs={Slot.MORNING: None, Slot.AFTERNOON: None},
        )

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    return State(
        version=payload.get("version", 1),
        initialized=payload.get("initialized", False),
        seen_ids=list(payload.get("seen_ids", [])),
        sent_ids=list(payload.get("sent_ids", [])),
        last_successful_windows=payload.get(
            "last_successful_windows",
            {Slot.MORNING: None, Slot.AFTERNOON: None},
        ),
        last_runs=payload.get("last_runs", {Slot.MORNING: None, Slot.AFTERNOON: None}),
    )


def save_state(path: str, state: State) -> None:
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": state.version,
        "initialized": state.initialized,
        "seen_ids": state.seen_ids[-MAX_IDS:],
        "sent_ids": state.sent_ids[-MAX_IDS:],
        "last_successful_windows": state.last_successful_windows,
        "last_runs": state.last_runs,
    }
    state_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
