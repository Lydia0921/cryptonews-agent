"""PPTX-specific schema validator."""

from pathlib import Path

from .base import BaseSchemaValidator


class PPTXSchemaValidator(BaseSchemaValidator):
    """Validates an unpacked PPTX directory.

    Checks:
    - Well-formed XML
    - Namespace declarations
    - Unique shape IDs within slides
    - File references from .rels files
    - Content_Types.xml presence
    - Relationship ID uniqueness per .rels file
    """

    # PPTX core namespace URIs
    REQUIRED_NAMESPACES = {
        "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }

    def __init__(self, unpacked_dir: Path, verbose: bool = False):
        super().__init__(unpacked_dir, verbose)
        self.slides_dir = unpacked_dir / "ppt" / "slides"
        self.xml_files = list(unpacked_dir.rglob("*.xml")) + list(
            unpacked_dir.rglob("*.rels")
        )

    def validate_unique_ids(self) -> bool:
        """Check for duplicate shape IDs (cNvPr id=) within each slide."""
        errors = []
        if not self.slides_dir.exists():
            if self.verbose:
                print("PASSED - No slides directory found (skipping unique ID check)")
            return True

        for slide_file in sorted(self.slides_dir.glob("slide*.xml")):
            try:
                import defusedxml.minidom
                dom = defusedxml.minidom.parse(str(slide_file))
                ids_seen = {}
                for elem in dom.getElementsByTagName("p:cNvPr"):
                    eid = elem.getAttribute("id")
                    if eid:
                        if eid in ids_seen:
                            rel = slide_file.relative_to(self.unpacked_dir)
                            errors.append(f"  {rel}: Duplicate cNvPr id={eid}")
                        else:
                            ids_seen[eid] = True
            except Exception:
                pass

        if errors:
            print(f"FAILED - Duplicate shape IDs found:")
            for error in errors:
                print(error)
            return False

        if self.verbose:
            print(f"PASSED - No duplicate shape IDs found")
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
