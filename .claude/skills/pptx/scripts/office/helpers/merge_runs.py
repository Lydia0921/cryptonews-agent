"""Merge adjacent text runs with identical formatting in Office XML.

Adjacent runs (w:r in DOCX, a:r in PPTX) that share the same run properties
can be merged into a single run. This reduces XML verbosity and can fix
issues caused by over-fragmented runs from copy-paste or programmatic editing.

Usage:
    python -m office.helpers.merge_runs <unpacked_dir>

Examples:
    python -m office.helpers.merge_runs presentation_unpacked/
"""

import argparse
import sys
from pathlib import Path

import defusedxml.minidom
from xml.dom import minidom as std_minidom


def merge_runs(unpacked_dir: Path) -> int:
    """Merge adjacent runs with identical formatting in all XML files.

    Args:
        unpacked_dir: Path to the unpacked PPTX/DOCX directory.

    Returns:
        Total number of runs merged across all files.
    """
    total_merged = 0

    # Detect file type
    if (unpacked_dir / "ppt").exists():
        run_tag = "a:r"
        rpr_tag = "a:rPr"
        text_tag = "a:t"
        para_tag = "a:p"
    else:
        run_tag = "w:r"
        rpr_tag = "w:rPr"
        text_tag = "w:t"
        para_tag = "w:p"

    for xml_file in sorted(unpacked_dir.rglob("*.xml")):
        try:
            content = xml_file.read_text(encoding="utf-8")
            if run_tag not in content:
                continue

            dom = std_minidom.parseString(content.encode("utf-8"))
            merged = _merge_runs_in_dom(dom, run_tag, rpr_tag, text_tag, para_tag)

            if merged > 0:
                xml_file.write_bytes(dom.toxml(encoding="UTF-8"))
                total_merged += merged

        except Exception:
            pass

    return total_merged


def _merge_runs_in_dom(dom, run_tag: str, rpr_tag: str, text_tag: str, para_tag: str) -> int:
    """Merge adjacent runs with identical properties within each paragraph."""
    total = 0

    for para in dom.getElementsByTagName(para_tag):
        runs = [
            child for child in para.childNodes
            if child.nodeType == child.ELEMENT_NODE and child.tagName == run_tag
        ]

        i = 0
        while i < len(runs) - 1:
            current = runs[i]
            next_run = runs[i + 1]

            # Check they are actually adjacent in the paragraph
            if not _are_adjacent(current, next_run):
                i += 1
                continue

            current_rpr = _get_child(current, rpr_tag)
            next_rpr = _get_child(next_run, rpr_tag)

            if _rpr_equal(current_rpr, next_rpr):
                # Merge: append text from next_run into current
                current_text_elem = _get_child(current, text_tag)
                next_text_elem = _get_child(next_run, text_tag)

                if current_text_elem is not None and next_text_elem is not None:
                    current_val = current_text_elem.firstChild.nodeValue if current_text_elem.firstChild else ""
                    next_val = next_text_elem.firstChild.nodeValue if next_text_elem.firstChild else ""
                    merged_text = current_val + next_val

                    if current_text_elem.firstChild:
                        current_text_elem.firstChild.nodeValue = merged_text
                    else:
                        text_node = dom.createTextNode(merged_text)
                        current_text_elem.appendChild(text_node)

                    # Preserve xml:space if either had it
                    if (merged_text.startswith(" ") or merged_text.endswith(" ")):
                        current_text_elem.setAttribute("xml:space", "preserve")

                    para.removeChild(next_run)
                    runs.pop(i + 1)
                    total += 1
                    continue  # Don't increment i, try merging again at same position

            i += 1

    return total


def _find_elements(parent, tag: str) -> list:
    """Return direct child elements with the given tag."""
    return [
        child for child in parent.childNodes
        if child.nodeType == child.ELEMENT_NODE and child.tagName == tag
    ]


def _get_child(parent, tag: str):
    """Return the first direct child element with the given tag, or None."""
    for child in parent.childNodes:
        if child.nodeType == child.ELEMENT_NODE and child.tagName == tag:
            return child
    return None


def _are_adjacent(node_a, node_b) -> bool:
    """Check if node_b immediately follows node_a in the parent's children."""
    sibling = node_a.nextSibling
    while sibling is not None:
        if sibling.nodeType == sibling.ELEMENT_NODE:
            return sibling is node_b
        sibling = sibling.nextSibling
    return False


def _rpr_equal(rpr_a, rpr_b) -> bool:
    """Compare two run property elements for equality.

    Both None counts as equal (no formatting on either run).
    """
    if rpr_a is None and rpr_b is None:
        return True
    if rpr_a is None or rpr_b is None:
        return False
    return _xml_equal(rpr_a, rpr_b)


def _xml_equal(node_a, node_b) -> bool:
    """Recursively compare two DOM nodes for structural equality."""
    if node_a.nodeType != node_b.nodeType:
        return False
    if node_a.nodeType == node_a.ELEMENT_NODE:
        if node_a.tagName != node_b.tagName:
            return False
        # Compare attributes
        attrs_a = {node_a.attributes.item(i).name: node_a.attributes.item(i).value
                   for i in range(node_a.attributes.length)}
        attrs_b = {node_b.attributes.item(i).name: node_b.attributes.item(i).value
                   for i in range(node_b.attributes.length)}
        if attrs_a != attrs_b:
            return False
        # Compare children
        children_a = [c for c in node_a.childNodes if c.nodeType == c.ELEMENT_NODE]
        children_b = [c for c in node_b.childNodes if c.nodeType == c.ELEMENT_NODE]
        if len(children_a) != len(children_b):
            return False
        return all(_xml_equal(ca, cb) for ca, cb in zip(children_a, children_b))
    elif node_a.nodeType == node_a.TEXT_NODE:
        return node_a.nodeValue == node_b.nodeValue
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Merge adjacent runs with identical formatting."
    )
    parser.add_argument("unpacked_dir", help="Unpacked PPTX/DOCX directory")
    args = parser.parse_args()

    unpacked_dir = Path(args.unpacked_dir)
    if not unpacked_dir.exists():
        print(f"Error: {unpacked_dir} not found", file=sys.stderr)
        sys.exit(1)

    merged = merge_runs(unpacked_dir)
    print(f"Merged {merged} run(s)")


if __name__ == "__main__":
    main()
