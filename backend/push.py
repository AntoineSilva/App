"""
Envoi de notifications push via le service gratuit d'Expo (aucune clé API
requise pour un usage basique : il suffit du push_token de l'appareil,
généré côté app mobile).
"""

import logging
import requests

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def envoyer_notification(push_token, titre, corps, data=None):
    payload = {
        "to": push_token,
        "title": titre,
        "body": corps,
        "sound": "default",
        "priority": "high",
    }
    if data:
        payload["data"] = data

    try:
        resp = requests.post(
            EXPO_PUSH_URL,
            json=payload,
            timeout=10,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("Échec de l'envoi de la notification : %s", e)
