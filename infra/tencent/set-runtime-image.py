#!/usr/bin/env python3
import argparse
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("value")
    parser.add_argument("--file", type=Path, default=Path("runtime/.env.runtime"))
    args = parser.parse_args()
    if not args.value or any(character.isspace() for character in args.value):
        raise SystemExit("invalid image tag")
    lines = args.file.read_text().splitlines()
    rendered = []
    found = False
    for line in lines:
        if line.startswith("FITCREW_IMAGE_TAG="):
            rendered.append(f"FITCREW_IMAGE_TAG={args.value}")
            found = True
        else:
            rendered.append(line)
    if not found:
        rendered.append(f"FITCREW_IMAGE_TAG={args.value}")
    temporary = args.file.with_suffix(".next")
    temporary.write_text("\n".join(rendered) + "\n")
    os.chmod(temporary, 0o600)
    temporary.replace(args.file)


if __name__ == "__main__":
    main()
