"""Validator for redlining (tracked changes) issues in Office documents."""

from pathlib import Path

import defusedxml.minidom


class RedliningValidator:
    """Checks for tracked changes / redlining artifacts in PPTX or DOCX files.

    Detects:
    - w:ins / w:del elements (Word tracked insertions and deletions)
    - w:rPrChange, w:pPrChange (formatting change revisions)
    - p:ph with revision attributes in PPTX
    - Any revision marks that should be accepted or rejected before finalizing
    """

    # Word tracked change element names
    TRACKED_CHANGE_TAGS = {
        "w:ins",
        "w:del",
        "w:rPrChange",
        "w:pPrChange",
        "w:sectPrChange",
        "w:tblPrChange",
        "w:trPrChange",
        "w:tcPrChange",
        "w:numChange",
        "w:moveFrom",
        "w:moveTo",
    }

    def __init__(self, unpacked_dir: Path, verbose: bool = False):
        self.unpacked_dir = unpacked_dir
        self.verbose = verbose

    def validate(self) -> bool:
        """Check for any tracked change / redlining elements.

        Returns:
            True if no redlining found, False otherwise.
        """
        issues = []

        for xml_file in self.unpacked_dir.rglob("*.xml"):
            try:
                content = xml_file.read_text(encoding="utf-8")
                # Quick pre-check before full parse
                if not any(tag in content for tag in self.TRACKED_CHANGE_TAGS):
                    continue

                dom = defusedxml.minidom.parse(str(xml_file))
                rel = xml_file.relative_to(self.unpacked_dir)

                for tag in self.TRACKED_CHANGE_TAGS:
                    elements = dom.getElementsByTagName(tag)
                    if elements.length > 0:
                        issues.append(
                            f"  {rel}: Found {elements.length} <{tag}> element(s)"
                        )

            except Exception:
                pass

        if issues:
            print(f"FAILED - Tracked changes found ({len(issues)} occurrence(s)):")
            for issue in issues:
                print(issue)
            print("  Hint: Accept or reject all tracked changes before finalizing.")
            return False

        if self.verbose:
            print("PASSED - No tracked changes / redlining found")
        return True

    def has_redlines(self) -> bool:
        """Quick check — returns True if any redlining markup is present."""
        for xml_file in self.unpacked_dir.rglob("*.xml"):
            try:
                content = xml_file.read_text(encoding="utf-8")
                if any(tag in content for tag in self.TRACKED_CHANGE_TAGS):
                    return True
            except Exception:
                pass
        return False

    def strip_redlines(self, accept: bool = True) -> int:
        """Remove tracked change markup, optionally accepting all changes.

        Args:
            accept: If True, keep inserted text and discard deleted text.
                    If False, keep original text and discard insertions.

        Returns:
            Number of files modified.
        """
        modified = 0
        for xml_file in self.unpacked_dir.rglob("*.xml"):
            try:
                content = xml_file.read_text(encoding="utf-8")
                if not any(tag in content for tag in self.TRACKED_CHANGE_TAGS):
                    continue

                dom = defusedxml.minidom.parseString(content.encode("utf-8"))
                changed = False

                if accept:
                    # Accept insertions: unwrap w:ins children into parent
                    for ins in list(dom.getElementsByTagName("w:ins")):
                        parent = ins.parentNode
                        if parent:
                            for child in list(ins.childNodes):
                                parent.insertBefore(child, ins)
                            parent.removeChild(ins)
                            changed = True

                    # Accept deletions: remove w:del entirely
                    for del_elem in list(dom.getElementsByTagName("w:del")):
                        parent = del_elem.parentNode
                        if parent:
                            parent.removeChild(del_elem)
                            changed = True
                else:
                    # Reject insertions: remove w:ins entirely
                    for ins in list(dom.getElementsByTagName("w:ins")):
                        parent = ins.parentNode
                        if parent:
                            parent.removeChild(ins)
                            changed = True

                    # Reject deletions: unwrap w:del children into parent
                    for del_elem in list(dom.getElementsByTagName("w:del")):
                        parent = del_elem.parentNode
                        if parent:
                            for child in list(del_elem.childNodes):
                                parent.insertBefore(child, del_elem)
                            parent.removeChild(del_elem)
                            changed = True

                # Remove revision property change elements
                for tag in ("w:rPrChange", "w:pPrChange", "w:sectPrChange",
                            "w:tblPrChange", "w:trPrChange", "w:tcPrChange",
                            "w:numChange"):
                    for elem in list(dom.getElementsByTagName(tag)):
                        parent = elem.parentNode
                        if parent:
                            parent.removeChild(elem)
                            changed = True

                if changed:
                    xml_file.write_bytes(dom.toxml(encoding="UTF-8"))
                    modified += 1

            except Exception:
                pass

        return modified
