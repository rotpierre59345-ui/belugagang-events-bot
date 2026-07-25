# BeluGANG Events Bot 🎮

Bot Discord pour le serveur **BeluGANG** — mini-jeux automatiques, belubucks, niveaux et modération.

---

## Fonctionnement des Events Automatiques

Le bot lance des mini-jeux **100% automatiquement** toutes les **3 minutes** (± 1 minute de variation aléatoire) dans n'importe quel channel dont le nom contient **`eventsBelu€(&`**.

**Aucune commande requise — aucun modo nécessaire.**

### Mini-jeux disponibles

| Event | Description | Récompense |
|---|---|---|
| ⚡ Flash Event | Premier à cliquer sur GO! gagne | 50–200 belubucks |
| 🪙 Belubuck Drop | Tout le monde peut collecter | 30–150 belubucks |
| 🔢 HighLow | Deviner si le nombre caché est plus grand/petit/égal | 100 belubucks |
| ✂️ Pierre Feuille Ciseaux | Jouer contre le bot | 75 belubucks |
| 🌍 Devinette Drapeaux | Trouver le bon drapeau parmi 4 choix | 80 belubucks |

---

## Installation

### Variables d'environnement requises

| Variable | Description |
|---|---|
| `DISCORD_TOKEN` | Token du bot Discord principal |
| `SCEMER_TOKEN` | Token de l'instance secondaire (optionnel) |
| `DB_PATH` | Chemin vers la base SQLite (défaut : `data/belugagang.db`) |

### Déploiement Railway

1. Fork ce repo ou importe-le dans Railway
2. Active les **Privileged Gateway Intents** (SERVER MEMBERS, MESSAGE CONTENT) sur le [Discord Developer Portal](https://discord.com/developers/applications)
3. Ajoute la variable `DISCORD_TOKEN` dans les variables Railway
4. Le bot démarre automatiquement via le `Procfile`

### Déploiement local

```bash
pip install -r requirements.txt
# Crée un fichier .env avec DISCORD_TOKEN=ton_token
python bot.py
```

---

## Configuration du serveur

Pour activer les events automatiques, crée simplement un channel nommé exactement :

```
eventsBelu€(&
```

Le bot détectera automatiquement ce channel et y lancera des events toutes les **3 minutes**.

---

## Commandes Admin (optionnelles)

| Commande | Description | Permission |
|---|---|---|
| `/event [type]` | Lance manuellement un event dans ce channel | Gérer le serveur |
| `/events_status` | Vérifie si le channel d'events est bien configuré | Administrateur |

---

## Économie

| Commande | Description |
|---|---|
| `/balance` | Voir son solde de belubucks |
| `/work` | Travailler pour gagner des belubucks |
| `/level` | Voir son niveau |
| `/leaderboard` | Classement des niveaux |

---

*Créé pour BeluGANG.*
