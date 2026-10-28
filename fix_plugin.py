import pathlib
import re
import sys

APPLY = "--apply" in sys.argv
ONLY = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--only=")), None)

FOOTER = re.compile(
    r'table\(\s*\[\[\s*cell\(\s*"AliceDevs Core v3\.14[^"]*"\s*,\s*'
    r'align\s*=\s*"center"\s*,\s*is_header\s*=\s*True\s*\)\s*\]\]\s*,?\s*\)'
)
HEADER = re.compile(
    r'cell\(\s*f"[^"\n]*CMD/PREFIXES: \{prefix\}"\s*,\s*'
    r'align\s*=\s*"center"\s*,\s*is_header\s*=\s*True\s*\)'
)
HEADER_NEW = (
    'cell([emo(5262970276462745484, "💎"), '
    'RichTextBold(f" CMD/PREFIXES: {prefix}")], '
    'align="center", is_header=True)'
)

IMPORTS = {
    "footer": "from helpers.rich_footer import footer_table\n",
    "emo": "from helpers.emoprem import emo\n",
    "bold": "from pyrogram.types import RichTextBold\n",
}

changed = 0
for path in sorted(pathlib.Path("plugins").glob("*.py")):
    if ONLY and path.name != ONLY:
        continue
    text = path.read_text(encoding="utf-8")
    new, n_footer = FOOTER.subn("footer_table()", text)
    new, n_header = HEADER.subn(lambda m: HEADER_NEW, new)
    if n_footer == 0 and n_header == 0:
        continue

    need = []
    if n_footer:
        need.append("footer")
    if n_header:
        need += ["emo", "bold"]
    add = [IMPORTS[k] for k in need if IMPORTS[k] not in new]
    if add:
        lines = new.splitlines(keepends=True)
        pos = next(
            (i for i, l in enumerate(lines) if l.startswith(("from ", "import "))), 0
        )
        lines[pos:pos] = add
        new = "".join(lines)

    print(f"{'UBAH' if APPLY else 'AKAN DIUBAH'}: {path.name} (footer {n_footer}, header {n_header})")
    if APPLY:
        path.write_text(new, encoding="utf-8")
    changed += 1

print(f"Total file: {changed}")