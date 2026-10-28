"""Compare t('key') usages in the frontend with keys defined in locale files."""
import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "frontend" / "src"
LOCALES = SRC / "i18n" / "locales"


def parse_locale(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    keys: set[str] = set()
    stack: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.split("//")[0]
        stripped = line.strip()
        if not stripped:
            continue
        key_match = re.match(r"([A-Za-z0-9_]+)\s*:\s*(\{?)", stripped)
        # handle closing braces of nested objects
        if stripped.startswith("}"):
            if stack:
                stack.pop()
            continue
        if not key_match:
            continue
        key, brace = key_match.group(1), key_match.group(2)
        if brace:
            stack.append(key)
        else:
            keys.add(".".join(stack + [key]))
    return keys


locale_keys = {p.stem: parse_locale(p) for p in LOCALES.glob("*.ts")}

used: dict[str, set[str]] = {}
for py in list(SRC.rglob("*.jsx")) + list(SRC.rglob("*.tsx")):
    text = py.read_text(encoding="utf-8")
    for match in re.finditer(r"\bt\(\s*['\"]([A-Za-z0-9_.]+)['\"]", text):
        used.setdefault(match.group(1), set()).add(py.name)

base = locale_keys.get("tr", set())
missing_tr = sorted(k for k in used if k not in base)
print(f"used keys: {len(used)}  tr keys: {len(base)}")
print(f"missing in tr ({len(missing_tr)}):")
for k in missing_tr:
    print(f"  {k}   <- {sorted(used[k])}")

for lang, keys in sorted(locale_keys.items()):
    if lang == "tr":
        continue
    missing = sorted(k for k in used if k not in keys)
    print(f"missing in {lang}: {len(missing)}  e.g. {missing[:8]}")

unused = sorted(k for k in base if k not in used)
print(f"\ndefined but unused in tr: {len(unused)}")
print(", ".join(unused[:60]))
