# BeluGANG Events Bot

A Discord bot for BeluGANG Events — economy system, levelling, and automatic interactive events.

## Features

### Slash Commands

| Command | Description |
|---|---|
| `/balance [user]` | View your balance or another user's balance |
| `/work` | Work to earn belubucks (1-hour cooldown) |
| `/leaderboard` | See the top 10 richest members |
| `/level [user]` | View your level and XP progress |
| `/rank [user]` | Same as `/level` |
| `/shop` | Browse rewards available for belubucks |
| `/info` | Get help and information about the bot |
| `/data request` | Request a copy of your stored personal data |
| `/data delete` | Permanently delete all your personal data |

### Auto Events

Events are triggered by **mentioning the bot** with a channel:

```
@BeluGANG Events #your-channel
```

Once configured, events fire automatically every **1–3 minutes** in that channel (as seen in the video).

To stop events:
```
@BeluGANG Events stop
```

| Event | Description |
|---|---|
| ⚡ **Flash Event** | First to click GO! wins belubucks |
| 🚩 **Flag Event** | Guess the correct country flag from 3 choices |
| 💰 **Collect Event** | Everyone who clicks in time earns belubucks |
| 🎮 **Rock Paper Scissors** | Beat the bot's choice to win belubucks |

### Economy

- Currency: **belubucks**
- Earn by: working (`/work`), winning events
- Spend at: `/shop`

### Levelling

- Earn XP by winning events
- Level up announcements in channel
- View progress with `/level` or `/rank`

## Deployment on Railway

### Required Environment Variable

| Variable | Description |
|---|---|
| `DISCORD_TOKEN` | Your Discord bot token |

### Optional Environment Variables

| Variable | Default | Description |
|---|---|---|
| `EVENT_CHANNEL_NAME` | `general` | Name of the channel where events fire |
| `EVENT_INTERVAL_MIN` | `15` | Minimum minutes between events |
| `EVENT_INTERVAL_MAX` | `30` | Maximum minutes between events |

### Steps

1. Fork or push this repo to GitHub
2. Create a new Railway project from the repo
3. Set `DISCORD_TOKEN` in Railway's environment variables
4. Deploy — Railway will use the `Procfile` (`worker: python main.py`)

## Bot Permissions Required

- Send Messages
- Send Messages in Threads
- Embed Links
- Read Message History
- Use Application Commands
- View Channels

## Invite URL Scopes

- `bot`
- `applications.commands`

## Local Development

```bash
pip install -r requirements.txt
DISCORD_TOKEN=your_token_here python main.py
```

---

*BeluGANG Events — As a thank you for supporting BeluGANG! 💖*
