"""
Petit client pour interroger l'API interne (non officielle) de Vinted.
Vinted ne fournit pas d'API publique documentée : ce module reproduit les
requêtes que le site web effectue lui-même. Le format des réponses peut
changer sans préavis, et une utilisation trop agressive (fréquence trop
élevée) peut se faire bloquer temporairement par leur protection anti-bot —
d'où l'intervalle raisonnable (1-2 min) côté serveur.
"""

import requests

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9",
}


def get_session(domain="vinted.fr"):
    """Crée une session et récupère les cookies nécessaires (anti-bot, CSRF...)."""
    session = requests.Session()
    session.headers.update(BASE_HEADERS)
    session.get(f"https://www.{domain}/", timeout=15)
    return session


def search_items(session, mots_cles, prix_min=None, prix_max=None, domain="vinted.fr", per_page=20):
    """Recherche des articles et renvoie une liste de dicts normalisés."""
    url = f"https://www.{domain}/api/v2/catalog/items"
    params = {
        "search_text": mots_cles,
        "order": "newest_first",
        "per_page": per_page,
        "page": 1,
    }
    if prix_min:
        params["price_from"] = prix_min
    if prix_max:
        params["price_to"] = prix_max

    resp = session.get(url, params=params, timeout=15)

    if resp.status_code in (401, 403):
        # cookies expirés ou blocage temporaire : on ouvre une nouvelle session
        session = get_session(domain)
        resp = session.get(url, params=params, timeout=15)

    resp.raise_for_status()
    data = resp.json()

    items = []
    for it in data.get("items", []):
        prix = it.get("price")
        if isinstance(prix, dict):
            montant, devise = prix.get("amount"), prix.get("currency_code")
        else:
            montant, devise = prix, it.get("currency")

        items.append({
            "id": it.get("id"),
            "titre": it.get("title"),
            "prix": montant,
            "devise": devise,
            "marque": it.get("brand_title"),
            "taille": it.get("size_title"),
            "url": it.get("url"),
            "photo": (it.get("photo") or {}).get("url"),
        })

    return items, session


def filtre_marque_taille(items, marque=None, taille=None):
    """Filtre côté client sur la marque / taille (recherche partielle, insensible à la casse)."""
    res = []
    for it in items:
        if marque and (not it["marque"] or marque.lower() not in it["marque"].lower()):
            continue
        if taille and (not it["taille"] or taille.lower() not in it["taille"].lower()):
            continue
        res.append(it)
    return res
