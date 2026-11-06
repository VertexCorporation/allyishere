# qa-check.py — production QA for the allyishere static site.
#
# Checks:
#   1. generated pages are in sync with src/template.html + src/content/*.json
#   2. content files: same key set in every locale, no empty values
#   3. every page: structure, SEO metadata, a11y basics, no legacy/debug leftovers
#   4. cross-locale structural invariants (one design system, no per-language DOM)
#   5. encoding hygiene (UTF-8 without BOM, no double-encoded mojibake)
#   6. internal links/assets resolve, images carry alt + intrinsic size
#   7. CSS custom properties all defined; JS parses
#   8. sitemap/robots consistency
#
# Usage: python qa-check.py
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
LOCALES = ["ar", "az", "de", "en", "es", "fr", "hi", "id", "it", "ja", "ko", "ku", "nl", "pt", "ru", "tr", "zh"]

failures = []
warnings = []


def fail(msg):
    failures.append(msg)


def warn(msg):
    warnings.append(msg)


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


# ---- 1. build freshness ------------------------------------------------------
build = subprocess.run([sys.executable, str(ROOT / "src" / "build.py"), "--check"],
                       cwd=ROOT, capture_output=True, text=True)
if build.returncode != 0:
    fail("generated pages are out of date with template/content (run: python src/build.py)")

# ---- 2. content parity -------------------------------------------------------
contents = {}
for loc in LOCALES:
    try:
        contents[loc] = json.loads(read(f"src/content/{loc}.json"))
    except Exception as e:  # noqa: BLE001
        fail(f"src/content/{loc}.json is not valid JSON: {e}")

if len(contents) == len(LOCALES):
    en_keys = set(contents["en"])
    for loc in LOCALES:
        keys = set(contents[loc])
        missing = en_keys - keys
        extra = keys - en_keys
        if missing:
            fail(f"src/content/{loc}.json missing keys: {sorted(missing)}")
        if extra:
            fail(f"src/content/{loc}.json has extra keys: {sorted(extra)}")
        for k, v in contents[loc].items():
            if k == "hero_words":
                if not (isinstance(v, list) and v and all(isinstance(w, str) and w.strip() for w in v)):
                    fail(f"src/content/{loc}.json: hero_words must be a non-empty list of strings")
                continue
            if isinstance(v, str) and not v.strip():
                fail(f"src/content/{loc}.json: empty value for {k!r}")

