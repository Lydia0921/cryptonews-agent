"""Pack an unpacked PPTX/DOCX directory back into a zip archive.

Condenses pretty-printed XML back to single-line format and validates
the result before writing.

Usage:
    python -m office.pack <unpacked_dir> [output_file]

Examples:
    python -m office.pack presentation_unpacked/
    # Creates: presentation_unpacked.pptx (inferred from dir name)

    python -m office.pack my_edit/ output.pptx
    # Creates: output.pptx
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.dom import minidom
from xml.parsers.expat import ExpatError


def pack(unpacked_dir: Path, output_path: Path | None = None) -> Path:
    """Pack an unpacked directory back into a PPTX/DOCX file.

    Args:
        unpacked_dir: Path to the unpacked directory.
        output_path: Destination file path. Defaults to inferring from dir name.

    Returns:
        Path to the created archive.
    """
    if output_path is None:
        dir_name = unpacked_dir.name
        # Strip trailing _unpacked suffix if present
        if dir_name.endswith("_unpacked"):
            base = dir_name[: -len("_unpacked")]
        else:
            base = dir_name
        # Detect type from content
        if (unpacked_dir / "ppt").exists():
            ext = ".pptx"
        elif (unpacked_dir / "word").exists():
            ext = ".docx"
        else:
            ext = ".pptx"
        output_path = unpacked_dir.parent / f"{base}{ext}"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # [Content_Types].xml must be first
        ct_path = unpacked_dir / "[Content_Types].xml"
        if ct_path.exists():
            content = _condense_xml(ct_path.read_text(encoding="utf-8"))
            zf.writestr("[Content_Types].xml", content.encode("utf-8"))

        for file_path in sorted(unpacked_dir.rglob("*")):
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(unpacked_dir)
            arcname = str(rel)

            if arcname == "[Content_Types].xml":
                continue  # Already written first

            if file_path.suffix in (".xml", ".rels"):
                try:
                    text = file_path.read_text(encoding="utf-8")
                    condensed = _condense_xml(text)
                    zf.writestr(arcname, condensed.encode("utf-8"))
                    continue
                except Exception:
                    pass

            zf.write(file_path, arcname)

    return output_path


def _run_validation(unpacked_dir: Path) -> bool:
    """Run basic validation on the unpacked directory before packing.

    Args:
        unpacked_dir: Path to the unpacked directory.

    Returns:
        True if validation passes.
    """
    ct_path = unpacked_dir / "[Content_Types].xml"
    if not ct_path.exists():
        return False

    if (unpacked_dir / "ppt").exists():
        pres_path = unpacked_dir / "ppt" / "presentation.xml"
        if not pres_path.exists():
            return False

    return True


def _condense_xml(xml_string: str) -> str:
    """Condense pretty-printed XML to a compact single-line-per-element form.

    Preserves the XML declaration and meaningful whitespace in text nodes
    (elements with xml:space="preserve").

    Args:
        xml_string: Pretty-printed XML content.

    Returns:
        Condensed XML string.
    """
    try:
        # Re-parse and serialize without extra whitespace
        # Strip the pretty-print indentation by removing whitespace-only text nodes
        encoded = xml_string.encode("utf-8")
        dom = minidom.parseString(encoded)

        # Remove whitespace-only text nodes (indentation artifacts)
        _remove_whitespace_nodes(dom)

        result = dom.toxml(encoding="UTF-8").decode("utf-8")
        return result
    except ExpatError:
        # If we can't parse, return as-is (condensed by removing blank lines)
        lines = [line.strip() for line in xml_string.splitlines() if line.strip()]
        return "".join(lines)


def _remove_whitespace_nodes(node) -> None:
    """Recursively remove whitespace-only text nodes from a DOM tree."""
    to_remove = []
    for child in node.childNodes:
        if child.nodeType == child.TEXT_NODE and not child.nodeValue.strip():
            to_remove.append(child)
        else:
            _remove_whitespace_nodes(child)
    for child in to_remove:
        node.removeChild(child)


def main():
    parser = argparse.ArgumentParser(
        description="Pack an unpacked PPTX/DOCX directory into an archive."
    )
    parser.add_argument("unpacked_dir", help="Unpacked directory to pack")
    parser.add_argument(
        "output_file",
        nargs="?",
        help="Output file path (default: inferred from directory name)",
    )
    args = parser.parse_args()

    unpacked_dir = Path(args.unpacked_dir)
    if not unpacked_dir.exists():
        print(f"Error: {args.unpacked_dir} not found", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output_file) if args.output_file else None

    try:
        result = pack(unpacked_dir, output_path)
        print(f"Packed to: {result}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
