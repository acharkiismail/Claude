"""Extrait le tableau de l'avis public "Vente pour defaut de paiement de
taxes foncieres" (Ville de Montreal) vers un fichier Excel structure.

Le corps du tableau (comptes, adresses, lots, proprietaires, montants) est
dessine en vectoriel dans ce PDF (aucun texte reel, non selectionnable) --
il est decode via un regroupement de formes par similarite visuelle (voir
pdf_vector_glyph_clusters.py). Les titres de section "ARRONDISSEMENT DE
X (nn)" sont du vrai texte (juste l'apostrophe typographique mal decodee)
et sont lus normalement via get_text().

Usage:
  python pdf_montreal_table_to_excel.py --input-file "chemin.pdf" --output-file tableau.xlsx --first-page 1 --last-page 5
"""
import argparse
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF
import pandas as pd

ZOOM = 10
NORM = 18
THRESH = 18.0
MAX_SIZE = 20.0

# Table de correspondance forme -> vrai caractere, construite en lisant une
# planche-contact des formes uniques (voir pdf_vector_glyph_clusters.py).
# Valide contre une extraction OCR de reference sur ce document.
CLUSTER_TO_CHAR = {
    26: '0', 34: '1', 27: '2', 3: 'E', 35: '5', 42: '4', 12: 'A', 33: '3', 32: '6', 28: '7', 29: '9', 15: 'L',
    1: 'O', 0: 'N', 30: '8', 9: 'S', 7: 'T', 4: 'C', 17: 'U', 23: 'R', 40: ',', 10: 'I', 2: 'D', 44: '-',
    50: 'E', 14: 'I', 41: '8', 18: 'B', 47: 'A', 5: 'M', 31: '-', 52: 'N', 59: 'I', 36: 'V', 37: 'H', 6: 'P',
    11: 'G', 90: '-', 61: '3', 43: '1', 91: '#', 56: 'Y', 74: 'Q', 38: 'R', 76: 'K', 65: 'N', 53: '6', 58: 'F',
    19: '.', 70: 'B', 57: '.', 55: 'D', 87: '#', 13: 'T', 62: '8', 48: 'X', 45: 'U', 93: '.', 105: 'O', 72: '0',
    83: 'J', 66: 'H', 49: '2', 54: 'R', 92: '-', 77: 'Z', 84: 'W', 51: 'M', 69: ',', 21: 'S', 46: 'V', 78: 'O',
    86: '9', 68: '6', 39: 'M', 81: '4', 60: 'M', 75: '.', 67: '.', 8: 'E', 106: '.', 79: 'A', 122: '.', 71: '4',
    96: 'Y', 94: 'J', 121: 'B', 16: ',', 24: 'T', 89: 'E', 82: 'H', 88: 'A', 98: '#', 22: ')', 20: '(', 97: 'Y',
    63: 'A', 25: 'E', 85: ',', 108: 'Q', 64: 'A', 116: '.', 73: '0', 80: ',', 99: '7', 114: '#', 109: 'O', 110: 'N',
    111: 't', 112: 'r', 113: 'a', 123: 'T', 127: ',', 128: 'U', 139: 'P', 100: '5', 103: 'Y', 115: '#', 124: '9', 126: ',',
    95: '&', 107: 'D', 117: '1', 118: '3', 101: 'A', 104: 'F', 119: 'W', 120: 'L', 131: 'B', 137: '.', 141: 'P', 143: 'T',
    102: 'V', 125: 'W', 129: 'A', 130: 'K', 132: '/', 133: 'X', 134: 'A', 135: 'A', 136: ',', 138: ',', 140: ',', 142: 'Q',
    144: ',', 145: '(',
}

# Bornes de colonnes (en points PDF) calibrees sur les positions des en-tetes
# NO DE COMPTE / DESIGNATION DE L'IMMEUBLE / CAD. LOT(S) / NOM DU PROPRIETAIRE / MONTANT
LEFT_COLUMNS = [
    ("NO_COMPTE", 150, 232),
    ("DESIGNATION", 232, 335),
    ("CAD_LOT", 335, 420),
]
RIGHT_COLUMNS = [
    ("NO_COMPTE", 600, 646),
    ("DESIGNATION", 646, 750),
    ("CAD_LOT", 750, 835),
]
# PROPRIETAIRE et MONTANT n'ont pas de largeur fixe fiable : un nom long ("... ET AL",
# "... INC.") deborde d'une frontiere fixe selon sa longueur. On prend plutot toute la
# plage combinee et on coupe au plus grand espace trouve (le vrai espace entre le nom et
# le montant est toujours nettement plus large que les espaces entre mots du nom).
LEFT_PROP_MONTANT_RANGE = (420, 600)
RIGHT_PROP_MONTANT_RANGE = (835, 1190)

