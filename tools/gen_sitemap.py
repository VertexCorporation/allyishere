# tools/gen_sitemap.py — regenerate sitemap.xml from the canonical locale list.
import pathlib

root = pathlib.Path(__file__).resolve().parent.parent
LOCALES = ["ar", "az", "de", "en", "es", "fr", "hi", "id", "it", "ja", "ko", "ku", "nl", "pt", "ru", "tr", "zh"]
BASE = "https://allyishere.com"

lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    "",
    "  <!-- Localized landing pages -->",
]
for loc in LOCALES:
    priority = "1.0" if loc in ("en", "tr") else "0.85"
    lines += [
        "  <url>",
        f"    <loc>{BASE}/{loc}/</loc>",
        "    <changefreq>weekly</changefreq>",
        f"    <priority>{priority}</priority>",
        "  </url>",
    ]
lines += [
    "",
    "  <!-- Legal pages -->",
    "  <url>",
    f"    <loc>{BASE}/privacy-policy.html</loc>",
    "    <changefreq>yearly</changefreq>",
    "    <priority>0.5</priority>",
    "  </url>",
    "  <url>",
    f"    <loc>{BASE}/terms-of-service.html</loc>",
    "    <changefreq>yearly</changefreq>",
    "    <priority>0.3</priority>",
    "  </url>",
    "</urlset>",
]

(root / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("sitemap.xml written:", len(LOCALES) + 2, "urls")
