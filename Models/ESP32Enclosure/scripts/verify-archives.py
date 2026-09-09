#!/usr/bin/env python3
"""Verify preserved revision files without importing CAD or modifying archives.

Run this script from any directory. Paths in preserved-revisions.json are
relative to the enclosure package containing this script. New revisions that
are absent from that manifest are outside this check.
"""

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


def verify_archives(package_root):
    package_root = Path(package_root).resolve()
    manifest_path = package_root / "preserved-revisions.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not manifest:
        raise ValueError("Archive manifest must be a nonempty path-to-SHA256 mapping")

    archive_roots = set()
    for name, digest in manifest.items():
        path = PurePosixPath(name)
        if (path.is_absolute() or len(path.parts) < 3
                or path.parts[0] != "revisions" or ".." in path.parts
                or str(path) != name):
            raise ValueError(f"Invalid archive path in manifest: {name!r}")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"Invalid SHA256 in manifest for {name!r}")
        archive_roots.add(Path(*path.parts[:2]))

    problems = []
    checked = 0
    for name, expected in sorted(manifest.items()):
        file = package_root / name
        if not file.is_file():
            problems.append(f"Missing file: {name}")
            continue
        if file.is_symlink() or not file.resolve().is_relative_to(package_root):
            problems.append(f"Expected a package-local regular file: {name}")
            continue
        with file.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        checked += 1
        if actual != expected:
            problems.append(f"SHA256 mismatch: {name} (expected {expected}, got {actual})")

    actual_files = {
        file.relative_to(package_root).as_posix()
        for archive in archive_roots
        for file in (package_root / archive).rglob("*")
        if file.is_file() or file.is_symlink()
    }
    for name in sorted(actual_files - manifest.keys()):
        problems.append(f"Unexpected archive file: {name}")

    return checked, len(archive_roots), problems


def main():
    package_root = Path(__file__).resolve().parents[1]
    try:
        checked, revision_count, problems = verify_archives(package_root)
    except (OSError, ValueError, TypeError) as error:
        print(f"Archive verification failed: {error}", file=sys.stderr)
        return 1
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        print(f"Archive verification failed: {len(problems)} issue(s)", file=sys.stderr)
        return 1
    print(f"Verified {checked} preserved files across {revision_count} revision(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
