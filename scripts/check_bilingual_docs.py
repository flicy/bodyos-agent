#!/usr/bin/env python3
"""Require every Markdown document to be bilingual or have a paired translation."""

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]


def paired(path: Path) -> bool:
    if path.name.endswith("-zh.md"):
        return path.with_name(path.name.removesuffix("-zh.md") + "-en.md").is_file()
    if path.name.endswith("-en.md"):
        return path.with_name(path.name.removesuffix("-en.md") + "-zh.md").is_file()
    return False


def main() -> None:
    failures = []
    for path in sorted(ROOT.rglob("*.md")):
        if any(part in {".git", ".venv", ".build", ".pytest_cache"} for part in path.parts):
            continue
        if paired(path):
            continue
        content = path.read_text(encoding="utf-8")
        has_chinese = re.search(r"[\u3400-\u9fff]", content) is not None
        has_english = re.search(r"\b[A-Za-z]{4,}\b", content) is not None
        if not (has_chinese and has_english):
            failures.append(str(path.relative_to(ROOT)))
    if failures:
        raise SystemExit("Markdown lacks a Chinese/English pair: " + ", ".join(failures))
    print("All Markdown documents have Chinese and English coverage.")


if __name__ == "__main__":
    main()
