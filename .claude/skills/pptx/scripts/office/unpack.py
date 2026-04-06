"""Unpack a PPTX (or DOCX) file into a directory for editing.

Extracts the zip archive and pretty-prints all XML files for readability.

Usage:
    python -m office.unpack input.pptx [output_dir]
    python -m office.unpack input.docx [output_dir]

Examples:
    python -m office.unpack presentation.pptx
    # Unpacks to: presentation_unpacked/

    python -m office.unpack template.pptx my_edit/
    # Unpacks to: my_edit/
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.dom import minidom
from xml.parsers.expat import ExpatError


def unpack(input_path: Path, output_dir: Path | None = None) -> Path:
    """Unpack a PPTX/DOCX file into a directory with pretty-printed XML.

    Args:
        input_path: Path to the .pptx or .docx file.
        output_dir: Destination directory. Defaults to <stem>_unpacked/.

    Returns:
        Path to the unpacked directory.
    """
    if output_dir is None:
        output_dir = input_path.parent / f"{input_path.stem}_unpacked"

    output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(input_path, "r") as zf:
        for member in zf.infolist():
            target = output_dir / member.filename
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            data = zf.read(member.filename)

            if member.filename.endswith(".xml") or member.filename.endswith(".rels"):
                try:
                    text = data.decode("utf-8")
                    text = _escape_smart_quotes(text)
                    pretty = _pretty_print_xml(text)
                    target.write_text(pretty, encoding="utf-8")
                    continue
                except (UnicodeDecodeError, ExpatError):
                    pass  # Fall through to binary write

            target.write_bytes(data)

    return output_dir


def _pretty_print_xml(xml_string: str) -> str:
    """Pretty-print an XML string with consistent indentation.

    Args:
        xml_string: Raw XML content.

    Returns:
        Pretty-printed XML string.
    """
    try:
        dom = minidom.parseString(xml_string.encode("utf-8"))
        pretty = dom.toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")

        # Remove the extra blank lines that minidom adds
        lines = [line for line in pretty.splitlines() if line.strip()]
        return "\n".join(lines) + "\n"
    except ExpatError:
        return xml_string


def _escape_smart_quotes(text: str) -> str:
    """Replace smart/curly quotes with straight quotes in XML attribute values.

    Some Office files contain smart quotes inside XML attributes which causes
    parse errors. This replaces them with safe ASCII equivalents.

    Args:
        text: XML content possibly containing smart quotes.

    Returns:
        XML content with smart quotes replaced.
    """
    # Replace curly double quotes
    text = text.replace("\u201c", "&quot;").replace("\u201d", "&quot;")
    # Replace curly single quotes / apostrophes
    text = text.replace("\u2018", "&apos;").replace("\u2019", "&apos;")
    return text


def main():
    parser = argparse.ArgumentParser(
        description="Unpack a PPTX/DOCX file into a directory with pretty-printed XML."
    )
    parser.add_argument("input", help="Input file (.pptx or .docx)")
    parser.add_argument(
        "output_dir",
        nargs="?",
        help="Output directory (default: <stem>_unpacked/)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    if input_path.suffix.lower() not in (".pptx", ".docx"):
        print(f"Error: Expected .pptx or .docx, got: {input_path.suffix}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else None

    try:
        result = unpack(input_path, output_dir)
        print(f"Unpacked to: {result}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
