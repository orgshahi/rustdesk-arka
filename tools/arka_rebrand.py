#!/usr/bin/env python3
"""
ARKA re-runnable string rebrand (update-safe).

Replaces the product name token "RustDesk" -> "Arka" in the UI translation
files (src/lang/*.rs). Keys are lowercase_snake and URLs use lowercase
"rustdesk.com", so replacing the exact CamelCase token "RustDesk" only touches
user-facing product-name text, never keys or URLs.

Run this once, commit the result. After merging a newer RustDesk upstream, just
run it again to re-apply the rebrand to any new/changed strings:

    python tools/arka_rebrand.py

Note (AGPL-3.0): RustDesk is AGPL-licensed. Rebranding the UI name is allowed,
but you must keep this client's source available to its users and preserve the
LICENSE file and source copyright headers. This script deliberately touches only
UI strings, not LICENSE or copyright notices.
"""
import glob
import os
import sys

OLD = "RustDesk"
NEW = "Arka"

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO = os.environ.get("ARKA_REPO", REPO)


def main():
    lang_files = sorted(glob.glob(os.path.join(REPO, "src", "lang", "*.rs")))
    # AGENTS.md: never edit template.rs (the master key list). The UI text comes
    # from en.rs + the per-language files, so skipping template.rs does not affect
    # the visible rebrand.
    lang_files = [p for p in lang_files if os.path.basename(p) != "template.rs"]
    if not lang_files:
        print("No lang files found under src/lang/*.rs", file=sys.stderr)
        return 1
    total = 0
    changed_files = 0
    for path in lang_files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        count = content.count(OLD)
        if count:
            content = content.replace(OLD, NEW)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            total += count
            changed_files += 1
    print(f"Rebranded '{OLD}' -> '{NEW}': {total} replacements across "
          f"{changed_files}/{len(lang_files)} lang files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
