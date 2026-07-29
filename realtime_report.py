import json
import os
import time
import sys
import traceback
from datetime import datetime, timezone, timedelta
from html import escape
import argparse
import re

# ============================================================
# DASHBOARD HTML (Blue Prism JSON -> HTML)
# ============================================================

REFRESH_SECONDS = 120
PAGE_SIZE = 100

WRAPPER_KEYS = ("rows", "data", "items", "results", "Results", "value")

try:
    from zoneinfo import ZoneInfo
    TORONTO_TZ = ZoneInfo("America/Toronto")
except Exception:
    TORONTO_TZ = None


# ============================================================
# JSON READ (SAFE)
# ============================================================

def _safe_load_json_text(text: str):
    if text is None:
        return None
    t = text.strip()
    if t == "":
        return None
    try:
        return json.loads(t)
    except Exception:
        return None


def read_rows(json_path: str):
    with open(json_path, "r", encoding="utf-8-sig") as f:
        raw = f.read()
    data = _safe_load_json_text(raw)
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in WRAPPER_KEYS:
            if k in data and isinstance(data[k], list):
                return data[k]
    raise Exception("JSON invalide: attendu une liste ou un objet contenant rows/data/items/results/value.")


def read_locked_set(locks_json_path: str):
    if not locks_json_path:
        return set()
    if not os.path.exists(locks_json_path):
        return set()
    try:
        with open(locks_json_path, "r", encoding="utf-8-sig") as f:
            raw = f.read()
        data = _safe_load_json_text(raw)
        if data is None:
            return set()
        locked = set()

        def _extract(items):
            for item in items:
                if isinstance(item, dict):
                    for v in item.values():
                        s = str(v).strip().lower()
                        if s:
                            locked.add(s)
                else:
                    s = str(item).strip().lower()
                    if s:
                        locked.add(s)

        if isinstance(data, list):
            _extract(data)
        elif isinstance(data, dict):
            for k in WRAPPER_KEYS:
                if k in data and isinstance(data[k], list):
                    _extract(data[k])
        return locked
    except Exception:
        return set()


# ============================================================
# FILE WRITE / DELETE
# ============================================================

