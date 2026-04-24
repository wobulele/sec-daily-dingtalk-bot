# 洞见网安 RSS 分类推送到钉钉

按北京时间 `09:40` 和 `16:05` 抓取 [Doonsec RSS](https://wechat.doonsec.com/rss.xml)，筛选网安相关文章，按分类整理后通过钉钉群机器人发送。

## 功能

- RSS 抓取与解析
- 上午/下午时间窗筛选
- 仓库内 JSON 状态持久化去重
- 标题优先的规则分类，MiniMax 兜底
- 钉钉 Markdown 推送
- Debian cron 定时执行
- GitHub Actions 手动补跑

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

## Debian 服务器部署

当前项目是 Python 脚本，不需要 Node.js。

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip cron util-linux
sudo mkdir -p /opt/sec-daily-dingtalk-bot
sudo chown -R "$USER:$USER" /opt/sec-daily-dingtalk-bot
sudo mkdir -p /var/lib/sec-daily-dingtalk-bot
sudo chown -R "$USER:$USER" /var/lib/sec-daily-dingtalk-bot
git clone https://github.com/wobulele/sec-daily-dingtalk-bot.git /opt/sec-daily-dingtalk-bot
cd /opt/sec-daily-dingtalk-bot
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .[dev]
cp .env.example .env
chmod 600 .env
chmod +x scripts/run_doonsec_push.sh
```

编辑 `.env`，填入 `DINGTALK_WEBHOOK`、`DINGTALK_SECRET`、`MINIMAX_API_KEY`。

先手动验证：

```bash
pytest
./scripts/run_doonsec_push.sh morning --dry-run
./scripts/run_doonsec_push.sh afternoon --dry-run
./scripts/run_doonsec_push.sh afternoon
tail -n 80 logs/doonsec_push.log
```

## Debian cron

执行：

```bash
crontab -e
```

加入：

```cron
CRON_TZ=Asia/Shanghai
40 9 * * * APP_DIR=/opt/sec-daily-dingtalk-bot /opt/sec-daily-dingtalk-bot/scripts/run_doonsec_push.sh morning
5 16 * * * APP_DIR=/opt/sec-daily-dingtalk-bot /opt/sec-daily-dingtalk-bot/scripts/run_doonsec_push.sh afternoon
```

检查 cron：

```bash
crontab -l
systemctl status cron --no-pager
tail -n 80 /opt/sec-daily-dingtalk-bot/logs/doonsec_push.log
```

GitHub Actions 已停止自动定时，只保留手动触发。

## 手动触发参数

- `--slot morning|afternoon|auto`
- `--dry-run`
- `--now 2026-04-23T09:40:00+08:00`

## 状态文件说明

GitHub 手动运行时，`data/sent_state.json` 会记录状态。Debian cron 部署时，默认把状态写到 `/var/lib/sec-daily-dingtalk-bot/sent_state.json`，避免 cron 运行后污染 Git 工作区。

状态文件会记录：

- `initialized`: 是否完成首次上线初始化
- `seen_ids`: 已见过文章 ID
- `sent_ids`: 已发送文章 ID
- `last_successful_windows`: 最近一次成功处理的时间窗
- `last_runs`: 最近一次真实运行的触发来源、开始时间和数量统计

首次上线时，只推送当前时间窗内文章；更早文章只记入已见状态，不推送。