# ---- helpers -----------------------------------------------------------------
TAG_RE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)((?:\"[^\"]*\"|'[^']*'|[^'\">])*)>")


def structure_signature(html_text):
    """Tag+class sequence with localized hero words collapsed — the shape of the page."""
    text = re.sub(r'<span class="word">[^<]*</span>', "W", html_text)
    sig = []
    for close, tag, attrs in TAG_RE.findall(text):
        if tag.lower() in ("br", "img", "meta", "link", "path", "circle", "hr", "source"):
            continue
        m = re.search(r'class="([^"]*)"', attrs)
        cls = re.sub(r"\b(reveal|delay-\d+)\b", "", m.group(1)).strip() if m else ""
        sig.append(("/" if close else "") + tag.lower() + (f".{cls}" if cls else ""))
    return sig


def check_links(rel, html_text):
    for m in re.finditer(r'(?:href|src)="([^"]+)"', html_text):
        url = m.group(1)
        if url.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
            continue
        target = url.lstrip("/")
        if not (ROOT / target).exists():
            fail(f"{rel}: broken internal reference {url}")


FORBIDDEN = [
    (r"console\.(log|debug|info)\(", "console logging"),
    (r"\bTODO\b|\bFIXME\b|\bXXX\b", "TODO/FIXME marker"),
    (r"autoplay", "autoplay attribute"),
    (r"@latest", "unpinned CDN dependency"),
    (r'style="', "inline style"),
    (r"story-scroll-cue", "leftover scroll cue"),
    (r'theme-toggle-btn|id="themeToggle"', "legacy floating theme toggle"),
    (r'class="divider"', "legacy divider"),
    (r"alpha-notice|disclaimer-box|highlight-section", "legacy legal styling class"),
    (r"Ã[\x80-\xBF]|Ä[\x80-\xBF]|Å[\x80-\xBF]|â€", "double-encoded mojibake"),
]


# ---- 3. locale landing pages --------------------------------------------------
signatures = {}
for loc in LOCALES:
    rel = f"{loc}/index.html"
    raw = (ROOT / rel).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        fail(f"{rel}: UTF-8 BOM present")
    try:
        t = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        fail(f"{rel}: invalid UTF-8 ({e})")
        continue

    lang_m = re.search(r'<html[^>]*\blang="([^"]*)"', t)
    if not lang_m or lang_m.group(1) != loc:
        fail(f"{rel}: html lang must be {loc!r}")
    dir_m = re.search(r'<html[^>]*\bdir="([^"]*)"', t)
    expected_dir = "rtl" if loc == "ar" else "ltr"
    if not dir_m or dir_m.group(1) != expected_dir:
        fail(f"{rel}: html dir must be {expected_dir!r}")

    if len(re.findall(r"<h1[ >]", t)) != 1:
        fail(f"{rel}: exactly one <h1> required")
    if t.count('<main id="main">') != 1 or t.count("</main>") != 1:
        fail(f"{rel}: main landmark mismatch")
    if t.count("<footer") != 1:
        fail(f"{rel}: exactly one footer required")
    if 'class="skip-link"' not in t:
        fail(f"{rel}: skip link missing")

    if f'canonical" href="https://allyishere.com/{loc}/"' not in t:
        fail(f"{rel}: canonical must be https://allyishere.com/{loc}/")
    if t.count('rel="alternate" hreflang=') != 18:  # 17 locales + x-default
        fail(f"{rel}: hreflang cluster incomplete")
    if 'property="og:title"' not in t or 'property="og:image"' not in t or 'property="og:locale"' not in t:
        fail(f"{rel}: Open Graph metadata incomplete")
    if "application/ld+json" not in t:
        fail(f"{rel}: JSON-LD missing")
    if 'name="description"' not in t:
        fail(f"{rel}: meta description missing")
    if 'name="theme-color"' not in t:
        fail(f"{rel}: theme-color missing")

    # the language switcher must offer every locale and mark the current one
    menu = re.search(r'<div class="lang-menu"[^>]*>(.*?)\n\s*</div>', t, re.S)
    if not menu:
        fail(f"{rel}: language menu missing")
    else:
        offers = set(re.findall(r'href="/([a-z]{2})/"', menu.group(1)))
        if offers != set(LOCALES):
            fail(f"{rel}: language menu does not offer every locale")
        if f'href="/{loc}/" lang="{loc}" hreflang="{loc}" aria-current="true"' not in menu.group(1):
            fail(f"{rel}: current language not marked in menu")

    # controls must be reachable and labeled
    if 'id="langBtn"' not in t or 'aria-haspopup="true"' not in t:
        fail(f"{rel}: language button misconfigured")
    if 'id="hamburgerBtn"' not in t or 'aria-controls="mobileMenu"' not in t:
        fail(f"{rel}: hamburger misconfigured")
    if 'id="themeBtn"' not in t or "aria-label" not in t:
        fail(f"{rel}: theme button misconfigured")

    # images must not break layout
    for m in re.finditer(r"<img[^>]*>", t):
        img = m.group(0)
        if 'alt="' not in img:
            fail(f"{rel}: img without alt ({img[:60]})")
        if "width=" not in img or "height=" not in img:
            fail(f"{rel}: img without intrinsic size ({img[:60]})")

    for pat, label in FORBIDDEN:
        if re.search(pat, t):
            fail(f"{rel}: {label} found")

    check_links(rel, t)
    signatures[loc] = structure_signature(t)

base_sig = signatures.get("en")
if base_sig:
    for loc in LOCALES:
        if signatures[loc] != base_sig:
            a, b = signatures[loc], base_sig
            i = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            fail(f"{loc}/index.html: DOM structure differs from en/ at element {i} "
                 f"({a[i:i + 3]!r} vs {b[i:i + 3]!r})")


# ---- 4. utility pages ----------------------------------------------------------
# root redirector
t = read("index.html")
if 'http-equiv="refresh"' not in t or "window.location.replace" not in t:
    fail("index.html: root must redirect (meta refresh + JS negotiation)")
if 'rel="canonical" href="https://allyishere.com/"' not in t:
    fail("index.html: canonical missing")
for pat, label in FORBIDDEN:
    if re.search(pat, t):
        fail(f"index.html: {label} found")

# 404
t = read("404.html")
if 'content="noindex"' not in t:
    fail("404.html: must be noindex")
if 'id="nf-message"' not in t or 'id="nf-home"' not in t:
    fail("404.html: localization hooks missing")
if t.count("lang: ") < 17:
    fail("404.html: localization table incomplete")
for pat, label in FORBIDDEN:
    if re.search(pat, t):
        fail(f"404.html: {label} found")
check_links("404.html", t)

# legal pages (English-only source of truth, full site chrome)
for rel in ("privacy-policy.html", "terms-of-service.html"):
    t = read(rel)
    if 'lang="en"' not in t:
        fail(f"{rel}: must declare lang=en")
    if 'href="/main.css"' not in t:
        fail(f"{rel}: must use the shared design system (/main.css)")
    if 'id="themeBtn"' not in t:
        fail(f"{rel}: theme control missing")
    if 'class="policy-main"' not in t or "<h1" not in t:
        fail(f"{rel}: content structure missing")
    for pat, label in FORBIDDEN:
        if re.search(pat, t):
            fail(f"{rel}: {label} found")
    check_links(rel, t)

# ---- 5. CSS: every referenced custom property must be defined --------------------
css = read("main.css")
defined = set(re.findall(r"(--[\w-]+)\s*:", css))
used = set(re.findall(r"var\(\s*(--[\w-]+)", css))
undefined = used - defined
if undefined:
    fail(f"main.css: undefined custom properties: {sorted(undefined)}")
for pat, label in FORBIDDEN:
    if re.search(pat, css):
        fail(f"main.css: {label} found")
if "prefers-reduced-motion" not in css:
    fail("main.css: reduced-motion support missing")

# ---- 6. JS parses ----------------------------------------------------------------
node = shutil.which("node")
if node:
    check = subprocess.run([node, "--check", str(ROOT / "main.js")], capture_output=True, text=True)
    if check.returncode != 0:
        fail(f"main.js: syntax error: {check.stderr.strip()}")
else:
    warn("node not available — main.js not syntax-checked")
js = read("main.js")
for pat, label in FORBIDDEN:
    if re.search(pat, js):
        fail(f"main.js: {label} found")

# ---- 7. sitemap / robots ----------------------------------------------------------
robots = read("robots.txt")
if "Sitemap: https://allyishere.com/sitemap.xml" not in robots:
    fail("robots.txt: sitemap line missing")
sitemap = read("sitemap.xml")
locs_in_sitemap = set(re.findall(r"<loc>https://allyishere\.com/([a-z]{2})/</loc>", sitemap))
if locs_in_sitemap != set(LOCALES):
    fail(f"sitemap.xml: locale coverage mismatch ({sorted(locs_in_sitemap)})")
for legal in ("privacy-policy.html", "terms-of-service.html"):
    if f"<loc>https://allyishere.com/{legal}</loc>" not in sitemap:
        fail(f"sitemap.xml: {legal} missing")

# ---- report -----------------------------------------------------------------------
print("QA FAILURES:", len(failures))
for f0 in failures:
    print("  FAIL:", f0)
print("QA WARNINGS:", len(warnings))
for w0 in warnings:
    print("  warn:", w0)
if not failures:
    print("RESULT: PASS")
sys.exit(1 if failures else 0)
