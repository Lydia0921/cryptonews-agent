"""Simplify or strip tracked changes (redlines) from Office XML files.

Provides utilities to accept, reject, or inspect tracked changes in
DOCX/PPTX documents. Can be used standalone or imported as a module.

Usage:
    python -m office.helpers.simplify_redlines <unpacked_dir> [--reject] [--dry-run]

Examples:
    python -m office.helpers.simplify_redlines document_unpacked/
    # Accepts all tracked changes (default)

    python -m office.helpers.simplify_redlines document_unpacked/ --reject
    # Rejects all tracked changes (restores original)

    python -m office.helpers.simplify_redlines document_unpacked/ --dry-run
    # Reports what would be changed without modifying files
"""

import argparse
import sys
from pathlib import Path
from xml.dom import minidom

import defusedxml.minidom


# Tags representing tracked change containers
TRACKED_INSERTION_TAGS = {"w:ins", "w:moveTo"}
TRACKED_DELETION_TAGS = {"w:del", "w:moveFrom"}
REVISION_PROPERTY_TAGS = {
    "w:rPrChange",
    "w:pPrChange",
    "w:sectPrChange",
    "w:tblPrChange",
    "w:trPrChange",
    "w:tcPrChange",
    "w:numChange",
}
ALL_REDLINE_TAGS = TRACKED_INSERTION_TAGS | TRACKED_DELETION_TAGS | REVISION_PROPERTY_TAGS


def simplify_redlines(
    unpacked_dir: Path,
    accept: bool = True,
    dry_run: bool = False,
) -> dict[str, int]:
    """Process tracked changes across all XML files in an unpacked directory.

    Args:
        unpacked_dir: Path to the unpacked PPTX/DOCX directory.
        accept: If True, accept all changes. If False, reject all changes.
        dry_run: If True, count changes but do not modify files.

    Returns:
        Dict with counts: {"files_modified": N, "insertions": N, "deletions": N, "property_changes": N}
    """
    stats = {"files_modified": 0, "insertions": 0, "deletions": 0, "property_changes": 0}

    for xml_file in sorted(unpacked_dir.rglob("*.xml")):
        try:
            content = xml_file.read_text(encoding="utf-8")
            if not _has_redlines(content):
                continue

            file_stats = _process_file(xml_file, content, accept=accept, dry_run=dry_run)
            if file_stats["total"] > 0:
                stats["files_modified"] += 1
                stats["insertions"] += file_stats["insertions"]
                stats["deletions"] += file_stats["deletions"]
                stats["property_changes"] += file_stats["property_changes"]

        except Exception:
            pass

    return stats


def _has_redlines(content: str) -> bool:
    """Quick string scan before full DOM parse."""
    return any(tag in content for tag in ALL_REDLINE_TAGS)


def _process_file(
    xml_file: Path,
    content: str,
    accept: bool,
    dry_run: bool,
) -> dict[str, int]:
    stats = {"insertions": 0, "deletions": 0, "property_changes": 0, "total": 0}

    dom = minidom.parseString(content.encode("utf-8"))

    if accept:
        stats["insertions"] += _unwrap_elements(dom, TRACKED_INSERTION_TAGS)
        stats["deletions"] += _remove_elements(dom, TRACKED_DELETION_TAGS)
    else:
        stats["insertions"] += _remove_elements(dom, TRACKED_INSERTION_TAGS)
        stats["deletions"] += _unwrap_elements(dom, TRACKED_DELETION_TAGS)

    stats["property_changes"] += _remove_elements(dom, REVISION_PROPERTY_TAGS)
    stats["total"] = stats["insertions"] + stats["deletions"] + stats["property_changes"]

    if stats["total"] > 0 and not dry_run:
        xml_file.write_bytes(dom.toxml(encoding="UTF-8"))

    return stats


def _unwrap_elements(dom, tags: set[str]) -> int:
    """Unwrap elements: move children into parent, remove the wrapper element.

    Used to accept insertions (keep content) or reject deletions (restore content).
    """
    count = 0
    for tag in tags:
        for elem in list(dom.getElementsByTagName(tag)):
            parent = elem.parentNode
            if parent is None:
                continue
            for child in list(elem.childNodes):
                parent.insertBefore(child, elem)
            parent.removeChild(elem)
            count += 1
    return count


def _remove_elements(dom, tags: set[str]) -> int:
    """Remove elements entirely (and all their children).

    Used to reject insertions (discard new content) or accept deletions (remove old content).
    """
    count = 0
    for tag in tags:
        for elem in list(dom.getElementsByTagName(tag)):
            parent = elem.parentNode
            if parent is not None:
                parent.removeChild(elem)
                count += 1
    return count


def get_redline_summary(unpacked_dir: Path) -> dict[str, list[str]]:
    """Return a summary of tracked changes found per file.

    Args:
        unpacked_dir: Path to the unpacked directory.

    Returns:
        Dict mapping relative file path -> list of tag counts found.
    """
    summary = {}

    for xml_file in sorted(unpacked_dir.rglob("*.xml")):
        try:
            content = xml_file.read_text(encoding="utf-8")
            if not _has_redlines(content):
                continue

            dom = defusedxml.minidom.parse(str(xml_file))
            file_issues = []

            for tag in sorted(ALL_REDLINE_TAGS):
                elements = dom.getElementsByTagName(tag)
                if elements.length > 0:
                    file_issues.append(f"{tag}: {elements.length}")

            if file_issues:
                rel = str(xml_file.relative_to(unpacked_dir))
                summary[rel] = file_issues

        except Exception:
            pass

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Simplify or strip tracked changes from an unpacked Office document."
    )
    parser.add_argument("unpacked_dir", help="Unpacked DOCX/PPTX directory")
    parser.add_argument(
        "--reject",
        action="store_true",
        help="Reject all changes instead of accepting them",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report changes without modifying files",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show a summary of tracked changes found without modifying",
    )
    args = parser.parse_args()

    unpacked_dir = Path(args.unpacked_dir)
    if not unpacked_dir.exists():
        print(f"Error: {unpacked_dir} not found", file=sys.stderr)
        sys.exit(1)

    if args.summary:
        summary = get_redline_summary(unpacked_dir)
        if not summary:
            print("No tracked changes found.")
        else:
            print(f"Tracked changes found in {len(summary)} file(s):")
            for path, issues in summary.items():
                print(f"  {path}:")
                for issue in issues:
                    print(f"    {issue}")
        return

    accept = not args.reject
    action = "Accepting" if accept else "Rejecting"
    mode = " (dry run)" if args.dry_run else ""
    print(f"{action} all tracked changes{mode}...")

    stats = simplify_redlines(unpacked_dir, accept=accept, dry_run=args.dry_run)

    print(f"Files modified:    {stats['files_modified']}")
    print(f"Insertions:        {stats['insertions']}")
    print(f"Deletions:         {stats['deletions']}")
    print(f"Property changes:  {stats['property_changes']}")


if __name__ == "__main__":
    main()
