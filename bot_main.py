"""
Entrypoint de production — BeluGANG Events Bot.
Utilisé par le Procfile (Railway/Heroku) : web: python bot_main.py
"""

import asyncio
from bot import main

if __name__ == "__main__":
    asyncio.run(main())
