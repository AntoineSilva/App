"""
Serveur backend de l'app "Alertes Vinted".

- Expose une API REST utilisée par l'app mobile (créer/lister/supprimer des
  recherches, chacune rattachée au push_token de l'appareil).
- Fait tourner en arrière-plan une boucle qui vérifie toutes les recherches
  actives toutes les INTERVALLE_SECONDES et envoie une notification push
  dès qu'un nouvel article correspond.

⚠️ Ce serveur doit rester en cours d'exécution en permanence (pas un
hébergement qui "s'endort" après inactivité) pour que la surveillance soit
vraiment continue. Voir le README pour les options d'hébergement.
"""

import logging
import threading
import time

from flask import Flask, jsonify, request

import database as db
import push
import vinted_client as vc

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

INTERVALLE_SECONDES = 90  # vérification toutes les 1-2 minutes
SESSIONS = {}  # cache de sessions Vinted par domaine


def get_cached_session(domain="vinted.fr"):
    if domain not in SESSIONS:
        SESSIONS[domain] = vc.get_session(domain)
    return SESSIONS[domain]


@app.route("/api/searches", methods=["POST"])
def creer_recherche():
    data = request.get_json(force=True) or {}
    push_token = data.get("push_token")
    mots_cles = data.get("mots_cles")

    if not push_token or not mots_cles:
        return jsonify({"erreur": "push_token et mots_cles sont requis"}), 400

    search_id = db.add_search(
        push_token=push_token,
        nom=data.get("nom") or mots_cles,
        mots_cles=mots_cles,
        prix_min=data.get("prix_min"),
        prix_max=data.get("prix_max"),
        marque=data.get("marque"),
        taille=data.get("taille"),
    )
    return jsonify({"id": search_id}), 201


@app.route("/api/searches", methods=["GET"])
def lister_recherches():
    push_token = request.args.get("push_token")
    if not push_token:
        return jsonify({"erreur": "push_token requis"}), 400
    return jsonify(db.list_searches(push_token))


@app.route("/api/searches/<int:search_id>", methods=["DELETE"])
def supprimer_recherche(search_id):
    push_token = request.args.get("push_token")
    if not push_token:
        return jsonify({"erreur": "push_token requis"}), 400
    ok = db.remove_search(push_token, search_id)
    return jsonify({"supprime": ok})


@app.route("/api/health", methods=["GET"])
def sante():
    return jsonify({"statut": "ok"})


def verifier_toutes_les_recherches():
    recherches = db.get_all_active_searches()
    for r in recherches:
        try:
            session = get_cached_session()
            items, session = vc.search_items(
                session, r["mots_cles"], prix_min=r["prix_min"], prix_max=r["prix_max"]
            )
            SESSIONS["vinted.fr"] = session
            items = vc.filtre_marque_taille(items, marque=r["marque"], taille=r["taille"])

            deja_vus = set(r["derniers_ids"].split(",")) if r["derniers_ids"] else set()
            nouveaux = [it for it in items if str(it["id"]) not in deja_vus]

            # On n'alerte pas au tout premier passage (sinon spam de tout
            # l'historique existant) : on enregistre juste une référence.
            if nouveaux and deja_vus:
                for it in nouveaux[:5]:
                    push.envoyer_notification(
                        r["push_token"],
                        titre=r["nom"],
                        corps=f"{it['titre']} — {it['prix']} {it['devise'] or ''}",
                        data={"url": it["url"]},
                    )

            tous_ids = ",".join(str(it["id"]) for it in items)[:2000]
            db.update_seen_ids(r["id"], tous_ids)

        except Exception as e:
            logger.error("Erreur pendant la vérification de la recherche %s : %s", r["id"], e)


def boucle_surveillance():
    while True:
        try:
            verifier_toutes_les_recherches()
        except Exception as e:
            logger.error("Erreur dans la boucle de surveillance : %s", e)
        time.sleep(INTERVALLE_SECONDES)


if __name__ == "__main__":
    db.init_db()
    threading.Thread(target=boucle_surveillance, daemon=True).start()
    logger.info("Serveur démarré, vérification toutes les %s secondes.", INTERVALLE_SECONDES)
    app.run(host="0.0.0.0", port=5000)
