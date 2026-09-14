# Backend — Alertes Vinted

Ce serveur fait deux choses :
1. Expose une API REST que l'app mobile utilise pour créer/lister/supprimer des recherches.
2. Vérifie en continu (toutes les 90 secondes) les recherches actives et envoie une notification push dès qu'un nouvel article correspond.

## 1. Installer

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # sous Windows : venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Lancer en local (pour tester)

```bash
python app.py
```

Le serveur écoute sur `http://0.0.0.0:5000`. Pour que ton téléphone (en dev, via Expo Go) puisse l'atteindre pendant que tu codes, utilise l'IP locale de ton PC (ex: `http://192.168.1.20:5000`) comme `API_URL` dans `mobile/App.js` — ton téléphone et ton PC doivent être sur le même réseau Wi-Fi.

## 3. Héberger pour de vrai (obligatoire pour que tes amis reçoivent des alertes)

⚠️ **Important** : le serveur doit tourner **en permanence**, pas seulement quand ton PC est allumé, sinon la surveillance s'arrête. Tu as plusieurs options, du plus simple au plus robuste :

- **Un petit VPS** (quelques euros/mois — OVH, Hetzner, DigitalOcean...) : tu y déploies le dossier `backend/` et tu le lances avec `python app.py` derrière un `systemd`/`screen`/`tmux` pour qu'il survive à la déconnexion SSH.
- **Une plateforme d'hébergement d'apps** (Render, Railway, Fly.io...) : vérifie bien de prendre une offre "always-on" — les offres gratuites qui "s'endorment" après inactivité casseraient la surveillance continue.
- **Ton propre PC/Raspberry Pi à la maison**, allumé en permanence, avec le port 5000 ouvert sur ta box (redirection de port) ou via un tunnel (ex: ngrok, Cloudflare Tunnel) pour avoir une URL publique stable.

Une fois hébergé, récupère l'URL publique (ex: `https://ton-app.exemple.com`) et mets-la dans `API_URL` en haut de `mobile/App.js`.

## 4. Déployer sur un VPS avec Docker (recommandé si tu en as un)

Sur ton VPS (SSH, puis dans le dossier du projet cloné depuis GitHub) :

```bash
cd vinted-alertes/backend
docker build -t vinted-backend .
docker run -d --name vinted-backend --restart unless-stopped -p 5000:5000 vinted-backend
```

- `--restart unless-stopped` : le conteneur redémarre tout seul après un crash ou un reboot du serveur → surveillance vraiment continue.
- Vérifie que ça tourne : `curl http://localhost:5000/api/health` doit répondre `{"statut":"ok"}`.
- Si `ufw` est actif sur le VPS : `sudo ufw allow 5000/tcp`.
- Pour mettre à jour après un `git pull` : `docker build -t vinted-backend . && docker stop vinted-backend && docker rm vinted-backend` puis relance la commande `docker run` ci-dessus.

⚠️ Ce backend répond en HTTP simple, pas HTTPS. Android bloque par défaut le trafic HTTP non chiffré depuis une app — voir la note dans `mobile/README.md` pour l'activer en test, ou passer par un tunnel Cloudflare pour avoir une vraie URL HTTPS sans toucher aux ports 80/443 déjà utilisés.

## API

- `POST /api/searches` — body JSON : `{push_token, nom, mots_cles, prix_min, prix_max, marque, taille}`
- `GET /api/searches?push_token=...` — liste les recherches actives de cet appareil
- `DELETE /api/searches/<id>?push_token=...` — supprime une recherche
- `GET /api/health` — vérifie que le serveur répond

## Notes

- Les recherches sont stockées dans `vinted_app.db` (SQLite), créée automatiquement au premier lancement.
- Ce backend s'appuie sur l'API interne, non officielle, de Vinted : son format peut changer sans préavis.
- L'intervalle de vérification (`INTERVALLE_SECONDES` dans `app.py`) est fixé à 90 secondes, un compromis entre réactivité et respect du service.
