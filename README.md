# 🤖 Automated Job Monitoring Bot

An autonomous bot that continuously monitors job portals and notifies you **only when new job postings appear**, avoiding duplicates and unnecessary noise.

## 🚀 Overview

This project automates the process of tracking job offers across multiple job portals. It runs on a fixed schedule, detects **only newly published jobs**, stores a persistent history, and sends direct links instantly.

Ideal for developers, recruiters, or job seekers who want **real-time job alerts** without manually checking job boards.

## ✨ Key Features

- ⏱ Runs automatically **every 30 minutes**
- 🔍 Scans multiple job portals
- 🆕 Detects **only new job postings**
- 💾 Stores a persistent history of processed jobs
- 📲 Sends **direct links** to new job offers
- ❌ Prevents duplicate or repeated notifications
- 🤖 Fully autonomous execution

## 🧠 How It Works

1. The bot fetches data from configured job portals.
2. Each job posting is normalized and uniquely identified.
3. New postings are compared against the stored history.
4. Only unseen jobs are saved and sent as notifications.
5. Previously processed jobs are ignored automatically.

## 📦 Installation

### Requirements

- Python 3.9+
- pip
- Virtual environment (recommended)

### Setup

```bash
git clone https://github.com/your-username/job-monitoring-bot.git
cd job-monitoring-bot
python -m venv venv
source venv/bin/activate  # Linux / macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

## ▶️ Usage

Run the bot manually:

```bash
python main.py
python telegram_bot.py
```

For continuous operation, schedule it using `cron`, Task Scheduler, or a process manager so it runs every 30 minutes.

If you find this project useful, feel free to ⭐ star the repository and contribute.
