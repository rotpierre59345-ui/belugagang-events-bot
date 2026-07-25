# BeluGANG Events Bot 🐾

A complete Discord bot inspired by the **BeluGANG** server, designed to manage events, "belubucks" economy, levels, and moderation.

## 🚀 Features

- **Economy (BeluBucks):** `/balance`, `/work`, `/shop`, `/buy`, `/richlist`.
- **Levels:** XP gain per message, `/level`, `/rank`, `/leaderboard`.
- **Mini-games:** Flash Event, HighLow, RPS, Flag Guessing, Belubuck Drop.
- **Moderation:** Auto anti-link/spam, GDPR data management (`/data`).

## 🛠️ Installation (Railway)

1. Create a bot on the [Discord Developer Portal](https://discord.com/developers/applications).
2. Enable **Privileged Gateway Intents** (SERVER MEMBERS, MESSAGE CONTENT).
3. Fork this repo.
4. Create a new **Railway** project and connect your repo.
5. Add the following environment variables:
   - `DISCORD_TOKEN`: Your main bot token.
   - `SCEMER_TOKEN`: The token for the webhook/verification system (non-verified bots).
6. Railway will deploy automatically.

---
*Created for BeluGANG.*
