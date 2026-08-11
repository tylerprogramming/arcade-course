# Deploy the scheduled agent on a VPS (Hostinger)

Goal: the Morning Planner (`05-scheduled-agent/morning_planner.py`) runs every
morning on an **always-on box**, so it fires before you sit down — laptop open or
not. A small Hostinger VPS is plenty.

> Why a VPS and not local cron: local cron only fires if your machine is awake.
> A VPS is always on, so "it ran before I got up" is literally true.

## 1. One-time server setup (Ubuntu VPS)

```bash
ssh root@YOUR_VPS_IP
apt update && apt install -y python3-venv git
git clone <your project repo> arcade-course && cd arcade-course/project
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env        # paste ARCADE_API_KEY, ANTHROPIC_API_KEY, ARCADE_USER_ID
```

Authorize the tools once (interactive, so the OAuth URLs can be clicked):

```bash
cd 05-scheduled-agent
python morning_planner.py --discover     # confirm your ClickUp/Calendar tool names, set them
python morning_planner.py                # dry run: click the auth URLs it prints, confirm the plan looks right
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
30 6 * * *  cd /root/arcade-course/project/05-scheduled-agent && /root/arcade-course/project/.venv/bin/python morning_planner.py --apply >> /var/log/morning_planner.log 2>&1
```

## 2b. Or a systemd timer (nicer logs)

`/etc/systemd/system/morning-planner.service`
```ini
[Unit]
Description=Morning Planner agent

[Service]
Type=oneshot
WorkingDirectory=/root/arcade-course/project/05-scheduled-agent
ExecStart=/root/arcade-course/project/.venv/bin/python morning_planner.py --apply
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
systemctl list-timers | grep morning     # verify
journalctl -u morning-planner.service     # read a run's output
```

## Safety on a server
- Keep `--apply` writing to the wipeable **"AI Plan"** calendar until you fully trust it.
- `.env` holds only API keys (chmod 600 it). Arcade holds the OAuth tokens, not the box.
- Never commit `.env`. It's gitignored.

## Disclosure
If the Hostinger VPS is part of a Hostinger partnership, say so on camera + in the
description. Don't blend it with the Arcade disclosure — call each out where it appears.
