# Ally web — build pipeline

The multilingual site is **generated, not hand-maintained**. One template, one
content file per language, one design system:

```
src/template.html          single structural source for every locale
src/content/{loc}.json     localized copy (17 languages)
src/css/*.css              design system, assembled in order
tools/build.py             writes {loc}/index.html from template + content
tools/build_css.py         writes main.css from src/css/ (fixed order)
tools/gen_sitemap.py       writes sitemap.xml from the locale list
qa-check.py                static production QA (run after every change)
```

## Workflow

1. Edit copy in `src/content/{loc}.json` (every locale must keep the same key
   set; `en` is the reference and the deterministic fallback).
2. Edit structure/`<head>`/shared chrome in `src/template.html`.
3. Edit styles in `src/css/*.css` — never in `main.css` directly (it is generated).
4. Regenerate and verify:

```sh
python tools/build_css.py
python src/build.py
python tools/gen_sitemap.py   # only if the locale list changed
python qa-check.py
```

## Rules

- `/{loc}/index.html` files are **generated artifacts that are committed**;
  never edit them by hand (QA fails with "out of date" if they drift).
- Only localized copy and text direction (`dir`) may differ between locales —
  QA enforces identical DOM structure, section order and design tokens.
- Localized UI strings (including aria-labels) live in the content JSON files.
- Legal pages (`privacy-policy.html`, `terms-of-service.html`) are English
  source-of-truth documents and are hand-maintained, styled by the same system.
- `404.html` localizes a fixed message set client-side; the root `index.html`
  negotiates the language (stored choice, then browser languages) and
  redirects to `/{loc}/`.
