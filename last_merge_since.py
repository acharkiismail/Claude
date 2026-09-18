import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

# ============================================================
# Calcule depuis quand interroger la file pour le prochain cycle.
#
# Lit last_merge_utc dans le fichier maître écrit par realtime_report.py et
# renvoie la borne inférieure à utiliser dans le filtre "Get Data from Queue".
# En marche normale la fenêtre vaut un cycle; après une panne de 3 h elle vaut
# 3 h, sans intervention. La fusion côté realtime_report.py étant un upsert sur
# key_col, redemander une fenêtre trop large ne duplique rien.
# ============================================================

STAMP_FMT = "%Y-%m-%dT%H:%M:%SZ"


def read_last_merge(master_path: str):
    """Horodatage de la dernière fusion réussie, ou None s'il est introuvable.
    Un maître absent, verrouillé ou corrompu n'est pas une erreur : on retombe
    simplement sur la fenêtre maximale."""
    for path in (master_path, master_path + ".bak"):
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                data = json.loads(f.read())
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        raw = data.get("last_merge_utc")
        if not raw:
            continue
        try:
            return datetime.strptime(str(raw).strip(), STAMP_FMT).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


def compute_since(master_path: str, overlap_minutes: int, max_minutes: int):
    """Retourne (borne_inferieure, origine)."""
    now = datetime.now(timezone.utc)
    floor = now - timedelta(minutes=max_minutes)

    last_merge = read_last_merge(master_path)
    if last_merge is None:
        return floor, "max_window"

    # Un horodatage dans le futur signale une horloge décalée : on ne lui fait pas
    # confiance, la fenêtre maximale est le choix prudent.
    if last_merge > now:
        return floor, "max_window"

    since = last_merge - timedelta(minutes=overlap_minutes)
    if since < floor:
        return floor, "capped"
    return since, "last_merge"


def main():
    ap = argparse.ArgumentParser(
        description="Calcule la borne inférieure à utiliser pour interroger la file.")
    ap.add_argument("--master_json", required=True,
                    help="Fichier maître écrit par realtime_report.py")
    ap.add_argument("--overlap_minutes", type=int, default=5,
                    help="Marge retranchée à la dernière fusion, contre les décalages d'horloge (défaut 5)")
    ap.add_argument("--max_minutes", type=int, default=1440,
                    help="Fenêtre maximale, aussi utilisée quand le maître est absent (défaut 1440)")
    args = ap.parse_args()

    if args.overlap_minutes < 0:
        sys.stdout.write(f"ERROR|message=invalid_overlap_minutes|value={args.overlap_minutes}\n")
        sys.exit(1)
    if args.max_minutes <= 0:
        sys.stdout.write(f"ERROR|message=invalid_max_minutes|value={args.max_minutes}\n")
        sys.exit(1)

    try:
        since, source = compute_since(args.master_json, args.overlap_minutes, args.max_minutes)
        minutes_back = int((datetime.now(timezone.utc) - since).total_seconds() // 60)
        sys.stdout.write(
            f"ok|since_utc={since.strftime(STAMP_FMT)}"
            f"|minutes_back={minutes_back}"
            f"|source={source}\n")
        sys.exit(0)
    except Exception as e:
        sys.stdout.write(f"ERROR|message={type(e).__name__}|detail={e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
