from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.request import Request, urlopen

from .models import Article, Category


DROP_KEYWORDS = {
    "报名",
    "开班",
    "培训",
    "课程",
    "优惠",
    "抽奖",
    "直播",
    "沙龙",
    "大会",
    "峰会",
    "活动",
    "读书日",
    "限时注册",
    "套餐",
    "兑换",
    "合作",
    "莅临",
    "入选",
    "开幕",
    "启幕",
    "圆满举行",
    "圆满举办",
    "受邀演讲",
    "报名中",
    "知识星球",
    "促销",
    "礼品",
    "领取",
    "认证培训",
    "招聘",
    "内推",
    "事业编",
    "招募",
    "会员",
    "征集",
    "安心保障",
    "免费领",
    "比赛",
    "竞赛",
    "礼遇",
    "套餐",
    "沙龙成功举办",
    "读书月",
    "宣传短片",
    "供应商征集",
    "校企",
    "育英才",
    "产教融合",
    "人才培养",
    "服务公告",
    "数据库说明",
}

NON_SECURITY_AI_KEYWORDS = {"融资", "采购", "算力", "支付", "招聘", "服务项目", "采购大模型", "采购智能体"}
THREAT_KEYWORDS = {
    "apt",
    "勒索",
    "攻击",
    "钓鱼",
    "木马",
    "后门",
    "黑客",
    "暗网",
    "情报",
    "团伙",
    "投毒",
    "窃密",
    "供应链",
    "朝鲜it工人",
    "威胁通缉令",
    "样本",
}
VULNERABILITY_KEYWORDS = {
    "cve-",
    "ghsa-",
    "漏洞",
    "rce",
    "ssrf",
    "sql",
    "注入",
    "提权",
    "0day",
    "1day",
    "poc",
    "远程代码执行",
    "exploit",
}
OFFENSIVE_KEYWORDS = {
    "渗透",
    "红队",
    "蓝队",
    "红蓝",
    "内网",
    "免杀",
    "攻防",
    "靶场",
    "代码审计",
    "后渗透",
    "溯源",
}
TOOLS_KEYWORDS = {
    "工具",
    "框架",
    "开源",
    "项目",
    "star",
    "扫描",
    "管理工具",
    "知识库",
    "架构实践",
    "宝典",
    "浏览器保存的登录密码",
}
AI_SECURITY_KEYWORDS = {
    "ai",
    "人工智能",
    "大模型",
    "智能体",
    "agent",
    "提示词",
    "模型",
}
AI_SECURITY_GUARD_KEYWORDS = {
    "安全",
    "治理",
    "投毒",
    "风险",
    "攻击",
    "防护",
    "漏洞",
    "侵权",
    "合规",
    "提示词注入",
}
POLICY_KEYWORDS = {
    "国务院",
    "工信部",
    "网警",
    "处罚",
    "罚",
    "政策",
    "法规",
    "通报",
    "年报",
    "市场",
    "白皮书",
    "采购",
    "政府",
    "公安",
}
RESEARCH_KEYWORDS = {
    "报告",
    "白皮书",
    "论文",
    "标准",
    "gb/t",
    "解读",
    "学报",
    "综述",
    "数据库",
    "题库",
}

SECURITY_CONTEXT_KEYWORDS = THREAT_KEYWORDS | VULNERABILITY_KEYWORDS | OFFENSIVE_KEYWORDS | TOOLS_KEYWORDS | {
    "安全",
    "网安",
    "信安",
    "病毒",
    "数据安全",
    "网络安全",
}


@dataclass(slots=True, frozen=True)
class ClassificationDecision:
    keep: bool
    category: Category | None
    reason: str


class MiniMaxClient:
    def __init__(self, api_key: str | None, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url

    def classify(self, article: Article) -> ClassificationDecision | None:
        if not self.api_key:
            return None

        prompt = (
            "你是网络安全 RSS 文章分类器。"
            "请仅返回 JSON，字段为 keep(boolean)、category(string)、reason(string)。"
            "category 只能是：威胁情报与攻击活动、漏洞预警与风险通报、攻防实战与渗透测试、"
            "安全工具与工程实践、AI安全与大模型治理、政策法规与行业动态、研究报告与标准解读、DROP。"
            "如果标题属于培训、活动、广告、促销、明显非网安内容，则 keep=false 且 category=DROP。"
            f"标题：{article.title}\n发布者：{article.author}"
        )
        payload = {
            "model": "MiniMax-M2.7",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        }
        request = Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:
                body = json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

        content = _extract_message_content(body)
        if not content:
            return None

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return None

        keep = bool(parsed.get("keep"))
        category_label = str(parsed.get("category", "")).strip()
        reason = str(parsed.get("reason", "")).strip() or "minimax-fallback"
        if not keep or category_label == "DROP":
            return ClassificationDecision(keep=False, category=None, reason=reason)

        for category in Category:
            if category.value == category_label:
                return ClassificationDecision(keep=True, category=category, reason=reason)
        return None


def _extract_message_content(body: dict) -> str | None:
    choices = body.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = [part.get("text", "") for part in content if isinstance(part, dict)]
            return "".join(parts)
    return None


def classify_article(article: Article, minimax_client: MiniMaxClient | None = None) -> ClassificationDecision:
    title = normalize_text(article.title)
    author = normalize_text(article.author)

    if any(keyword in title for keyword in DROP_KEYWORDS):
        return ClassificationDecision(False, None, "drop-keyword")

    if _is_non_security_ai(title):
        return ClassificationDecision(False, None, "non-security-ai")

    if any(keyword in title for keyword in AI_SECURITY_KEYWORDS):
        if any(keyword in title for keyword in AI_SECURITY_GUARD_KEYWORDS) or "安全" in author:
            return ClassificationDecision(True, Category.AI_SECURITY, "ai-security-keyword")

    for keyword in VULNERABILITY_KEYWORDS:
        if keyword in title:
            return ClassificationDecision(True, Category.VULNERABILITY, "vulnerability-keyword")

    for keyword in THREAT_KEYWORDS:
        if keyword in title:
            return ClassificationDecision(True, Category.THREAT_INTEL, "threat-keyword")

    for keyword in OFFENSIVE_KEYWORDS:
        if keyword in title:
            return ClassificationDecision(True, Category.OFFENSIVE, "offensive-keyword")

    for keyword in TOOLS_KEYWORDS:
        if keyword in title:
            return ClassificationDecision(True, Category.TOOLS, "tools-keyword")

    for keyword in POLICY_KEYWORDS:
        if keyword in title:
            return ClassificationDecision(True, Category.POLICY, "policy-keyword")

    for keyword in RESEARCH_KEYWORDS:
        if keyword in title:
            return ClassificationDecision(True, Category.RESEARCH, "research-keyword")

    if any(keyword in title for keyword in SECURITY_CONTEXT_KEYWORDS):
        if minimax_client:
            decision = minimax_client.classify(article)
            if decision:
                return decision
        return ClassificationDecision(True, Category.RESEARCH, "research-fallback")

    return ClassificationDecision(False, None, "out-of-scope")


def normalize_text(text: str) -> str:
    normalized = text.lower()
    normalized = re.sub(r"\s+", "", normalized)
    return normalized


def _is_non_security_ai(title: str) -> bool:
    if not any(keyword in title for keyword in AI_SECURITY_KEYWORDS):
        return False
    has_security_guard = any(keyword in title for keyword in AI_SECURITY_GUARD_KEYWORDS)
    has_non_security = any(keyword in title for keyword in NON_SECURITY_AI_KEYWORDS)
    return has_non_security and not has_security_guard