# Champs qui doivent etre purement numeriques (+tiret) : O/0 sont visuellement
# impossibles a distinguer par la forme dans cette police, donc un O ici est presque
# certainement un 0 mal identifie
NUMERIC_FIELDS = {"NO_COMPTE", "CAD_LOT", "MONTANT"}
LOOKALIKE_FIX = {"O": "0"}

# PROPRIETAIRE est presque toujours un nom (rarement de vrais chiffres) : l'ambiguite
# 0/O joue dans l'autre sens ici (ex: "HABITATI0NS" doit redevenir "HABITATIONS"). On
# corrige un 0 en O seulement quand il touche une lettre (jamais en plein milieu d'un
# nombre), pour ne pas casser un vrai chiffre isole dans un nom.
ZERO_NEAR_LETTER_RE = re.compile(r"(?<=[A-ZÀ-Ÿ])0|0(?=[A-ZÀ-Ÿ])")

# Lignes fantomes issues de rares glyphes vectoriels mal isoles (artefact de rendu,
# pas une vraie donnee) : leur DESIGNATION decode systematiquement en "N t r a"
NOISE_DESIGNATIONS = {"N T R A"}

NO_COMPTE_RE = re.compile(r"^\d{6}-\d{2}$")
MONTANT_RE = re.compile(r"^\d{1,3}(?: \d{3})* ?[.,]\d{2}$")

# Mots d'en-tete de colonne : si NO_COMPTE contient un de ces mots, la "ligne"
# est en fait l'en-tete du tableau (parfois lui-meme dessine en vectoriel),
# pas une vraie ligne de donnees -> a exclure
HEADER_WORDS = {"COMPTE", "NO DE", "NODE", "N T R A"}


def cluster_shapes_for_pages(doc, first_page, last_page):
    """Extrait et regroupe par similarite toutes les formes vectorielles de
    taille caractere sur les pages donnees. Retourne items (avec cluster_id
    assigne) et la liste des clusters (utile pour diagnostic seulement)."""
    items = []
    for page_num in range(first_page, last_page + 1):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), colorspace=fitz.csGRAY)
        full_img_samples = pix.samples
        stride = pix.stride
        from PIL import Image
        full_img = Image.frombytes("L", (pix.width, pix.height), full_img_samples)

        for d in page.get_drawings():
            r = d["rect"]
            if r.width <= 0 or r.height <= 0 or r.width > MAX_SIZE or r.height > MAX_SIZE:
                continue
            pad = 0.15
            x0, y0 = (r.x0 - pad) * ZOOM, (r.y0 - pad) * ZOOM
            x1, y1 = (r.x1 + pad) * ZOOM, (r.y1 + pad) * ZOOM
            crop = full_img.crop((x0, y0, x1, y1)).resize((NORM, NORM), Image.LANCZOS)
            vec = list(crop.tobytes())
            items.append({"page": page_num, "bbox": (r.x0, r.y0, r.x1, r.y1), "vec": vec})

    def dist(a, b):
        return sum(abs(x - y) for x, y in zip(a, b)) / len(a)

    clusters = []
    for it in items:
        v = it["vec"]
        found = None
        for ci, c in enumerate(clusters):
            if dist(v, c["rep_vec"]) < THRESH:
                found = ci
                break
        if found is None:
            clusters.append({"rep_vec": v, "count": 1})
            it["cluster_id"] = len(clusters) - 1
        else:
            clusters[found]["count"] += 1
            it["cluster_id"] = found

    return items, clusters


def get_section_headers(doc, first_page, last_page):
    """Retourne une liste de (page, y0, x0, texte_arrondissement) pour
    chaque en-tete de section trouve, un vrai texte (mal decode seulement au
    niveau de l'apostrophe typographique)."""
    headers = []
    pattern = re.compile(r"ARRONDISSEMENT[^\n]*\(\d+\)")
    for page_num in range(first_page, last_page + 1):
        page = doc[page_num]
        text = page.get_text().replace("¶", "'")
        for m in pattern.finditer(text):
            # retrouver la position: cherche le premier mot du match
            words = page.get_text("words")
            first_word = m.group().split()[0]
            for w in words:
                if w[4] == "ARRONDISSEMENT":
                    # verifie grossierement que ce mot appartient a ce match (approche simple: on
                    # associe par ordre d'apparition plus bas)
                    pass
            headers.append(m.group())
    return headers


