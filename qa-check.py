# qa-check.py — static QA for the allyishere site.
# 1) Verifies every internal href/src target exists on disk.
# 2) Verifies structural requirements on every page.
import os
import re
import sys

ROOT = r"C:\Users\excal\Ally-ALL\allyishere"
LOCALES = ["ar", "az", "de", "en", "es", "fr", "hi", "id", "it", "ja", "ko", "ku", "nl", "pt", "ru", "tr", "zh"]

failures = []
warnings = []

def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# ---- per-page structural checks -------------------------------------------
pages = ["index.html", "404.html", "privacy-policy.html", "terms-of-service.html"]
pages += [l + "/index.html" for l in LOCALES]

for rel in pages:
    path = os.path.join(ROOT, rel)
    html = read(path)
    name = rel

    if "</html>" not in html:
        failures.append(f"{name}: missing </html>")
    if "<title>" not in html and "document.title" not in html:
        failures.append(f"{name}: no title")
    if "main.css" not in html:
        failures.append(f"{name}: main.css not linked")
    if "skip-link" not in html and "404" not in name:
        failures.append(f"{name}: no skip-link")
    if 'id="main"' not in html and "404" not in name:
        failures.append(f"{name}: no main landmark")
    if "main.js" not in html and "404" not in name and "index.html" in rel and rel != "index.html":
        failures.append(f"{name}: main.js missing")
    # locale index pages: canonical + hreflang
    if rel.endswith("/index.html"):
        if 'rel="canonical"' not in html:
            failures.append(f"{name}: no canonical")
        if html.count('hreflang=') < 18:
            failures.append(f"{name}: hreflang incomplete ({html.count('hreflang=')})")
        if "<style>" in html:
            warnings.append(f"{name}: leftover inline <style>")
        if "autoplay" in html:
            warnings.append(f"{name}: leftover autoplay attr")
        if html.count('<main id="main">') != 1 or html.count("</main>") != 1:
            failures.append(f"{name}: main landmark mismatch")

# ---- internal asset/link existence ----------------------------------------
url_re = re.compile(r'(?:href|src)="(/[^"#?]+|assets/[^"#?]+|\.\./assets/[^"#?]+)"')

for rel in pages:
    path = os.path.join(ROOT, rel)
    html = read(path)
    base_dir = os.path.dirname(path)
    for m in url_re.finditer(html):
        target = m.group(1)
        if target.startswith("http"):
            continue
        if target.startswith("/"):
            fs = os.path.join(ROOT, target.lstrip("/"))
        else:
            fs = os.path.normpath(os.path.join(base_dir, target))
        if not os.path.exists(fs):
            failures.append(f"{rel}: broken internal ref {target}")

# ---- duplicate id check (basic) --------------------------------------------
for rel in pages:
    html = read(os.path.join(ROOT, rel))
    ids = re.findall(r'\bid="([^"]+)"', html)
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        failures.append(f"{rel}: duplicate ids {sorted(dupes)}")

print("PAGES CHECKED:", len(pages))
print("WARNINGS:", len(warnings))
for w in warnings:
    print("  warn:", w)
print("FAILURES:", len(failures))
for f in failures:
    print("  fail:", f)

sys.exit(1 if failures else 0)
