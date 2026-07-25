# BeluGANG Events Bot 🐾

Un bot Discord complet inspiré du serveur **BeluGANG**, conçu pour gérer les événements, l'économie des "belubucks", les niveaux et la modération.

## 🚀 Fonctionnalités

- **Économie (BeluBucks) :**
  - `/balance` : Voir son solde.
  - `/work` : Travailler pour gagner des belubucks.
  - `/shop` & `/buy` : Acheter des rôles exclusifs.
  - `/leaderboard` : Classement des plus riches.
- **Système de Niveaux :**
  - Gain d'XP par message.
  - `/level` & `/rank` : Voir sa progression.
  - Notifications de montée de niveau.
- **Événements Mini-jeux :**
  - **Flash Event** : Premier à cliquer sur "GO!".
  - **HighLow** : Deviner le nombre caché.
  - **Rock Paper Scissors** : Jouer contre le bot.
  - **Flag Guessing** : Trouver le bon drapeau.
  - **Belubuck Drop** : Collecter des pièces avant qu'elles ne disparaissent.
  - Événements automatiques toutes les 15 minutes.
- **Modération & RGPD :**
  - Anti-liens et anti-spam automatique.
  - `/data request` & `/data delete` : Gestion des données personnelles.

## 🛠️ Installation sur Railway

1. Crée un bot sur le [Discord Developer Portal](https://discord.com/developers/applications).
2. Active les **Privileged Gateway Intents** (SERVER MEMBERS, MESSAGE CONTENT).
3. Fork ce dépôt sur GitHub.
4. Crée un nouveau projet sur **Railway** et connecte ton dépôt.
5. Ajoute la variable d'environnement suivante :
   - `DISCORD_TOKEN` : Le jeton de ton bot.
6. Railway déploiera automatiquement le bot.

## ⚙️ Configuration Admin

- `/seteventchannel <#salon>` : Définit le salon où les événements automatiques auront lieu.
- `/addshop <role> <prix>` : Ajoute un rôle à la boutique.
- `/give <membre> <montant>` : (Admin) Donner des belubucks.

---
*Créé avec ❤️ pour la BeluGANG.*