def build_table(input_file: str, first_page: int, last_page: int):
    doc = fitz.open(input_file)

    items, clusters = cluster_shapes_for_pages(doc, first_page, last_page)

    decoded = []
    for it in items:
        ch = CLUSTER_TO_CHAR.get(it["cluster_id"], "?")
        x0, y0, x1, y1 = it["bbox"]
        decoded.append({"page": it["page"], "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                         "ycenter": (y0 + y1) / 2, "ch": ch})

    # en-tetes de section (arrondissement), avec position, pour associer chaque ligne
    section_headers = []  # (page, y0, x0, "ARRONDISSEMENT DE X (nn)")
    pattern = re.compile(r"ARRONDISSEMENT\s+D[E’']?\s*.*?\(\d+\)")
    for page_num in range(first_page, last_page + 1):
        page = doc[page_num]
        blocks = page.get_text("blocks")
        for b in blocks:
            btext = b[4].replace("¶", "'").strip()
            m = pattern.search(btext.replace("\n", " "))
            if m:
                section_headers.append({"page": page_num, "y0": b[1], "x0": b[0], "text": m.group()})

    def section_for(page_num, x0, y0):
        candidates = [h for h in section_headers if h["page"] == page_num
                      and h["y0"] <= y0 + 2
                      and (h["x0"] < 500) == (x0 < 600)]
        if not candidates:
            return ""
        return max(candidates, key=lambda h: h["y0"])["text"]

    # regroupe par page, PUIS par bloc gauche/droit, PUIS par ligne visuelle (centre Y).
    # Regrouper les lignes avant de separer gauche/droite ferait courir le risque qu'un
    # caractere du bloc gauche (ex: la virgule decimale, legerement decalee en Y) rejoigne
    # par erreur une ligne du bloc droit si son decalage se trouve etre plus proche.
    rows_by_page = {}
    for d in decoded:
        rows_by_page.setdefault(d["page"], []).append(d)

    row_tol = 3.0

    def group_into_rows(chars):
        rows = []  # chaque row: liste de caracteres + 'yavg' (moyenne courante)
        for c in sorted(chars, key=lambda w: w["ycenter"]):
            best_row, best_dist = None, None
            for row in rows:
                d = abs(row["yavg"] - c["ycenter"])
                if d <= row_tol and (best_dist is None or d < best_dist):
                    best_row, best_dist = row, d
            if best_row is not None:
                best_row["chars"].append(c)
                n = len(best_row["chars"])
                best_row["yavg"] += (c["ycenter"] - best_row["yavg"]) / n
            else:
                rows.append({"chars": [c], "yavg": c["ycenter"]})
        return [r["chars"] for r in rows]

    records = []
    for page_num, chars in rows_by_page.items():
        left_chars = [c for c in chars if c["x0"] < 600]
        right_chars = [c for c in chars if c["x0"] >= 600]
        left_rows = group_into_rows(left_chars)
        right_rows = group_into_rows(right_chars)

        def chars_to_text(chars_sorted):
            out = []
            prev_x1 = None
            for c in chars_sorted:
                if prev_x1 is not None and c["x0"] - prev_x1 > 1.8:
                    out.append(" ")
                out.append(c["ch"])
                prev_x1 = c["x1"]
            return "".join(out).strip()

        def split_prop_montant(chars_in_range):
            """Coupe au plus grand espace entre deux caracteres consecutifs :
            c'est toujours la frontiere nom/montant, plus large que les espaces
            internes du nom (ET AL, INC., etc). Mais si le nom deborde sur la ligne
            physique suivante, cette ligne-ci n'a PAS de montant du tout -- dans ce cas
            le plus grand espace tombe entre deux mots du nom (ex: 'LES' / 'HABITATIONS
            SOLIDAIRES'), pas avant un montant. On verifie donc que la partie "montant"
            contient au moins un chiffre ; sinon tout appartient au nom."""
            chars_sorted = sorted(chars_in_range, key=lambda w: w["x0"])
            if not chars_sorted:
                return [], []
            best_gap, best_i = -1, len(chars_sorted)
            for i in range(1, len(chars_sorted)):
                gap = chars_sorted[i]["x0"] - chars_sorted[i - 1]["x1"]
                if gap > best_gap:
                    best_gap, best_i = gap, i
            prop_chars, montant_chars = chars_sorted[:best_i], chars_sorted[best_i:]
            # Un vrai montant n'a jamais de lettre autre que O (confondu avec 0 dans
            # ce meme glyphe ambigu -- corrige plus tard via LOOKALIKE_FIX). Toute
            # AUTRE lettre trahit un nom, pas un montant : sans ce garde-fou, un 0
            # confondu avec O au milieu d'un nom (ex: "HABITATI0NS") suffit a faire
            # croire qu'il y a un montant ici.
            has_other_letter = any(c["ch"].isalpha() and c["ch"] != "O" for c in montant_chars)
            has_digit = any(c["ch"].isdigit() for c in montant_chars)
            if has_other_letter or not has_digit:
                return chars_sorted, []
            return prop_chars, montant_chars

        def build_prelim_records(rows, columns, prop_montant_range):
            prelim = []
            for row in rows:
                block = sorted(row, key=lambda w: w["x0"])
                if not block:
                    continue
                fields = {name: [] for name, _, _ in columns}
                for c in block:
                    for name, xmin, xmax in columns:
                        if xmin <= c["x0"] < xmax:
                            fields[name].append(c)
                            break

                record = {}
                for name, _, _ in columns:
                    record[name] = chars_to_text(sorted(fields[name], key=lambda w: w["x0"]))

                pm_min, pm_max = prop_montant_range
                pm_chars = [c for c in block if pm_min <= c["x0"] < pm_max]
                prop_chars, montant_chars = split_prop_montant(pm_chars)
                record["PROPRIETAIRE"] = chars_to_text(prop_chars)
                record["MONTANT"] = chars_to_text(montant_chars)

                total_len = sum(len(v) for v in record.values())
                if total_len < 5:
                    continue  # bruit residuel (virgule/marque isolee), pas une vraie ligne
                if record["NO_COMPTE"].upper().replace(",", "").strip() in HEADER_WORDS:
                    continue  # ligne d'en-tete de colonnes, pas une donnee
                if record["DESIGNATION"].upper().strip() in NOISE_DESIGNATIONS:
                    continue  # ligne fantome (glyphes vectoriels mal isoles), pas une vraie donnee

                for name in NUMERIC_FIELDS:
                    for bad, good in LOOKALIKE_FIX.items():
                        record[name] = record[name].replace(bad, good)
                record["PROPRIETAIRE"] = ZERO_NEAR_LETTER_RE.sub("O", record["PROPRIETAIRE"])
                record["DESIGNATION"] = ZERO_NEAR_LETTER_RE.sub("O", record["DESIGNATION"])

                record["_x0"] = block[0]["x0"]
                record["_y0"] = block[0]["ycenter"]
                prelim.append(record)
            return prelim

        def merge_continuations(prelim):
            """Un nom de proprietaire ou une adresse trop longue deborde sur une 2e
            ligne PHYSIQUE dans le PDF (ex: nom -> 'LES HABITATIONS SOLIDAIRES' puis
            'DE LA SHAPEM' + montant ; ou adresse -> '1288 AV DES CANADIENS-DE-M' puis
            '#2208' + proprietaire + montant). Cette ligne-la n'a jamais de lot cadastral
            ni de no de compte valide -- on la fusionne dans la ligne precedente plutot
            que de la traiter comme une ligne a part. On exige que la ligne precedente
            n'ait PAS deja de montant : sinon elle est deja complete, et cette ligne sans
            no de compte est plutot une ligne separee dont le compte a rate son decodage
            (ex: "KHAJOUEI 12 722,11" appartenant a un tout autre compte) -- la
            fusionner serait une erreur.

            Un 2e cas distinct : une adresse trop longue deborde carrement dans la
            colonne du lot cadastral sur la 1ere ligne (ex: "1288 AV DES CANADIENS-
            DE-M" + "0NTREAL" comme "lot"), et la 2e ligne porte alors le vrai lot
            cadastral en plus du numero d'unite/proprietaire/montant (ex: "#2208" +
            "00 5888333" + "ETC LAURSON RIVIERE" + "5 361,91"). Ici le lot de la
            ligne precedente n'est pas un vrai lot -- c'est la suite de l'adresse --
            donc on le rattache a DESIGNATION et on prend le vrai lot sur la 2e ligne."""
            prelim.sort(key=lambda r: r["_y0"])
            merged = []
            for rec in prelim:
                is_continuation = (
                    merged
                    and not NO_COMPTE_RE.match(rec["NO_COMPTE"])
                    and not rec["CAD_LOT"]
                    and (rec["DESIGNATION"] or rec["PROPRIETAIRE"] or rec["MONTANT"])
                    and not merged[-1]["MONTANT"]
                )
                is_address_wrap = (
                    not is_continuation
                    and merged
                    and not NO_COMPTE_RE.match(rec["NO_COMPTE"])
                    and rec["CAD_LOT"]
                    and (rec["PROPRIETAIRE"] or rec["MONTANT"])
                    and NO_COMPTE_RE.match(merged[-1]["NO_COMPTE"])
                    and not merged[-1]["PROPRIETAIRE"]
                    and not merged[-1]["MONTANT"]
                )
                if is_continuation:
                    prev = merged[-1]
                    if rec["DESIGNATION"]:
                        prev["DESIGNATION"] = (prev["DESIGNATION"] + " " + rec["DESIGNATION"]).strip()
                    if rec["PROPRIETAIRE"]:
                        prev["PROPRIETAIRE"] = (prev["PROPRIETAIRE"] + " " + rec["PROPRIETAIRE"]).strip()
                    if not prev["MONTANT"] and rec["MONTANT"]:
                        prev["MONTANT"] = rec["MONTANT"]
                    continue
                if is_address_wrap:
                    prev = merged[-1]
                    base = prev["DESIGNATION"] + prev["CAD_LOT"]
                    if rec["DESIGNATION"]:
                        base += ("" if base.endswith("-") else " ") + rec["DESIGNATION"]
                    prev["DESIGNATION"] = ZERO_NEAR_LETTER_RE.sub("O", base.strip())
                    prev["CAD_LOT"] = rec["CAD_LOT"]
                    prev["PROPRIETAIRE"] = rec["PROPRIETAIRE"]
                    prev["MONTANT"] = rec["MONTANT"]
                    continue
                merged.append(rec)
            return merged

        left_prelim = build_prelim_records(left_rows, LEFT_COLUMNS, LEFT_PROP_MONTANT_RANGE)
        right_prelim = build_prelim_records(right_rows, RIGHT_COLUMNS, RIGHT_PROP_MONTANT_RANGE)

        for record in merge_continuations(left_prelim) + merge_continuations(right_prelim):
            record["ARRONDISSEMENT"] = section_for(page_num, record["_x0"], record["_y0"])
            record["PAGE"] = page_num + 1
            record["VALIDE_NO_COMPTE"] = bool(NO_COMPTE_RE.match(record["NO_COMPTE"]))
            record["VALIDE_MONTANT"] = bool(MONTANT_RE.match(record["MONTANT"]))
            del record["_x0"]
            del record["_y0"]
            records.append(record)

    doc.close()
    return records


def main(input_file, output_file, first_page, last_page):
    input_path = Path(input_file)
    if not input_path.is_file():
        print(f"Fichier introuvable: {input_path}")
        sys.exit(1)

    doc = fitz.open(str(input_path))
    end_page = last_page if last_page is not None else doc.page_count - 1
    end_page = min(end_page, doc.page_count - 1)
    doc.close()

    print(f"Traitement des pages {first_page + 1} a {end_page + 1}...")
    records = build_table(str(input_path), first_page, end_page)
    print(f"Lignes extraites: {len(records)}")

    df = pd.DataFrame(records, columns=[
        "ARRONDISSEMENT", "NO_COMPTE", "DESIGNATION", "CAD_LOT", "PROPRIETAIRE", "MONTANT",
        "VALIDE_NO_COMPTE", "VALIDE_MONTANT", "PAGE",
    ])
    df.to_excel(output_file, index=False)

    nb_invalides = (~df["VALIDE_NO_COMPTE"] | ~df["VALIDE_MONTANT"]).sum()
    print(f"Lignes signalees pour verification manuelle (format inattendu): {nb_invalides}")
    print(f"Termine -> {output_file}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Extrait le tableau de l'avis public Ville de Montreal vers Excel")
    ap.add_argument("--input-file", required=True)
    ap.add_argument("--output-file", required=True)
    ap.add_argument("--first-page", type=int, default=0)
    ap.add_argument("--last-page", type=int, default=None)
    args = ap.parse_args()
    main(args.input_file, args.output_file, args.first_page, args.last_page)
