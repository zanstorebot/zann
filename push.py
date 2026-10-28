import pathlib
import re
import sys

APPLY = "--apply" in sys.argv
FOLDERS = ["plugins", "command", "assistant"]
NEW_IMPORT = "from helpers.emoprem import emo\n"

OLD = re.compile(r"^from helpers\.emo import emo\s*$", re.M)
USES = re.compile(r"\bemo\(")
HAS_IMPORT = re.compile(r"^from helpers(?:\.emoprem)? import .*\bemo\b", re.M)
OWN_EMO = re.compile(r"^\s*(?:def emo\b|emo\s*=)", re.M)

changed = 0
for folder in FOLDERS:
    for path in sorted(pathlib.Path(folder).rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        new = OLD.sub(NEW_IMPORT.rstrip("\n"), text)

        if (
            USES.search(new)
            and not HAS_IMPORT.search(new)
            and not OWN_EMO.search(new)
        ):
            lines = new.splitlines(keepends=True)
            for i, line in enumerate(lines):
                if line.startswith(("from ", "import ")):
                    lines.insert(i, NEW_IMPORT)
                    break
            else:
                lines.insert(0, NEW_IMPORT)
            new = "".join(lines)

        if new != text:
            print(f"{'UBAH' if APPLY else 'AKAN DIUBAH'}: {path}")
            if APPLY:
                path.write_text(new, encoding="utf-8")
            changed += 1

print(f"Total file: {changed}")