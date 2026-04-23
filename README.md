# 洞见网安 RSS 分类推送到钉钉

按北京时间 `09:40` 和 `16:05` 抓取 [Doonsec RSS](https://wechat.doonsec.com/rss.xml)，筛选网安相关文章，按分类整理后通过钉钉群机器人发送。

## 功能

- RSS 抓取与解析
- 上午/下午时间窗筛选
- 仓库内 JSON 状态持久化去重
- 标题优先的规则分类，MiniMax 兜底
- 钉钉 Markdown 推送
- GitHub Actions 定时执行与手动补跑

## 环境变量

- `DINGTALK_WEBHOOK`: 钉钉群机器人 Webhook
- `DINGTALK_SECRET`: 钉钉群机器人加签密钥
- `MINIMAX_API_KEY`: MiniMax API Key
- `MINIMAX_BASE_URL`: MiniMax 接口地址，可选。支持三种写法：域名、`/v1`、完整 `.../v1/text/chatcompletion_v2`，程序会自动补全。
- `RSS_URL`: RSS 源地址，可选，默认 `https://wechat.doonsec.com/rss.xml`
- `STATE_FILE`: 状态文件路径，可选，默认 `data/sent_state.json`

## 本地运行

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .[dev]
pytest
python -m doonsec_push --slot morning --dry-run
```

## 手动触发参数

- `--slot morning|afternoon|auto`
- `--dry-run`
- `--now 2026-04-23T09:40:00+08:00`

## 状态文件说明

`data/sent_state.json` 会记录：

- `initialized`: 是否完成首次上线初始化
- `seen_ids`: 已见过文章 ID
- `sent_ids`: 已发送文章 ID
- `last_successful_windows`: 最近一次成功处理的时间窗

首次上线时，只推送当前时间窗内文章；更早文章只记入已见状态，不推送。
