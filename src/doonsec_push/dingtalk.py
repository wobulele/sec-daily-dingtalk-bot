from __future__ import annotations

import base64
import hashlib
import hmac
import json
from urllib.parse import urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen


def sign_webhook(webhook: str, secret: str) -> str:
    timestamp = _current_millis()
    string_to_sign = f"{timestamp}\n{secret}"
    digest = hmac.new(secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha256).digest()
    sign = base64.b64encode(digest).decode("utf-8")

    parsed = urlparse(webhook)
    query = parsed.query
    extra = urlencode({"timestamp": timestamp, "sign": sign})
    joined_query = f"{query}&{extra}" if query else extra
    return urlunparse(parsed._replace(query=joined_query))


def send_markdown(webhook: str, secret: str, markdown_text: str) -> None:
    signed_webhook = sign_webhook(webhook, secret)
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "洞见网安 RSS 推送",
            "text": markdown_text,
        },
    }
    request = Request(
        signed_webhook,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        body = json.loads(response.read().decode("utf-8"))
    if body.get("errcode") != 0:
        raise RuntimeError(f"DingTalk push failed: {body}")


def _current_millis() -> int:
    import time

    return int(round(time.time() * 1000))
