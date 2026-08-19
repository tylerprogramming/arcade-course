# Deploy the scheduled agent on a VPS

Goal: the Morning Planner (`05-scheduled-agent/morning_planner.py`) runs every
morning on an **always-on box**, so it fires before you sit down — laptop open or
not. A small VPS (Hostinger, DigitalOcean, Hetzner — any Ubuntu box) is plenty.

> Why a VPS and not local cron: local cron only fires if your machine is awake.
> A VPS is always on, so "it ran before I got up" is literally true.

## 1. One-time server setup (Ubuntu VPS)

```bash
ssh root@YOUR_VPS_IP
apt update && apt install -y git curl
curl -LsSf https://astral.sh/uv/install.sh | sh      # same uv you used locally
source ~/.bashrc

git clone https://github.com/tylerprogramming/arcade-course.git
cd arcade-course
uv sync                                              # fetches Python 3.12 + deps
cp .env.example .env && nano .env                    # ARCADE_API_KEY, your LLM key, ARCADE_USER_ID
chmod 600 .env
```

> **pip fallback** (no uv): `apt install -y python3-venv && python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt`.
> Then use `/root/arcade-course/.venv/bin/python` everywhere `uv run` appears below.

Authorize the tools once (interactive, so the OAuth URLs can be clicked):

```bash
uv run 05-scheduled-agent/morning_planner.py --discover  # confirm your ClickUp/Calendar tool names
uv run 05-scheduled-agent/morning_planner.py             # dry run: click the auth URLs, check the plan
```

After you approve once, Arcade stores the tokens for your `ARCADE_USER_ID`; later
scheduled runs authorize instantly with no prompt. No tokens live on the VPS.

## 2a. Schedule with cron (simplest)

```bash
crontab -e
```
Add (6:30am daily; adjust path + timezone):
```
CRON_TZ=America/New_York
30 6 * * *  cd /root/arcade-course && /root/.local/bin/uv run 05-scheduled-agent/morning_planner.py --apply >> /var/log/morning_planner.log 2>&1
```
(`which uv` gives you the absolute path — cron has almost no `PATH`, so it must be absolute.)

## 2b. Or a systemd timer (nicer logs)

`/etc/systemd/system/morning-planner.service`
```ini
[Unit]
Description=Morning Planner agent

[Service]
Type=oneshot
WorkingDirectory=/root/arcade-course
ExecStart=/root/.local/bin/uv run 05-scheduled-agent/morning_planner.py --apply
```

`/etc/systemd/system/morning-planner.timer`
```ini
[Unit]
Description=Run Morning Planner every morning

[Timer]
OnCalendar=*-*-* 06:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
systemctl daemon-reload
systemctl enable --now morning-planner.timer
systemctl list-timers | grep morning      # verify
journalctl -u morning-planner.service     # read a run's output
```

## Safety on a server
- Keep `--apply` writing to the wipeable **"AI Plan"** calendar (`PLAN_CALENDAR_ID` in `.env`) until you fully trust it.
- `.env` holds only API keys (`chmod 600` it). Arcade holds the OAuth tokens, not the box.
- Never commit `.env`. It's gitignored.
