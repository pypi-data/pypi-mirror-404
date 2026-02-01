<div align="center">
  <h1>🐈 nanobot</h1>
  <p><strong>A simpler personal AI assistant</strong></p>
  <p>
    <img src="https://img.shields.io/badge/python->=3.11-blue">
    <img src="https://img.shields.io/badge/license-MIT-green">
  </p>
</div>

😊 **nanobot** is a **minimal, clean implementation** of [OpenClaw](https://github.com/nicepkg/openclaw) — easy to read, good to research.

🎁 The entire codebase is about **4000 lines**.

👌 Supports **Telegram**, **WhatsApp**, scheduled tasks, and tool use.


## Install

**Install from PyPi**

```bash
pip install nanobot
```

**Install from source** (recommended for development)

```bash
git clone https://github.com/user/nanobot.git
cd nanobot
pip install -e .
```

## Quick Start

> [!TIP]
> Set your API key in `~/.nanobot/config.json`. Get one at [OpenRouter](https://openrouter.ai/keys).

**1. Initialize**

```bash
nanobot onboard
```

**2. Configure** (`~/.nanobot/config.json`)

```json
{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-xxx"
    }
  }
}
```

**3. Chat**

```bash
nanobot agent -m "What is 2+2?"
```

That's it! You have a working AI assistant in 2 minutes.

## Chat Apps

Talk to your nanobot through Telegram or WhatsApp — anytime, anywhere.

| Channel | Setup |
|---------|-------|
| **Telegram** | Easy (just a token) |
| **WhatsApp** | Medium (scan QR) |

<details>
<summary><b>Telegram</b> (Recommended)</summary>

**1. Create a bot**
- Open Telegram, search `@BotFather`
- Send `/newbot`, follow prompts
- Copy the token

**2. Configure**

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["YOUR_USER_ID"]
    }
  }
}
```

> Get your user ID from `@userinfobot` on Telegram.

**3. Run**

```bash
nanobot gateway
```

</details>

<details>
<summary><b>WhatsApp</b></summary>

Requires **Node.js ≥18**.

**1. Link device**

```bash
nanobot channels login
# Scan QR with WhatsApp → Settings → Linked Devices
```

**2. Configure**

```json
{
  "channels": {
    "whatsapp": {
      "enabled": true,
      "allowFrom": ["+1234567890"]
    }
  }
}
```

**3. Run** (two terminals)

```bash
# Terminal 1
nanobot channels login

# Terminal 2
nanobot gateway
```

</details>

## Configuration

<details>
<summary><b>Full config example</b></summary>

```json
{
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5"
    }
  },
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-xxx"
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "123456:ABC...",
      "allowFrom": ["123456789"]
    },
    "whatsapp": {
      "enabled": false
    }
  },
  "tools": {
    "web": {
      "search": {
        "apiKey": "BSA..."
      }
    }
  }
}
```

</details>

**API Keys:**
- **OpenRouter**: https://openrouter.ai/keys
- **Brave Search** (optional): https://brave.com/search/api/

## CLI Reference

| Command | Description |
|---------|-------------|
| `nanobot onboard` | Initialize config & workspace |
| `nanobot agent -m "..."` | Chat with the agent |
| `nanobot agent` | Interactive chat mode |
| `nanobot gateway` | Start the gateway |
| `nanobot status` | Show status |
| `nanobot channels login` | Link WhatsApp (scan QR) |
| `nanobot channels status` | Show channel status |

<details>
<summary><b>Scheduled Tasks (Cron)</b></summary>

```bash
# Add a job
nanobot cron add --name "daily" --message "Good morning!" --cron "0 9 * * *"
nanobot cron add --name "hourly" --message "Check status" --every 3600

# List jobs
nanobot cron list

# Remove a job
nanobot cron remove <job_id>
```

</details>

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Telegram   │────▶│   Gateway   │────▶│    Agent    │
│  WhatsApp   │◀────│   (bus)     │◀────│   (LLM)     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │    Tools    │
                    │ (web, shell)│
                    └─────────────┘
```

## Contribute

PRs welcome! The codebase is intentionally small and readable.

```
nanobot/
├── agent/       # LLM agent loop & tools
├── channels/    # Telegram, WhatsApp
├── bus/         # Message routing
├── config/      # Configuration
├── cron/        # Scheduled tasks
└── cli/         # CLI commands
```