def safe_write(final_path: str, content: str):
    """Écriture directe — pas de os.replace (compatibilité lecteur réseau)."""
    dirpath = os.path.dirname(final_path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(final_path, "w", encoding="utf-8") as f:
        f.write(content)


def try_delete_file(path: str):
    if not path:
        return
    for _ in range(5):
        try:
            if os.path.exists(path):
                os.remove(path)
            return
        except Exception:
            time.sleep(0.2)


# ============================================================
# MASTER FILE (accumulation journée + fusion incrémentale)
# ============================================================

def load_master(master_path: str):
    """Retourne les lignes du maître si elles datent d'aujourd'hui (Toronto), sinon repart à vide."""
    if not master_path or not os.path.exists(master_path):
        return []
    try:
        with open(master_path, "r", encoding="utf-8-sig") as f:
            data = _safe_load_json_text(f.read())
    except Exception:
        return []
    if not isinstance(data, dict):
        return []
    if data.get("date") != today_toronto_str():
        return []
    rows = data.get("rows")
    return rows if isinstance(rows, list) else []


def merge_into_master(master_path: str, new_rows: list, key_col: str):
    """Upsert new_rows (lot incrémental, ex. dernière heure) dans le fichier maître
    (journée complète) en se basant sur key_col, puis persiste et renvoie le résultat.
    Les lignes sans key_col renseigné sont simplement ajoutées (pas de dédoublonnage possible)."""
    master_rows = load_master(master_path)

    by_key = {}
    ordered_keys = []
    unkeyed = []
    for r in master_rows:
        if not isinstance(r, dict):
            continue
        k = str(r.get(key_col)).strip() if key_col else ""
        if k:
            if k not in by_key:
                ordered_keys.append(k)
            by_key[k] = r
        else:
            unkeyed.append(r)

    for r in new_rows:
        if not isinstance(r, dict):
            continue
        k = str(r.get(key_col)).strip() if key_col else ""
        if k:
            if k not in by_key:
                ordered_keys.append(k)
            by_key[k] = r
        else:
            unkeyed.append(r)

    merged = [by_key[k] for k in ordered_keys] + unkeyed

    master_content = json.dumps({"date": today_toronto_str(), "rows": merged}, ensure_ascii=False)
    safe_write(master_path, master_content)
    return merged


# ============================================================
# HELPERS
# ============================================================

def get_columns(rows):
    cols, seen = [], set()
    for r in rows:
        if not isinstance(r, dict):
            continue
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                cols.append(k)
    return cols


def is_blank_or_default_date(s: str) -> bool:
    if not s:
        return True
    return s.strip().startswith("0001-01-01")


def parse_iso_any_to_dt(s: str):
    if not s:
        return None
    raw = str(s).strip()
    if raw == "" or is_blank_or_default_date(raw):
        return None
    iso = raw.replace(" ", "T")
    if iso.endswith("Z"):
        iso = iso[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(iso)
    except Exception:
        return None


def _nth_weekday_of_month(year, month, weekday, n):
    d = datetime(year, month, 1)
    add = (weekday - d.weekday()) % 7
    return 1 + add + (n - 1) * 7


def toronto_offset_hours_for_utc(dt_utc: datetime) -> int:
    y = dt_utc.year
    start_day = _nth_weekday_of_month(y, 3, 6, 2)
    dst_start = datetime(y, 3, start_day, 7, 0, 0, tzinfo=timezone.utc)
    end_day   = _nth_weekday_of_month(y, 11, 6, 1)
    dst_end   = datetime(y, 11, end_day, 6, 0, 0, tzinfo=timezone.utc)
    return -4 if (dst_start <= dt_utc < dst_end) else -5


def utc_to_toronto_fallback(dt_utc: datetime) -> datetime:
    return dt_utc + timedelta(hours=toronto_offset_hours_for_utc(dt_utc))


def pretty_iso_to_toronto(s) -> str:
    if s is None:
        return ""
    raw = str(s).strip()
    if raw == "" or is_blank_or_default_date(raw):
        return ""
    dt = parse_iso_any_to_dt(raw)
    if dt is None:
        return raw
    dt_utc = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    dt_local = dt_utc.astimezone(TORONTO_TZ) if TORONTO_TZ else utc_to_toronto_fallback(dt_utc)
    return dt_local.strftime("%Y-%m-%d %H:%M:%S")


def today_toronto_str() -> str:
    dt_utc = datetime.now(timezone.utc)
    dt_local = dt_utc.astimezone(TORONTO_TZ) if TORONTO_TZ else utc_to_toronto_fallback(dt_utc)
    return dt_local.strftime("%Y-%m-%d")


# ============================================================
# SORTING
# ============================================================

def normalize_for_sort(v):
    if v is None:
        return (2, "")
    s = str(v).strip()
    if s == "" or is_blank_or_default_date(s):
        return (2, "")
    dt = parse_iso_any_to_dt(s)
    if dt is not None:
        dt = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
        return (0, dt)
    s_norm = s.replace(",", ".")
    if re.fullmatch(r"[-+]?\d+(\.\d+)?", s_norm):
        try:
            return (1, float(s_norm))
        except Exception:
            pass
    return (2, s.lower())


def sort_rows_in_python(rows, sort_col: str, desc: bool,
                        exception_col="", completed_col="", locked_set=None):
    locked_set = locked_set or set()

    def is_locked(r):
        if not isinstance(r, dict) or not locked_set:
            return False
        def clean(v):
            return "" if v is None else ("" if is_blank_or_default_date(str(v).strip()) else str(v).strip())
        if clean(r.get(exception_col)) or clean(r.get(completed_col)):
            return False
        return any(str(v).strip().lower() in locked_set for v in r.values())

    locked_rows = [r for r in rows if isinstance(r, dict) and is_locked(r)]
    other_rows  = [r for r in rows if not (isinstance(r, dict) and is_locked(r))]

    if sort_col and any(isinstance(r, dict) and sort_col in r for r in other_rows):
        rows_with, rows_empty = [], []
        for r in other_rows:
            if not isinstance(r, dict):
                continue
            sval = "" if r.get(sort_col) is None else str(r.get(sort_col)).strip()
            if sval == "" or is_blank_or_default_date(sval):
                rows_empty.append(r)
            else:
                rows_with.append(r)
        rows_with.sort(key=lambda rr: normalize_for_sort(rr.get(sort_col)), reverse=desc)
        other_rows = rows_with + rows_empty

    return locked_rows + other_rows


# ============================================================
# STATE
# ============================================================

def compute_state(row: dict, exception_col: str, completed_col: str, locked_set: set):
    def clean(v):
        if v is None:
            return ""
        s = str(v).strip()
        return "" if is_blank_or_default_date(s) else s

    exc  = clean(row.get(exception_col)) if exception_col else ""
    comp = clean(row.get(completed_col)) if completed_col else ""

    if exc  != "": return "\U0001f6a9", "exception"  # 🚩
    if comp != "": return "✅",     "completed"  # ✅
    if locked_set:
        for v in row.values():
            if str(v).strip().lower() in locked_set:
                return "\U0001f512", "locked"        # 🔒
    return "…", "pending"                       # …


def count_states(rows, exception_col, completed_col, locked_set):
    counts = {"exception": 0, "completed": 0, "locked": 0, "pending": 0}
    for row in rows:
        if isinstance(row, dict):
            _, state = compute_state(row, exception_col, completed_col, locked_set)
            counts[state] += 1
    return counts


# ============================================================
# JAVASCRIPT
# ============================================================

def _build_js(page_size, default_sort_col_js, default_sort_desc_js, refresh_seconds):
    return (
        "const PAGE_SIZE = " + str(page_size) + ";\n"
        "const DEFAULT_SORT_COLUMN = \"" + default_sort_col_js + "\";\n"
        "const DEFAULT_SORT_DESC = " + default_sort_desc_js + ";\n"
        "const REFRESH_SECONDS = " + str(refresh_seconds) + ";\n"
        "\n"

        # ---- Pagination (O(n)) ----
        "let currentPage = 1;\n"
        "\n"
        "function updatePagination() {\n"
        "  const tbody = document.querySelector('#table tbody');\n"
        "  const allRows = Array.from(tbody.rows);\n"
        "  const filteredRows = allRows.filter(r => r.dataset.filtered !== '0');\n"
        "  const total = filteredRows.length;\n"
        "  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));\n"
        "  if (currentPage > totalPages) currentPage = totalPages;\n"
        "  if (currentPage < 1) currentPage = 1;\n"
        "  const start = (currentPage - 1) * PAGE_SIZE;\n"
        "  const end   = start + PAGE_SIZE;\n"
        "  allRows.forEach(r => { r.style.display = 'none'; });\n"
        "  filteredRows.slice(start, end).forEach(r => { r.style.display = ''; });\n"
        "  document.getElementById('pageInfo').textContent =\n"
        "    `Page ${currentPage} / ${totalPages} — ${total} ligne(s)`;\n"
        "}\n"
        "\n"
        "function prevPage() { currentPage--; updatePagination(); }\n"
        "function nextPage() { currentPage++; updatePagination(); }\n"
        "\n"

        # ---- Countdown ----
        "let _countdown = REFRESH_SECONDS;\n"
        "function _tickCountdown() {\n"
        "  _countdown--;\n"
        "  if (_countdown < 0) _countdown = REFRESH_SECONDS;\n"
        "  const el = document.getElementById('countdown');\n"
        "  if (el) el.textContent = _countdown + 's';\n"
        "}\n"
        "setInterval(_tickCountdown, 1000);\n"
        "\n"

        # ---- Filters ----
        "function normalizeText(x) {\n"
        "  return (x ?? '').toString().trim().toLowerCase();\n"
        "}\n"
        "\n"
        "function wildcardMatch(cellText, patternRaw) {\n"
        "  const text = normalizeText(cellText);\n"
        "  const p    = normalizeText(patternRaw);\n"
        "  if (!p) return true;\n"
        "  if (p === '=blank')    return text === '';\n"
        "  if (p === '=notblank') return text !== '';\n"
        "  if (p.includes('*')) {\n"
        "    const esc = p.replace(/[.+?^${}()|[\\]\\\\]/g, '\\\\$&');\n"
        "    return new RegExp('^' + esc.replace(/\\*/g, '.*') + '$', 'i').test(text);\n"
        "  }\n"
        "  return text.includes(p);\n"
        "}\n"
        "\n"
        "function buildFilterRow() {\n"
        "  const headerCells = Array.from(document.querySelector('#table thead tr').cells);\n"
        "  const filterRow   = document.getElementById('filterRow');\n"
        "  filterRow.innerHTML = '';\n"
        "  headerCells.forEach((th, i) => {\n"
        "    const cell = document.createElement('th');\n"
        "    if (i === 0) {\n"
        "      const sel = document.createElement('select');\n"
        "      sel.id = 'stateFilter';\n"
        "      sel.innerHTML =\n"
        "        '<option value=\"\">Tous</option>'\n"
        "        + '<option value=\"exception\">\U0001f6a9 Exceptions</option>'\n"
        "        + '<option value=\"completed\">✅ Complété</option>'\n"
        "        + '<option value=\"locked\">\U0001f512 En cours</option>'\n"
        "        + '<option value=\"pending\">… En attente</option>';\n"
        "      sel.addEventListener('change', applyAllFilters);\n"
        "      cell.appendChild(sel);\n"
        "    } else {\n"
        "      const inp = document.createElement('input');\n"
        "      inp.type = 'text'; inp.placeholder = 'Contient… (ou *.*)';\n"
        "      inp.addEventListener('keyup', applyAllFilters);\n"
        "      cell.appendChild(inp);\n"
        "    }\n"
        "    filterRow.appendChild(cell);\n"
        "  });\n"
        "  const headerH = document.querySelector('#table thead tr:first-child').offsetHeight;\n"
        "  Array.from(filterRow.cells).forEach(c => { c.style.top = headerH + 'px'; });\n"
        "}\n"
        "\n"
        "function applyHighlight(term) {\n"
        "  document.querySelectorAll('#table tbody td[data-display]').forEach(td => {\n"
        "    const display = td.getAttribute('data-display') || '';\n"
        "    if (!term) { td.textContent = display; return; }\n"
        "    const esc = term.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');\n"
        "    td.innerHTML = display.replace(new RegExp('(' + esc + ')', 'gi'), '<mark>$1</mark>');\n"
        "  });\n"
        "}\n"
        "\n"
        "function applyAllFilters() {\n"
        "  const globalFilter = normalizeText(document.getElementById('search')?.value || '');\n"
        "  const filterValues = Array.from(document.getElementById('filterRow').cells)\n"
        "    .map(c => { const el = c.querySelector('input,select'); return el ? el.value : ''; });\n"
        "\n"
        "  Array.from(document.querySelector('#table tbody').rows).forEach(r => {\n"
        "    let ok = true;\n"
        "    if (globalFilter && !normalizeText(r.textContent).includes(globalFilter)) ok = false;\n"
        "    if (ok) {\n"
        "      for (let col = 0; col < filterValues.length; col++) {\n"
        "        const f = filterValues[col]; if (!f) continue;\n"
        "        if (col === 0) {\n"
        "          if (normalizeText(r.cells[0].getAttribute('data-raw')) !== normalizeText(f))\n"
        "            { ok = false; break; }\n"
        "        } else {\n"
        "          if (!wildcardMatch(r.cells[col].getAttribute('data-raw') || '', f))\n"
        "            { ok = false; break; }\n"
        "        }\n"
        "      }\n"
        "    }\n"
        "    r.dataset.filtered = ok ? '1' : '0';\n"
        "  });\n"
        "\n"
        "  currentPage = 1;\n"
        "  updatePagination();\n"
        "  applyHighlight(globalFilter);\n"
        "}\n"
        "\n"
        "function resetAllFilters() {\n"
        "  const s = document.getElementById('search'); if (s) s.value = '';\n"
        "  Array.from(document.getElementById('filterRow').cells).forEach(c => {\n"
        "    const inp = c.querySelector('input');  if (inp) inp.value = '';\n"
        "    const sel = c.querySelector('select'); if (sel) sel.value = '';\n"
        "  });\n"
        "  Array.from(document.querySelector('#table tbody').rows)\n"
        "    .forEach(r => { r.dataset.filtered = '1'; });\n"
        "  currentPage = 1;\n"
        "  updatePagination();\n"
        "  applyHighlight('');\n"
        "}\n"
        "\n"
        "function filterByState(state) {\n"
        "  const sel = document.getElementById('stateFilter');\n"
        "  if (sel) { sel.value = state; applyAllFilters(); }\n"
        "}\n"
        "\n"

        # ---- Export CSV ----
        "function exportCSV() {\n"
        "  const headers = Array.from(document.querySelectorAll('#table thead tr:first-child th'))\n"
        "    .map(th => {\n"
        "      const txt = (th.childNodes[0] ? th.childNodes[0].textContent : th.textContent || '').trim();\n"
        "      return '\"' + txt.replace(/\"/g, '\"\"') + '\"';\n"
        "    });\n"
        "  const filteredRows = Array.from(document.querySelector('#table tbody').rows)\n"
        "    .filter(r => r.dataset.filtered !== '0');\n"
        "  const lines = filteredRows.map(r =>\n"
        "    Array.from(r.cells).map(td => {\n"
        "      const v = (td.getAttribute('data-raw') || '').trim();\n"
        "      return '\"' + v.replace(/\"/g, '\"\"') + '\"';\n"
        "    }).join(',')\n"
        "  );\n"
        "  const csv = '\\uFEFF' + [headers.join(','), ...lines].join('\\r\\n');\n"
        "  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });\n"
        "  const url  = URL.createObjectURL(blob);\n"
        "  const a    = document.createElement('a');\n"
        "  a.href = url; a.download = 'export.csv';\n"
        "  document.body.appendChild(a); a.click();\n"
        "  setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 0);\n"
        "}\n"
        "\n"

        # ---- Sorting ----
        "let sortState = { col: -1, asc: true };\n"
        "\n"
        "function compareCells(aRaw, bRaw, asc) {\n"
        "  aRaw = (aRaw || '').trim(); bRaw = (bRaw || '').trim();\n"
        "  const aE = aRaw === '', bE = bRaw === '';\n"
        "  if (aE && bE) return 0;\n"
        "  if (aE) return 1; if (bE) return -1;\n"
        "  const isoRe = /^\\d{4}-\\d{2}-\\d{2}T/;\n"
        "  if (isoRe.test(aRaw) && isoRe.test(bRaw)) {\n"
        "    const aMs = Date.parse(aRaw), bMs = Date.parse(bRaw);\n"
        "    if (!isNaN(aMs) && !isNaN(bMs)) return asc ? aMs - bMs : bMs - aMs;\n"
        "  }\n"
        "  const numRe = /^[-+]?\\d+(\\.\\d+)?$/;\n"
        "  const aN = aRaw.replace(',','.'), bN = bRaw.replace(',','.');\n"
        "  if (numRe.test(aN) && numRe.test(bN)) {\n"
        "    const a = parseFloat(aN), b = parseFloat(bN);\n"
        "    return asc ? a - b : b - a;\n"
        "  }\n"
        "  const cmp = aRaw.localeCompare(bRaw, 'fr', { sensitivity: 'base' });\n"
        "  return asc ? cmp : -cmp;\n"
        "}\n"
        "\n"
        "function sortTable(colIndex, forceAsc = null) {\n"
        "  const tbody = document.querySelector('#table tbody');\n"
        "  const trs   = Array.from(tbody.rows);\n"
        "  if (forceAsc === null) {\n"
        "    if (sortState.col === colIndex) sortState.asc = !sortState.asc;\n"
        "    else { sortState.col = colIndex; sortState.asc = true; }\n"
        "  } else { sortState.col = colIndex; sortState.asc = forceAsc; }\n"
        "  trs.sort((a, b) => compareCells(\n"
        "    a.cells[colIndex].getAttribute('data-raw') || '',\n"
        "    b.cells[colIndex].getAttribute('data-raw') || '',\n"
        "    sortState.asc));\n"
        "  trs.forEach(tr => tbody.appendChild(tr));\n"
        "  Array.from(document.querySelector('#table thead tr').cells).forEach((th, i) => {\n"
        "    const sp = th.querySelector('.arrow'); if (!sp) return;\n"
        "    sp.textContent = (i === sortState.col) ? (sortState.asc ? '▲' : '▼') : '';\n"
        "  });\n"
        "  applyAllFilters();\n"
        "}\n"
        "\n"
        "function findColIndex(name) {\n"
        "  if (!name) return -1;\n"
        "  return Array.from(document.querySelectorAll('#table thead tr:first-child th'))\n"
        "    .findIndex(th => (th.textContent || '').trim().startsWith(name));\n"
        "}\n"
        "\n"
        # Affiche juste la flèche de tri sans réordonner le DOM : l'ordre initial
        # (verrouillés en tête) vient déjà du Python et ne doit pas être écrasé.
        "function showInitialSortArrow(colIndex, asc) {\n"
        "  sortState.col = colIndex;\n"
        "  sortState.asc = asc;\n"
        "  Array.from(document.querySelector('#table thead tr').cells).forEach((th, i) => {\n"
        "    const sp = th.querySelector('.arrow'); if (!sp) return;\n"
        "    sp.textContent = (i === sortState.col) ? (sortState.asc ? '▲' : '▼') : '';\n"
        "  });\n"
        "}\n"
        "\n"
        "window.addEventListener('load', () => {\n"
        "  buildFilterRow();\n"
        "  Array.from(document.querySelector('#table tbody').rows)\n"
        "    .forEach(r => { r.dataset.filtered = '1'; });\n"
        "  applyAllFilters();\n"
        "  if (DEFAULT_SORT_COLUMN) {\n"
        "    const idx = findColIndex(DEFAULT_SORT_COLUMN);\n"
        "    if (idx >= 0) showInitialSortArrow(idx, !DEFAULT_SORT_DESC);\n"
        "  }\n"
        "});\n"
    )


# ============================================================
# HTML BUILDERS
# ============================================================

def build_html_no_cases(title):
    now   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="refresh" content="{REFRESH_SECONDS}">
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: Arial; margin: 16px; }}
    .card {{ border: 1px solid #ddd; padding: 14px; border-radius: 10px; max-width: 820px; }}
    .muted {{ color: #555; }}
  </style>
</head>
<body>
  <h2>{escape(title)}</h2>
  <div class="card">
    <h3>Aucun cas traité aujourd'hui</h3>
    <p class="muted">Données du {escape(today)} · Dernière mise à jour: {escape(now)}</p>
    <p>Aucune donnée n'a été reçue pour l'instant.</p>
  </div>
</body>
</html>"""


def build_html_table(rows, cols, title, default_sort_col, default_sort_desc,
                     exception_col, completed_col, locked_set):

    now   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")

    counts = count_states(rows, exception_col, completed_col, locked_set)
    status_bar = (
        f'<button class="badge badge-all"       onclick="filterByState(\'\')">Tous ({len(rows)})</button>'
        f'<button class="badge badge-exception" onclick="filterByState(\'exception\')">\U0001f6a9 Exceptions ({counts["exception"]})</button>'
        f'<button class="badge badge-completed" onclick="filterByState(\'completed\')">✅ Complété ({counts["completed"]})</button>'
        f'<button class="badge badge-locked"    onclick="filterByState(\'locked\')">\U0001f512 En cours ({counts["locked"]})</button>'
        f'<button class="badge badge-pending"   onclick="filterByState(\'pending\')">… En attente ({counts["pending"]})</button>'
    )

    # Colonnes source exclues du tableau — remplacées par "Dernière mise à jour"
    skip_cols = {c for c in (exception_col, completed_col) if c}
    display_data_cols = [c for c in cols if c not in skip_cols]

    LAST_UPDATE_COL = "Dernière mise à jour"
    first_col  = display_data_cols[:1]
    other_cols = display_data_cols[1:]
    display_cols = ["État"] + first_col + [LAST_UPDATE_COL] + other_cols

    th_html = "".join(
        f'<th onclick="sortTable({i})">{escape(c)} <span class="arrow"></span></th>'
        for i, c in enumerate(display_cols)
    )

    def _get_col_raw(row, col):
        if not col:
            return ""
        v = row.get(col)
        s = "" if v is None else str(v).strip()
        return "" if is_blank_or_default_date(s) else s

    def _make_td(raw_val):
        raw_stripped = str(raw_val).strip() if raw_val else ""
        if is_blank_or_default_date(raw_stripped):
            raw_stripped = ""
        pretty = pretty_iso_to_toronto(raw_stripped)
        return (f'<td data-raw="{escape(raw_stripped)}" data-display="{escape(pretty)}">'
                f'{escape(pretty)}</td>')

    tr_list = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        icon, state = compute_state(r, exception_col, completed_col, locked_set)
        tds = [f'<td data-raw="{escape(state)}" class="state">{escape(icon)}</td>']

        for c in first_col:
            tds.append(_make_td(r.get(c)))

        last_update_raw    = _get_col_raw(r, exception_col) or _get_col_raw(r, completed_col)
        last_update_pretty = pretty_iso_to_toronto(last_update_raw)
        tds.append(
            f'<td data-raw="{escape(last_update_raw)}" data-display="{escape(last_update_pretty)}">'
            f'{escape(last_update_pretty)}</td>'
        )

        for c in other_cols:
            tds.append(_make_td(r.get(c)))

        tr_list.append(f'<tr class="row-{state}">' + "".join(tds) + "</tr>")

    tbody = "\n".join(tr_list)
    default_sort_col_js  = escape(default_sort_col or "")
    default_sort_desc_js = "true" if default_sort_desc else "false"
    js = _build_js(PAGE_SIZE, default_sort_col_js, default_sort_desc_js, REFRESH_SECONDS)

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="refresh" content="{REFRESH_SECONDS}">
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: Arial; margin: 16px; }}
    input  {{ padding: 8px; width: 420px; }}
    button {{ padding: 8px 10px; cursor: pointer; }}

    .controls {{
      display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-top: 8px;
    }}
    .pager button {{ padding: 6px 10px; }}
    .pager span   {{ margin: 0 6px; color: #333; }}

    .status-bar {{
      display: flex; gap: 8px; align-items: center; margin: 8px 0; flex-wrap: wrap;
    }}
    .badge {{
      padding: 4px 14px; border-radius: 20px; border: none;
      font-size: 13px; font-weight: bold; cursor: pointer;
      transition: opacity .15s;
    }}
    .badge:hover     {{ opacity: .75; }}
    .badge-all       {{ background: #e8e8e8; color: #333; }}
    .badge-exception {{ background: #fff1f1; color: #c0392b; }}
    .badge-completed {{ background: #f3fff5; color: #27ae60; }}
    .badge-locked    {{ background: #eef4ff; color: #2980b9; }}
    .badge-pending   {{ background: #fffdf0; color: #856404; }}

    .refresh-info {{ font-size: 12px; color: #888; margin-left: 8px; }}

    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
    th, td {{ border: 1px solid #ddd; padding: 6px; font-size: 13px; }}
    th {{
      background: #f2f2f2; position: sticky; top: 0; z-index: 2;
      cursor: pointer; user-select: none; white-space: nowrap;
    }}
    #filterRow th {{
      position: sticky; z-index: 2; background: #fafafa;
    }}
    tr:nth-child(even) {{ background: #fafafa; }}
    .arrow  {{ font-size: 11px; margin-left: 4px; color: #666; }}
    td.state {{ text-align: center; font-size: 15px; }}

    tr.row-exception td {{ background: #fff1f1; }}
    tr.row-pending   td {{ background: #fffdf0; }}
    tr.row-completed td {{ background: #f3fff5; }}
    tr.row-locked    td {{ background: #eef4ff; }}

    #filterRow input, #filterRow select {{
      width: 95%; padding: 6px; font-size: 12px;
    }}

    mark {{ background: #ffe066; padding: 0 2px; border-radius: 2px; }}
  </style>
</head>
<body>
  <h2>{escape(title)}</h2>
  <p>
    Données du {escape(today)} &middot; Mise à jour: {escape(now)}
    &middot; {len(rows)} ligne(s)
    <span class="refresh-info">&#x21bb; <span id="countdown">{REFRESH_SECONDS}s</span></span>
  </p>

  <div class="status-bar">{status_bar}</div>

  <div class="controls">
    <input id="search" type="text" placeholder="Recherche globale..." onkeyup="applyAllFilters()">
    <button onclick="resetAllFilters()">Reset filtres</button>
    <button onclick="exportCSV()">&#11123; Export CSV</button>
    <div class="pager">
      <button onclick="prevPage()">&#9664;</button>
      <span id="pageInfo"></span>
      <button onclick="nextPage()">&#9654;</button>
    </div>
  </div>

  <table id="table">
    <thead>
      <tr>{th_html}</tr>
      <tr id="filterRow"></tr>
    </thead>
    <tbody>{tbody}</tbody>
  </table>

<script>
{js}
</script>
</body>
</html>"""


# ============================================================
# PIPELINE
# ============================================================

def run_build(input_json, output_html, title, sort_col, sort_desc,
              exception_col, completed_col, locks_json,
              master_json="", key_col=""):
    rows = read_rows(input_json)

    if master_json:
        rows = merge_into_master(master_json, rows, key_col)

    locked_set = read_locked_set(locks_json)
    rows       = sort_rows_in_python(rows, sort_col, sort_desc,
                                     exception_col=exception_col,
                                     completed_col=completed_col,
                                     locked_set=locked_set)

    if len(rows) == 0:
        html = build_html_no_cases(title)
    else:
        cols = get_columns(rows)
        html = build_html_table(
            rows=rows, cols=cols, title=title,
            default_sort_col=sort_col, default_sort_desc=sort_desc,
            exception_col=exception_col, completed_col=completed_col,
            locked_set=locked_set,
        )

    safe_write(output_html, html)
    try_delete_file(input_json)
    try_delete_file(locks_json)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_json",    required=True)
    ap.add_argument("--output_html",   required=True)
    ap.add_argument("--title",         required=True)
    ap.add_argument("--sort_col",      default="")
    ap.add_argument("--sort_desc",     default="true")
    ap.add_argument("--exception_col", default="")
    ap.add_argument("--completed_col", default="")
    ap.add_argument("--locks_json",    default="")
    ap.add_argument("--master_json",   default="", help="Fichier persistant qui accumule la journée; --input_json ne fournit alors qu'un lot incrémental (ex. dernière heure)")
    ap.add_argument("--key_col",       default="", help="Colonne identifiant unique un cas, requise si --master_json est utilisé")
    args = ap.parse_args()

    sort_desc = str(args.sort_desc).strip().lower() in ("true", "1", "yes", "y")

    if args.master_json and not args.key_col:
        print("ERROR: --key_col est requis quand --master_json est utilisé", file=sys.stderr)
        sys.exit(1)

    try:
        run_build(
            input_json=args.input_json,
            output_html=args.output_html,
            title=args.title,
            sort_col=args.sort_col,
            sort_desc=sort_desc,
            exception_col=args.exception_col,
            completed_col=args.completed_col,
            locks_json=args.locks_json,
            master_json=args.master_json,
            key_col=args.key_col,
        )
        print(f"SUCCESS: HTML generated -> {args.output_html}")
        sys.exit(0)

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
