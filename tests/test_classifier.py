from doonsec_push.classifier import classify_article
from doonsec_push.models import Article, Category
from doonsec_push.config import SHANGHAI_TZ
from datetime import datetime


def build_article(title: str, author: str = "测试安全") -> Article:
    return Article(
        title=title,
        link="https://mp.weixin.qq.com/s/test",
        author=author,
        published_at=datetime(2026, 4, 23, 9, 40, tzinfo=SHANGHAI_TZ),
    )


def test_classifier_drops_training_and_promotion_content() -> None:
    decision = classify_article(build_article("5月认证培训开班啦！课程火热报名中"))
    assert decision.keep is False


def test_classifier_marks_vulnerability_articles() -> None:
    decision = classify_article(build_article("Progress ShareFile 远程代码执行漏洞(CVE-2026-2701)"))
    assert decision.keep is True
    assert decision.category == Category.VULNERABILITY


def test_classifier_marks_ai_security_articles() -> None:
    decision = classify_article(build_article("AI投毒情报预警 | Xinference国产推理框架遭受供应链窃密后门投毒"))
    assert decision.keep is True
    assert decision.category == Category.AI_SECURITY


def test_classifier_drops_generic_ai_procurement_articles() -> None:
    decision = classify_article(build_article("国务院：支持采购大模型、智能体服务", author="智探AI应用"))
    assert decision.keep is False


def test_classifier_does_not_keep_irrelevant_title_only_because_author_looks_security_related() -> None:
    decision = classify_article(build_article("中国氢能“十五五”迎来爆发拐点", author="网络安全直通车"))
    assert decision.keep is False


def test_classifier_routes_vulnerability_mining_to_offensive_practice() -> None:
    decision = classify_article(build_article("记一次某大学的漏洞挖掘"))
    assert decision.keep is True
    assert decision.category == Category.OFFENSIVE


def test_classifier_routes_static_site_vulnerability_case_to_offensive_practice() -> None:
    decision = classify_article(build_article("静态网站中存在的 20 多个漏洞"))
    assert decision.keep is True
    assert decision.category == Category.OFFENSIVE


def test_classifier_keeps_security_certification_knowledge() -> None:
    decision = classify_article(build_article("网络安全含金量最高的四个证书详细图解！"))
    assert decision.keep is True
    assert decision.category == Category.RESEARCH


def test_classifier_keeps_mythos_opinion_article() -> None:
    decision = classify_article(build_article("Mythos正在袪魅？"))
    assert decision.keep is True
    assert decision.category == Category.AI_SECURITY


def test_classifier_keeps_ai_assistant_tool_article() -> None:
    decision = classify_article(build_article("OpenClaw 适配普通人的纯免费Ai助手 | 家庭版介绍— 由浅到深的问题解决"))
    assert decision.keep is True
    assert decision.category == Category.AI_SECURITY
