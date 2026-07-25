"""
SCEMER — Instance secondaire du BeluGANG Events Bot.
Ce fichier est conservé pour compatibilité Railway (Procfile).
Il démarre la même instance principale avec le token SCEMER_TOKEN si disponible,
sinon il ne fait rien.
"""

import os
import asyncio
import logging
from bot import bot, load_cogs

logger = logging.getLogger("BeluGANG.Scemer")


async def main():
    token = os.getenv("SCEMER_TOKEN")
    if not token:
        logger.warning("SCEMER_TOKEN non défini — instance SCEMER non démarrée.")
        return
    logger.info("Démarrage de l'instance SCEMER...")
    async with bot:
        await load_cogs()
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
