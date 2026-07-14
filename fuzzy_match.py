import argparse
import sys
import os

try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "libs"))
    from rapidfuzz import fuzz as _fuzz
    def _score(keyword, text):
        return _fuzz.partial_ratio(keyword.lower(), text.lower())
except Exception:
    import difflib
    def _score(keyword, text):
        keyword = keyword.lower()
        text = text.lower()
        klen = len(keyword)
        if klen == 0:
            return 100.0
        if len(text) <= klen:
            return difflib.SequenceMatcher(None, keyword, text).ratio() * 100
        best = 0.0
        for i in range(len(text) - klen + 1):
            ratio = difflib.SequenceMatcher(None, keyword, text[i:i + klen]).ratio() * 100
            if ratio > best:
                best = ratio
        return best


def fuzzy_match(text: str, keyword: str, threshold: int) -> None:
    if not keyword.strip():
        sys.stdout.write("ERROR|message=keyword_is_empty\n")
        sys.stdout.flush()
        sys.exit(1)

    if not text.strip():
        sys.stdout.write("ERROR|message=text_is_empty\n")
        sys.stdout.flush()
        sys.exit(1)

    score = round(_score(keyword, text), 1)
    found = score >= threshold

    sys.stdout.write(f"ok|score={score}|found={'true' if found else 'false'}|threshold={threshold}\n")
    sys.stdout.flush()
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Fuzzy match d'un keyword dans un texte"
    )
    parser.add_argument("--text", required=True, help="Texte dans lequel chercher")
    parser.add_argument("--keyword", required=True, help="Mot ou phrase à rechercher")
    parser.add_argument("--threshold", type=int, required=True, help="Score minimum pour considérer trouvé (ex: 80)")

    args = parser.parse_args()
    fuzzy_match(args.text, args.keyword, args.threshold)


if __name__ == "__main__":
    main()
