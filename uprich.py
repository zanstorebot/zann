import ast
import glob
import os
import sys

APPLY = "--apply" in sys.argv

IMPORTS = """

# ===== RICH HELP (edit + tombol Back) =====
from pyrogram.enums import ButtonStyle as _ButtonStyle
from pyrogram.helpers import RichMessageBuilder as _RMB, ikb as _ikb
"""

TAIL = """    _blocks = (
{blocks}
    )
    _builder = _RMB()
    for _blk in _blocks:
        _builder.add(_blk)
    rich = _builder.build()
    button = _ikb(
        [[("Back", f"help_back({{prev_page_num}})",
           _ButtonStyle.DANGER, "5258330865674494479")]]
    )
    if message_id:
        return await {c}.edit_rich_message(
            {ch}, message_id, rich, reply_markup=button
        )
    return await {c}.send_rich_message({ch}, rich, reply_markup=button)
"""


def find_func(tree):
    for n in tree.body:
        if isinstance(n, ast.AsyncFunctionDef) and n.name == "__HELP_RICH__":
            return n
    return None


def is_send_rich_return(stmt):
    if not isinstance(stmt, ast.Return):
        return None
    v = stmt.value
    if not isinstance(v, ast.Await) or not isinstance(v.value, ast.Call):
        return None
    call = v.value
    if not (isinstance(call.func, ast.Name) and call.func.id == "send_rich"):
        return None
    if call.keywords or len(call.args) < 3:
        return None
    return call


def convert(path):
    src = open(path, encoding="utf8").read()
    tree = ast.parse(src)
    fn = find_func(tree)
    if fn is None:
        return None, "tidak ada __HELP_RICH__"
    names = [a.arg for a in fn.args.args]
    if "message_id" in names:
        return None, "sudah format baru"
    if (fn.decorator_list or fn.args.defaults or fn.args.kwonlyargs
            or fn.args.vararg or fn.args.kwarg or len(names) < 3
            or fn.col_offset != 0):
        return None, "signature tidak standar"
    call = is_send_rich_return(fn.body[-1])
    if call is None:
        return None, "pola return send_rich(...) tidak dikenali"
    c_name, ch_name = names[0], names[1]
    a0, a1 = call.args[0], call.args[1]
    if not (isinstance(a0, ast.Name) and a0.id == c_name
            and isinstance(a1, ast.Name) and a1.id == ch_name):
        return None, "argumen send_rich tidak standar"
    segs = []
    for a in call.args[2:]:
        seg = ast.get_source_segment(src, a)
        if seg is None:
            return None, "gagal membaca blok"
        segs.append("        " + seg.strip() + ",")
    lines = src.splitlines()
    last = fn.body[-1]
    pre = lines[fn.body[0].lineno - 1: last.lineno - 1]
    header = "async def __HELP_RICH__({}, message_id=None, prev_page_num=0):".format(
        ", ".join(names))
    tail = TAIL.format(blocks="\n".join(segs), c=c_name, ch=ch_name)
    new_func = "\n".join([header] + pre) + "\n" + tail.rstrip("\n")
    start, end = fn.lineno - 1, fn.end_lineno
    new_lines = lines[:start] + new_func.split("\n") + lines[end:]
    new_src = "\n".join(new_lines) + "\n"
    if "_RMB" not in src:
        new_src = new_src.rstrip() + "\n" + IMPORTS
    compile(new_src, path, "exec")
    return new_src, "ok"


done, skipped = [], []
for path in sorted(glob.glob("plugins/*.py")):
    name = os.path.basename(path)
    if name == "__init__.py":
        continue
    try:
        new_src, why = convert(path)
    except SyntaxError as e:
        skipped.append((name, "gagal compile: {}".format(e)))
        continue
    if new_src is None:
        skipped.append((name, why))
        continue
    if APPLY:
        open(path, "w", encoding="utf8").write(new_src)
    done.append(name)

print("MODE:", "APPLY" if APPLY else "DRY-RUN")
print("DIUBAH:", len(done))
for n in done:
    print("  ", n)
print("DILEWATI:", len(skipped))
for n, why in skipped:
    print("  ", n, "->", why)