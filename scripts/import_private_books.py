#!/usr/bin/env python3
"""Import a user-provided PDF into encrypted owner-only BodyOS knowledge."""

import argparse
import hashlib
import os
from pathlib import Path

from bodyos_api.config import get_settings
from bodyos_api.crypto import FieldCipher
from bodyos_api.db import make_engine
from bodyos_api.knowledge import KnowledgeService
from pypdf import PdfReader
from sqlalchemy.orm import Session


def pdf_pages(path: Path) -> dict[int, str]:
    reader = PdfReader(path)
    return {
        page_number: text
        for page_number, page in enumerate(reader.pages, start=1)
        if (text := (page.extract_text() or "").strip())
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--author")
    parser.add_argument("--rights-status", default="user_provided_private_use_unverified")
    args = parser.parse_args()

    encoded_key = os.environ.get("BODYOS_ENCRYPTION_KEY", "")
    if not encoded_key:
        raise SystemExit("BODYOS_ENCRYPTION_KEY is required")
    settings = get_settings()
    with Session(make_engine(settings.database_url), expire_on_commit=False) as session:
        source = KnowledgeService(session, FieldCipher.from_base64(encoded_key)).import_pages(
            fitcrew_user_id=args.user_id,
            title=args.title,
            author=args.author,
            content_hash=sha256(args.pdf),
            rights_status=args.rights_status,
            pages=pdf_pages(args.pdf),
        )
    print(f"imported source_id={source.id} title={source.title!r}")


if __name__ == "__main__":
    main()
