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


def test_classifier_keeps_generic_ai_procurement_articles() -> None:
    decision = classify_article(build_article("国务院：支持采购大模型、智能体服务", author="智探AI应用"))
    assert decision.keep is True
    assert decision.category == Category.AI_SECURITY


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


def test_classifier_routes_intelligence_bills_to_policy() -> None:
    decision = classify_article(build_article("日本「国家情报会议」创设法案众议院通过", author="情报分析师"))
    assert decision.keep is True
    assert decision.category == Category.POLICY


def test_classifier_routes_security_tool_collections_to_tools_before_vulnerability() -> None:
    decision = classify_article(build_article("网络安全可视化工具集 |  FOFA 资产测绘爬取与 Nuclei 漏洞扫描"))
    assert decision.keep is True
    assert decision.category == Category.TOOLS


def test_classifier_routes_generic_large_model_articles_to_ai_security() -> None:
    decision = classify_article(build_article("小米大模型杀疯了：开源全球第一，还不要钱", author="数世咨询"))
    assert decision.keep is True
    assert decision.category == Category.AI_SECURITY


def test_classifier_routes_domestic_model_articles_to_ai_security() -> None:
    decision = classify_article(build_article("国产模型 Number One 是谁？", author="数世咨询"))
    assert decision.keep is True
    assert decision.category == Category.AI_SECURITY


def test_classifier_routes_bof_plugin_release_to_tools() -> None:
    decision = classify_article(build_article("丝滑绕过卡巴斯基、Defender！自研 BOF 维权插件 ccschtask 发布"))
    assert decision.keep is True
    assert decision.category == Category.TOOLS


def test_classifier_routes_robot_application_articles_to_ai_security() -> None:
    decision = classify_article(build_article("五一抢票崩溃？郑州东站的机器人 “新员工” 已经上岗了！"))
    assert decision.keep is True
    assert decision.category == Category.AI_SECURITY


def test_classifier_routes_recent_misclassified_titles() -> None:
    cases = [
        ("Kali200条命令，新手黑客小白必备！", Category.OFFENSIVE),
        ("躺平送外卖风雨兼程一天七八十，而挖漏洞半小时到手500，你会怎么选？", Category.POLICY),
        ("我们扫描了五万个 Skill，发现危险仍然存在", Category.AI_SECURITY),
        ("【安全圈】黑客利用 Breeze Cache WordPress 插件文件上传漏洞发动攻击", Category.VULNERABILITY),
        ("量芯筑盾 密护未来丨三未信安2026新产品发布会敬请期待", Category.POLICY),
        ("上海市发布自由贸易试验区、国家服务业扩大开放综合试点地区（上海）数据出境负面清单管理办法及负面清单", Category.POLICY),
        ("行业资讯：某单位网络安全服务项目，奇安信218万中标", Category.POLICY),
        ("行业资讯：某网络安全运行维护项目，北京金瑞亿98.9万中", Category.POLICY),
        ("行业资讯：某医院信息网络安全设备采购项目，新深信服是赢家", Category.POLICY),
        ("行业资讯：某学院网络安全综合演练平台和竞技平台项目423.6万中，奇安信锐捷等是赢家", Category.POLICY),
        ("行业资讯：某网络安全服务保障中心项目，中国电信绍兴分公司344.19万中", Category.POLICY),
        ("AI驱动攻破墨西哥政府机构：数亿条数据泄露背后的攻防启示录", Category.AI_SECURITY),
        ("决赛排名出炉！第二届腾讯云黑客松智能渗透挑战赛收官", Category.POLICY),
        ("【安全圈】UNC6692 通过微软 Teams 冒充 IT 服务台部署 SNOW 恶意软件", Category.THREAT_INTEL),
        ("【资料】美国陆军情报专员的入职条件", Category.POLICY),
        ("每周网安态势概览【20260426】017期", Category.POLICY),
        ("巅峰加冕！绿盟科技强势斩获“黑客松-智能渗透挑战赛”第一名", Category.POLICY),
        ("1984年这一天（42年前）Apple IIc 发布了", Category.POLICY),
        ("八部门联合发布《金融产品网络营销管理办法》", Category.POLICY),
        ("看懂银狐源码需要安全工程方面哪些知识？如何学习？", Category.THREAT_INTEL),
        ("国外：一周网络安全态势回顾之第147期，思科防火墙被植入“Firestarter”后门", Category.THREAT_INTEL),
        ("中国人民银行等八部门发布《金融产品网络营销管理办法》", Category.POLICY),
        ("日媒评论：马斯克对中国价值84亿美元的太空数据中心项目反应-有趣！", Category.POLICY),
        ("Claude Mythos安全神话：炒作还是名副其实？；白宫拟开放Claude漏洞挖掘AI | FreeBuf周报", Category.AI_SECURITY),
        ("关于发布第十一届CNCERT网络安全应急服务支撑单位遴选结果的通知", Category.POLICY),
        ("漏洞预警 | Windows截图工具信息泄露漏洞", Category.VULNERABILITY),
        ("美国 CISA 披露，联邦网络内思科 ASA 设备遭植入持久化 FIRESTARTER 后门", Category.THREAT_INTEL),
        ("实战复盘  如何通过 Apache 日志还原黑客的攻击链路？", Category.OFFENSIVE),
        ("如何通过漏洞组合链为工控平台CODESYS植入后门", Category.THREAT_INTEL),
        ("CPUID 被黑客入侵，可通过 CPU-Z 和 HWMonitor 下载传播恶意软件", Category.THREAT_INTEL),
        ("伊朗APT Seedworm通过微软Teams攻击全球组织", Category.THREAT_INTEL),
        ("MITRE ATT&CK 实战：如何通过对手模拟，让红队更像“真黑客”、蓝队不再被动挨打", Category.OFFENSIVE),
    ]

    for title, expected_category in cases:
        decision = classify_article(build_article(title))
        assert decision.keep is True, title
        assert decision.category == expected_category, title


def test_classifier_resolves_priority_conflicts() -> None:
    cases = [
        ("WordPress 插件文件上传漏洞发动攻击", Category.VULNERABILITY),
        ("MCP 工具扫描发现危险调用链", Category.AI_SECURITY),
        ("行业资讯：某安全设备采购项目 100 万中标", Category.POLICY),
        ("黑客松智能渗透挑战赛决赛排名出炉", Category.POLICY),
        ("MITRE ATT&CK 实战：红队对手模拟复盘", Category.OFFENSIVE),
    ]

    for title, expected_category in cases:
        decision = classify_article(build_article(title))
        assert decision.keep is True, title
        assert decision.category == expected_category, title
