"""Re-number the references list in ``docs/Final_Report.md`` (gap W-01).

Behaviour:
  - Walks the body of the dissertation in order; collects every inline citation
    of the form ``[N]``, ``[LN]``, or ``[N1, N2, ...]``.
  - Reads the existing references list at the end of the file. Detects alias
    entries (lines like ``[L1] ... Same as entry [8] above``) and collapses
    each alias to its canonical numeric label.
  - Assigns each canonical reference a new sequential number 1..K in the
    order it first appears in the body.
  - Rewrites every inline citation to the new numbering, deduplicating within
    a multi-citation group (so ``[8, L1]`` becomes ``[N]``, not ``[N, N]``).
  - Emits a new references list in the new numerical order, with one entry
    per canonical reference; alias-only entries are dropped.

The script is idempotent: running it twice produces no further changes.

Run from the repo root::

    py -3 scripts/renumber_references.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
REPORT = _REPO / "docs" / "Final_Report.md"

REFS_HEADER = "\n# References\n"
CITE_RE = re.compile(r"\[((?:L?\d+)(?:\s*,\s*L?\d+)*)\]")
ENTRY_HEAD_RE = re.compile(r"^\[(L?\d+)\]")
ALIAS_RE = re.compile(
    r"(?:[Ss]ame as entry|[Ss]ee entry|CLAY entry, same as|UIED Authors\. Same as entry)\s*\[(L?\d+)\]"
)
# Code-block detection so that patterns like ``offset[0]`` inside fenced or
# inline code do not get rewritten as citations.
FENCED_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_RE = re.compile(r"`[^`\n]+`")


def code_ranges(text: str) -> list[tuple[int, int]]:
    """Return sorted (start, end) byte ranges of all code regions in ``text``."""
    ranges: list[tuple[int, int]] = []
    for r in FENCED_RE.finditer(text):
        ranges.append((r.start(), r.end()))
    for r in INLINE_RE.finditer(text):
        ranges.append((r.start(), r.end()))
    ranges.sort()
    return ranges


def in_code(pos: int, ranges: list[tuple[int, int]]) -> bool:
    for s, e in ranges:
        if pos < s:
            return False
        if s <= pos < e:
            return True
    return False


def parse_refs_block(refs_block: str) -> tuple[dict[str, str], dict[str, str], str]:
    """Return ``(entries, alias_to_canonical, header_lines)``.

    - ``entries[label]`` is the full entry text including the leading ``[label]``.
    - ``alias_to_canonical[label]`` is set when an entry is a pure alias.
    - ``header_lines`` is everything between ``# References`` and the first
      ``[N]`` entry (the prose paragraph that opens the section).
    """
    lines = refs_block.splitlines()
    # Skip the leading "" produced by the split delimiter.
    assert lines[0] == "" or lines[0] == "# References" or not lines[0].strip()
    # Find the first entry line.
    header_end = None
    for i, ln in enumerate(lines):
        if ENTRY_HEAD_RE.match(ln):
            header_end = i
            break
    if header_end is None:
        raise RuntimeError("References block contains no [N] entries.")
    header = "\n".join(lines[:header_end])

    entries: dict[str, str] = {}
    alias_to_canonical: dict[str, str] = {}
    current_label: str | None = None
    current_lines: list[str] = []
    for ln in lines[header_end:]:
        # Stop reading entries when we hit the closing horizontal rule of the
        # references section; anything after that belongs to a trailing prose
        # note, not to the previous entry's bibliographic record.
        if ln.strip() == "---":
            break
        m = ENTRY_HEAD_RE.match(ln)
        if m:
            if current_label is not None:
                entries[current_label] = "\n".join(current_lines).strip()
            current_label = m.group(1)
            current_lines = [ln]
        elif current_label is not None:
            current_lines.append(ln)
    if current_label is not None:
        entries[current_label] = "\n".join(current_lines).strip()

    for label, body_text in entries.items():
        m = ALIAS_RE.search(body_text)
        if m:
            alias_to_canonical[label] = m.group(1)

    return entries, alias_to_canonical, header


def collect_first_appearance(body: str,
                             alias_to_canonical: dict[str, str],
                             code: list[tuple[int, int]]) -> list[str]:
    """Walk the body and return canonical labels in order of first appearance.
    Citations that occur inside fenced or inline code regions are ignored."""
    seen: set[str] = set()
    order: list[str] = []
    for m in CITE_RE.finditer(body):
        if in_code(m.start(), code):
            continue
        for raw in [p.strip() for p in m.group(1).split(",")]:
            canonical = alias_to_canonical.get(raw, raw)
            if canonical not in seen:
                seen.add(canonical)
                order.append(canonical)
    return order


def rewrite_body(body: str,
                 alias_to_canonical: dict[str, str],
                 new_number: dict[str, int],
                 code: list[tuple[int, int]]) -> str:
    def _sub(m: re.Match[str]) -> str:
        if in_code(m.start(), code):
            return m.group(0)
        new_ns: list[int] = []
        for raw in [p.strip() for p in m.group(1).split(",")]:
            canonical = alias_to_canonical.get(raw, raw)
            n = new_number.get(canonical)
            if n is None:
                return f"[MISSING_REF:{m.group(0)}]"
            if n not in new_ns:
                new_ns.append(n)
        return "[" + ", ".join(str(n) for n in new_ns) + "]"

    return CITE_RE.sub(_sub, body)


def build_new_refs_block(entries: dict[str, str],
                         new_number: dict[str, int]) -> str:
    out_lines: list[str] = []
    out_lines.append("# References")
    out_lines.append("")
    out_lines.append(
        "The references below are numbered in the order they first appear in the "
        "dissertation. Aliases used in the working draft (L-prefixed entries that "
        "duplicated a numeric entry) have been collapsed; each cited source "
        "appears exactly once."
    )
    out_lines.append("")
    for canonical, n in sorted(new_number.items(), key=lambda kv: kv[1]):
        entry = entries.get(canonical)
        if entry is None:
            out_lines.append(f"[{n}] (Missing entry for canonical label "
                             f"'{canonical}'; please supply.)")
            out_lines.append("")
            continue
        body_text = re.sub(r"^\[L?\d+\]\s*", "", entry)
        out_lines.append(f"[{n}] {body_text}")
        out_lines.append("")
    out_lines.append("---")
    out_lines.append("")
    out_lines.append(
        "*End of Final_Report.md draft. Inline citations were renumbered "
        "automatically against this list (gap W-01); re-run "
        "`scripts/renumber_references.py` after future citation changes to "
        "regenerate.*"
    )
    return "\n".join(out_lines)


def main() -> int:
    if not REPORT.exists():
        print(f"[error] {REPORT} not found", file=sys.stderr)
        return 2
    text = REPORT.read_text(encoding="utf-8")
    if REFS_HEADER not in text:
        print("[error] '# References' section not found", file=sys.stderr)
        return 2
    body, refs_block = text.split(REFS_HEADER, 1)
    refs_block = "# References\n" + refs_block

    entries, alias_to_canonical, _header = parse_refs_block(refs_block)
    body_code = code_ranges(body)
    order = collect_first_appearance(body, alias_to_canonical, body_code)
    new_number = {canonical: i + 1 for i, canonical in enumerate(order)}

    new_body = rewrite_body(body, alias_to_canonical, new_number, body_code)
    new_refs = build_new_refs_block(entries, new_number)
    REPORT.write_text(new_body + "\n" + new_refs + "\n", encoding="utf-8")

    print(f"[done] canonical references in body : {len(new_number)}")
    print(f"[done] aliases collapsed             : {len(alias_to_canonical)}")
    print(f"[done] entries kept in new refs list : {len(new_number)}")
    print(f"[done] entries dropped (alias-only)  : "
          f"{len(entries) - len(new_number)}")
    n_in_body = sum(1 for _ in CITE_RE.finditer(body))
    n_after = sum(1 for _ in CITE_RE.finditer(new_body))
    print(f"[done] inline citation groups        : {n_in_body} -> {n_after}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
