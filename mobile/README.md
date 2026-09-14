# App mobile — Alertes Vinted

## 1. Créer le projet Expo

```bash
npx create-expo-app@latest alertes-vinted
cd alertes-vinted
npx expo install expo-notifications expo-device expo-constants
```

Remplace ensuite le `App.js` et le `app.json` générés par ceux de ce dossier (`mobile/App.js` et `mobile/app.json`), et copie `mobile/eas.json` à la racine du projet.

Dans `App.js`, mets à jour `API_URL` avec l'adresse de ton backend (voir `backend/README.md`).

**Note HTTP vs HTTPS** : si ton backend tourne sur un VPS en simple HTTP (ex: `http://51.255.46.216:5000`), le `usesCleartextTraffic: true` déjà ajouté dans `app.json` permet à Android d'accepter cette connexion non chiffrée. C'est suffisant pour un usage entre amis, mais si tu veux une vraie URL HTTPS plus tard sans toucher aux ports 80/443 déjà pris par Docker, regarde du côté d'un **tunnel Cloudflare** (`cloudflared`) : il expose ton service en HTTPS via un nom de domaine, sans ouvrir aucun port supplémentaire sur le VPS.

## 2. Tester rapidement avec Expo Go

```bash
npx expo start
```

Scanne le QR code avec l'app **Expo Go** (iOS ou Android). Ça te permet de tester vite l'interface et l'ajout de recherches.

⚠️ **Limite importante** : depuis Expo SDK 53, **les notifications push à distance ne fonctionnent pas dans Expo Go sur Android** (seules les notifications locales, app ouverte, fonctionnent). Sur iOS via Expo Go, ça peut fonctionner mais reste moins fiable qu'une vraie app installée. Pour que tes amis reçoivent vraiment les alertes même téléphone verrouillé, il faut distribuer une vraie app installable — étape suivante.

## 3. Générer une app installable (APK) à envoyer à tes amis

C'est l'équivalent gratuit d'un lien "type Play Store", sans publier sur le Play Store.

```bash
npm install -g eas-cli
eas login          # crée un compte Expo gratuit si tu n'en as pas
eas init            # relie le projet à ton compte, remplit "projectId" dans app.json
eas build --platform android --profile preview
```

La commande `eas build` tourne dans le cloud d'Expo (gratuit, avec une limite mensuelle de builds sur le plan gratuit) et prend 10-15 minutes. À la fin, tu obtiens un **lien de téléchargement direct de l'APK** (et un QR code). Il te suffit d'envoyer ce lien à tes amis.

Sur leur téléphone Android, ils devront autoriser "l'installation d'apps depuis une source inconnue" la première fois (normal pour tout ce qui n'est pas sur le Play Store), puis installer l'APK. Une fois installée, l'app fonctionne comme une vraie app : elle reçoit les notifications même fermée ou téléphone verrouillé.

Pour iOS, la distribution hors App Store est plus contraignante (Apple impose des limitations techniques et de durée) — si tes amis sont sur iPhone, le plus simple reste Expo Go pour eux, avec la limite de fiabilité mentionnée plus haut.

## Comment ça marche

1. À l'ouverture, l'app demande la permission de notifications et récupère un `push_token` unique pour l'appareil.
2. Chaque recherche ajoutée dans l'app est envoyée au backend avec ce `push_token`.
3. Le backend vérifie Vinted toutes les 90 secondes pour chaque recherche active.
4. Dès qu'un nouvel article correspond, le backend envoie une notification push (via le service gratuit d'Expo) directement au téléphone concerné, avec un lien vers l'annonce.
5. Toucher la notification ouvre directement l'annonce dans le navigateur.
