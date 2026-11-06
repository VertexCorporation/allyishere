# tools/build_css.py — assemble src/css/*.css into main.css in fixed order.
import pathlib

root = pathlib.Path(__file__).resolve().parent.parent
parts = ["a-tokens.css", "b-scripts.css", "c-base.css", "d-header.css", "e-hero.css",
         "f-sections.css", "g-cards.css", "h-motion.css", "i-responsive.css"]
chunks = []
for name in parts:
    text = (root / "src" / "css" / name).read_text(encoding="utf-8")
    chunks.append(text.strip("\n"))
out = "\n".join(chunks) + "\n"
(root / "main.css").write_text(out, encoding="utf-8", newline="\n")

depth = 0
for ch in out:
    if ch == "{":
        depth += 1
    elif ch == "}":
        depth -= 1
print(f"main.css assembled: {len(out.splitlines())} lines, {len(out.encode('utf-8'))} bytes, brace depth {depth}")
if depth != 0:
    raise SystemExit("BRACE IMBALANCE")
