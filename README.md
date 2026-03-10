# 📡 Telegram Deal Scraper

A private, production-grade Python bot that listens to selected Telegram channels in real time, extracts deal links and metadata, and forwards structured payloads to an **n8n** webhook for downstream automation (notifications, filtering, database storage, etc.).

---

## 🧠 How It Works

```
Telegram Channels
      │
      ▼
  Telethon Client (loop.py)
  ├── Listens for new & edited messages
  ├── Deduplicates by message ID
  ├── Extracts URLs via regex
  ├── Fetches channel metadata
  └── Sends JSON payload → n8n Webhook → Automation
```

1. The bot connects to Telegram using the **Telethon** MTProto client.
2. It monitors multiple target channels for new and edited messages.
3. Any message containing a URL is parsed and enriched with channel info.
4. The payload is forwarded to an **n8n webhook** with retry logic.
5. n8n handles downstream processing (filtering, alerting, storage, etc.).

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Telegram Client | [Telethon](https://docs.telethon.dev/) (MTProto API) |
| HTTP Client | [aiohttp](https://docs.aiohttp.org/) |
| Env Management | [python-dotenv](https://pypi.org/project/python-dotenv/) |
| Async Runtime | Python `asyncio` |
| Automation Backend | [n8n](https://n8n.io/) (self-hosted) |
| Process Manager | [PM2](https://pm2.keymetrics.io/) |
| Deployment | Ubuntu VPS (SSH) |
| CI/CD | GitHub Actions |

---

## 📁 Project Structure

```
telegram-scraper/
├── loop.py                  # Main bot script
├── requirements.txt         # Python dependencies
├── Procfile                 # Worker process declaration
├── .env                     # Secret credentials (not committed)
├── .gitignore
├── deal_listener.session    # Telethon session file (auto-generated)
└── .github/
    └── workflows/
        └── deploy.yml       # CD: auto-deploy to VPS on push to main
```

---

## ⚙️ Environment Variables

Create a `.env` file in the project root (never commit this):

```env
TG_API_ID=your_telegram_api_id
TG_API_HASH=your_telegram_api_hash
```

Get your API credentials from [https://my.telegram.org](https://my.telegram.org) → **API development tools**.

---

## 🚀 Local Setup

### Prerequisites
- Python 3.11+
- A Telegram account
- Telegram API credentials from [my.telegram.org](https://my.telegram.org)

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/SSRNServices/telegram-scraper.git
cd telegram-scraper

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
echo "TG_API_ID=your_api_id" > .env
echo "TG_API_HASH=your_api_hash" >> .env

# 5. Run the bot (first run will ask for your phone number & OTP)
python loop.py
```

> **First run:** Telethon will prompt for your phone number and a login code sent via Telegram. This creates the `deal_listener.session` file. Subsequent runs use this session silently.

---

## 🖥️ VPS Deployment (Production)

The bot runs on an Ubuntu VPS managed by **PM2**.

### VPS Details
- **Host:** `210.56.146.156`
- **User:** `ubuntu`
- **App directory:** `/var/www/telegram-scraper`

### One-time VPS Setup

```bash
# SSH into VPS
ssh ubuntu@210.56.146.156

# Install Node.js & PM2 (if not already installed)
sudo apt update && sudo apt install -y nodejs npm
sudo npm install -g pm2

# Clone the repo
sudo mkdir -p /var/www/telegram-scraper
cd /var/www/telegram-scraper
git clone https://github.com/SSRNServices/telegram-scraper.git .

# Install Python dependencies
pip install -r requirements.txt --break-system-packages

# Create .env on the server
nano .env
# Paste: TG_API_ID=... and TG_API_HASH=...

# Run once interactively to generate the session file
python3 loop.py
# Complete the Telegram login, then Ctrl+C

# Start with PM2
pm2 start loop.py --name telegram-scraper --interpreter python3
pm2 save

# Auto-start PM2 on server reboot
pm2 startup
# Run the command it outputs
```

### PM2 Management Commands

```bash
pm2 status                            # View all processes
pm2 logs telegram-scraper             # Live logs
pm2 logs telegram-scraper --lines 100 # Last 100 lines
pm2 restart telegram-scraper          # Manual restart
pm2 stop telegram-scraper             # Stop the bot
pm2 delete telegram-scraper           # Remove from PM2
```

---

## 🔄 CI/CD — GitHub Actions

Every push to `main` automatically deploys to the VPS.

### Pipeline: `.github/workflows/deploy.yml`

```
Push to main
     │
     ▼
GitHub Actions Runner (ubuntu-latest)
     │
     └── SSH into VPS
           ├── git pull origin main
           ├── pip install -r requirements.txt
           └── pm2 restart telegram-scraper (or start if new)
```

### Required GitHub Secrets

Set these at: **Repo → Settings → Secrets and variables → Actions**

| Secret | Value |
|---|---|
| `VPS_HOST` | `210.56.146.156` |
| `VPS_USER` | `ubuntu` |
| `VPS_SSH_KEY` | Private SSH key for VPS access |

To get your private key:
```bash
cat ~/.ssh/id_rsa
```
Copy the full output (including `-----BEGIN ... -----` lines) as the secret value.

---

## 📦 Webhook Payload

Each matched message sends a JSON payload to the configured n8n webhook:

```json
{
  "message_id": 12345,
  "channel_id": -1001234567890,
  "channel_name": "Loot Deals",
  "channel_username": "LootDeals193",
  "text": "Full message text here...",
  "urls": ["https://amzn.in/d/xyz", "https://example.com"],
  "image": "https://t.me/LootDeals193/12345",
  "date": "2026-03-10 10:15:00+00:00"
}
```

---

## 🔒 Security Notes

- `.env` is **gitignored** — credentials are never committed.
- The Telethon session file (`*.session`) is **gitignored** to prevent account hijacking.
- SSH access to the VPS uses key-based authentication only.
- Telegram API credentials are stored only in `.env` on the VPS server.

---

## 🔧 Configuration

To add or remove monitored channels, edit `loop.py`:

```python
target_channels = [
    "@NadyMods",
    "@LootDeals193",
    # Add more channels here
]
```

To change the n8n webhook URL:
```python
webhook_url = "https://n8n.ssrn.online/webhook-test/..."
```

---

## 📋 Dependencies

```
telethon        # Telegram MTProto client
aiohttp         # Async HTTP for webhook delivery
python-dotenv   # .env file loading
```

Install: `pip install -r requirements.txt`
