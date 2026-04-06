"""DOCX-specific schema validator."""

from pathlib import Path

from .base import BaseSchemaValidator


class DOCXSchemaValidator(BaseSchemaValidator):
    """Validates an unpacked DOCX directory.

    Checks:
    - Well-formed XML
    - Namespace declarations
    - Unique bookmark and ID attributes within document.xml
    - File references from .rels files
    - Content_Types.xml presence
    - Relationship ID uniqueness per .rels file
    """

    # DOCX core namespace URIs
    REQUIRED_NAMESPACES = {
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    }

    def __init__(self, unpacked_dir: Path, verbose: bool = False):
        super().__init__(unpacked_dir, verbose)
        self.word_dir = unpacked_dir / "word"
        self.xml_files = list(unpacked_dir.rglob("*.xml")) + list(
            unpacked_dir.rglob("*.rels")
        )

    def validate_unique_ids(self) -> bool:
        """Check for duplicate bookmark IDs and drawing IDs in document.xml."""
        import defusedxml.minidom

        errors = []
        doc_path = self.word_dir / "document.xml"
        if not doc_path.exists():
            if self.verbose:
                print("PASSED - No document.xml found (skipping unique ID check)")
            return True

        try:
            dom = defusedxml.minidom.parse(str(doc_path))
            rel = doc_path.relative_to(self.unpacked_dir)

            # Check bookmark IDs
            bookmark_ids = {}
            for elem in dom.getElementsByTagName("w:bookmarkStart"):
                bid = elem.getAttribute("w:id")
                if bid:
                    if bid in bookmark_ids:
                        errors.append(f"  {rel}: Duplicate bookmark w:id={bid}")
                    else:
                        bookmark_ids[bid] = True

            # Check drawing IDs
            drawing_ids = {}
            for elem in dom.getElementsByTagName("wp:docPr"):
                did = elem.getAttribute("id")
                if did:
                    if did in drawing_ids:
                        errors.append(f"  {rel}: Duplicate drawing id={did}")
                    else:
                        drawing_ids[did] = True

        except Exception as e:
            errors.append(f"  document.xml: {e}")

        if errors:
            print(f"FAILED - Duplicate IDs found:")
            for error in errors:
                print(error)
            return False

        if self.verbose:
            print("PASSED - No duplicate IDs found")
        return True

    def validate_all_relationship_ids(self) -> bool:
        """Check for duplicate rId values within each .rels file."""
        import defusedxml.minidom

        errors = []
        for rels_file in self.unpacked_dir.rglob("*.rels"):
            try:
                dom = defusedxml.minidom.parse(str(rels_file))
                rids = {}
                for rel in dom.getElementsByTagName("Relationship"):
                    rid = rel.getAttribute("Id")
                    if rid:
                        if rid in rids:
                            rel_path = rels_file.relative_to(self.unpacked_dir)
                            errors.append(f"  {rel_path}: Duplicate Id={rid}")
                        else:
                            rids[rid] = True
            except Exception:
                pass

        if errors:
            print(f"FAILED - Duplicate relationship IDs found:")
            for error in errors:
                print(error)
            return False

        if self.verbose:
            print("PASSED - All relationship IDs are unique")
        return True
