# src/build.py — static site generator for the Ally multilingual landing page.
#
# One template (template.html) + one content file per locale (content/{loc}.json)
# produce every /{loc}/index.html. Structure, design and assets are identical
# across locales; only localized content (and text direction) may differ.
#
# Usage:  python src/build.py          # generate all locale pages
#         python src/build.py --check  # verify generated pages are up to date
import argparse
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

LOCALES = ["ar", "az", "de", "en", "es", "fr", "hi", "id", "it", "ja", "ko", "ku", "nl", "pt", "ru", "tr", "zh"]

LANG_NAMES = {
    "ar": "العربية", "az": "Azərbaycanca", "de": "Deutsch", "en": "English",
    "es": "Español", "fr": "Français", "hi": "हिन्दी", "id": "Bahasa Indonesia",
    "it": "Italiano", "ja": "日本語", "ko": "한국어", "ku": "Kurdî",
    "nl": "Nederlands", "pt": "Português", "ru": "Русский", "tr": "Türkçe", "zh": "中文",
}

OG_LOCALES = {
    "ar": "ar_AR", "az": "az_AZ", "de": "de_DE", "en": "en_US", "es": "es_ES",
    "fr": "fr_FR", "hi": "hi_IN", "id": "id_ID", "it": "it_IT", "ja": "ja_JP",
    "ko": "ko_KR", "ku": "ku_TR", "nl": "nl_NL", "pt": "pt_BR", "ru": "ru_RU",
    "tr": "tr_TR", "zh": "zh_CN",
}

APP_URL = "https://allyishere.com"
GITHUB_URL = "https://github.com/VertexCorporation/Ally"


def load_content(loc):
    return json.loads((SRC / "content" / f"{loc}.json").read_text(encoding="utf-8"))


def render(loc, template, en):
    data = load_content(loc)
    missing = [k for k in en if k not in data or data[k] in (None, "")]
    for k in missing:
        data[k] = en[k]
    lang = data.get("_lang", loc)
    ddir = data.get("_dir", "ltr")

    values = {}
    for k, v in data.items():
        if k.startswith("_") or k == "hero_words":
            continue
        if not isinstance(v, str):
            raise SystemExit(f"{loc}: key {k!r} must be a string")
        values[k] = html.escape(v, quote=True)

    # hero words -> spans (CSS staggers them; plain text fallback keeps order)
    words = load_content(loc).get("hero_words") or en["hero_words"]
    if not isinstance(words, list) or not words:
        raise SystemExit(f"{loc}: hero_words must be a non-empty list")
    values["HERO_WORDS"] = " ".join(
        f'<span class="word">{html.escape(w_, quote=True)}</span>' for w_ in words
    )

    values["LOCALE"] = loc
    values["LANG"] = lang
    values["DIR"] = ddir
    values["OG_LOCALE"] = OG_LOCALES[loc]

    hreflang = "\n".join(
        f'  <link rel="alternate" hreflang="{c}" href="{APP_URL}/{c}/">' for c in LOCALES
    ) + f'\n  <link rel="alternate" hreflang="x-default" href="{APP_URL}/en/">'
    values["HREFLANG"] = hreflang

    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": "https://vertexishere.com/#organization",
                "name": "Vertex",
                "url": "https://vertexishere.com",
                "logo": "https://vertexishere.com/assets/logo.svg",
            },
            {
                "@type": "WebSite",
                "@id": f"{APP_URL}/#website",
                "url": APP_URL,
                "name": "Ally",
                "inLanguage": lang,
                "publisher": {"@id": "https://vertexishere.com/#organization"},
            },
            {
                "@type": "WebPage",
                "url": f"{APP_URL}/{loc}/",
                "name": data["og_title"],
                "description": data["og_description"],
                "inLanguage": lang,
                "isPartOf": {"@id": f"{APP_URL}/#website"},
            },
        ],
    }, ensure_ascii=False, separators=(",", ":"))
    values["JSONLD"] = f'  <script type="application/ld+json">{jsonld}</script>'

    lang_menu = "\n".join(
        f'            <a href="/{c}/" lang="{c}" hreflang="{c}"'
        + (' aria-current="true"' if c == loc else "")
        + f'>{html.escape(LANG_NAMES[c], quote=True)}</a>'
        for c in LOCALES
    )
    values["LANG_MENU"] = lang_menu

    def sub(m):
        key = m.group(1)
        if key not in values:
            raise SystemExit(f"{loc}: template placeholder {key!r} has no value")
        return values[key]

    out = re.sub(r"\{\{(\w+)\}\}", sub, template)
    leftover = re.search(r"\{\{(\w+)\}\}", out)
    if leftover:
        raise SystemExit(f"{loc}: unsubstituted placeholder {leftover.group(1)!r}")
    return out + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify pages are up to date without writing")
    args = ap.parse_args()

    template = (SRC / "template.html").read_text(encoding="utf-8")
    en = load_content("en")

    problems = []
    for loc in LOCALES:
        try:
            page = render(loc, template, en)
        except SystemExit as e:
            problems.append(str(e))
            continue
        target = ROOT / loc / "index.html"
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != page:
                problems.append(f"{loc}/index.html is out of date (run: python src/build.py)")
        else:
            target.write_text(page, encoding="utf-8", newline="\n")
            print(f"built {loc}/index.html ({len(page.encode('utf-8'))} bytes)")

    if problems:
        print("BUILD PROBLEMS:", file=sys.stderr)
        for p in problems:
            print(" -", p, file=sys.stderr)
        sys.exit(1)
    if args.check:
        print("check OK: all", len(LOCALES), "locale pages are up to date")


if __name__ == "__main__":
    main()
