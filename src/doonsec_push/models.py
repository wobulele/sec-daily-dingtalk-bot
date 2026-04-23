from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Slot(StrEnum):
    MORNING = "morning"
    AFTERNOON = "afternoon"


class Category(StrEnum):
    THREAT_INTEL = "威胁情报与攻击活动"
    VULNERABILITY = "漏洞预警与风险通报"
    OFFENSIVE = "攻防实战与渗透测试"
    TOOLS = "安全工具与工程实践"
    AI_SECURITY = "AI安全与大模型治理"
    POLICY = "政策法规与行业动态"
    RESEARCH = "研究报告与标准解读"


CATEGORY_ORDER = [
    Category.THREAT_INTEL,
    Category.VULNERABILITY,
    Category.OFFENSIVE,
    Category.TOOLS,
    Category.AI_SECURITY,
    Category.POLICY,
    Category.RESEARCH,
]


@dataclass(slots=True, frozen=True)
class Article:
    title: str
    link: str
    author: str
    published_at: datetime


@dataclass(slots=True, frozen=True)
class ClassifiedArticle:
    article: Article
    category: Category

