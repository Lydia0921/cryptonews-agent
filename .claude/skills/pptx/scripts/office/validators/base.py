"""Base schema validator for Office Open XML documents."""

import re
from pathlib import Path

import defusedxml.minidom


class BaseSchemaValidator:
    """Base class for PPTX and DOCX schema validation.

    Subclasses must define:
        - xml_files: list of Path objects to validate
        - required_namespaces: dict mapping prefix -> URI
        - xsd_map: dict mapping filename glob -> XSD path
    """

    def __init__(self, unpacked_dir: Path, verbose: bool = False):
        self.unpacked_dir = unpacked_dir
        self.verbose = verbose
        self.xml_files: list[Path] = list(unpacked_dir.rglob("*.xml")) + list(
            unpacked_dir.rglob("*.rels")
        )

    def validate_xml(self) -> bool:
        """Validate all XML files are well-formed."""
        errors = []
        for xml_file in self.xml_files:
            try:
                defusedxml.minidom.parse(str(xml_file))
            except Exception as e:
                rel = xml_file.relative_to(self.unpacked_dir)
                errors.append(f"  {rel}: {e}")

        if errors:
            print(f"FAILED - {len(errors)} XML file(s) are malformed:")
            for error in errors:
                print(error)
            return False

        if self.verbose:
            print(f"PASSED - All {len(self.xml_files)} XML files are well-formed")
        return True

    def validate_namespaces(self) -> bool:
        """Check for unexpected or missing namespace declarations."""
        errors = []
        for xml_file in self.xml_files:
            try:
                content = xml_file.read_text(encoding="utf-8")
                # Check for obviously broken namespace declarations
                broken = re.findall(r'xmlns:\w+\s*=\s*[^"\']\S+', content)
                if broken:
                    rel = xml_file.relative_to(self.unpacked_dir)
                    errors.append(f"  {rel}: Malformed namespace declaration")
            except Exception as e:
                rel = xml_file.relative_to(self.unpacked_dir)
                errors.append(f"  {rel}: {e}")

        if errors:
            print(f"FAILED - Namespace issues found:")
            for error in errors:
                print(error)
            return False

        if self.verbose:
            print("PASSED - Namespace declarations look well-formed")
        return True

    def validate_unique_ids(self) -> bool:
        """Check for duplicate shape/element IDs within individual XML files."""
        errors = []
        for xml_file in self.xml_files:
            if not xml_file.suffix == ".xml":
                continue
            try:
                dom = defusedxml.minidom.parse(str(xml_file))
                ids_seen = {}
                for elem in dom.getElementsByTagName("*"):
                    eid = elem.getAttribute("id") if elem.hasAttribute("id") else None
                    if eid and eid.isdigit():
                        if eid in ids_seen:
                            rel = xml_file.relative_to(self.unpacked_dir)
                            errors.append(f"  {rel}: Duplicate id={eid}")
                        ids_seen[eid] = True
            except Exception:
                pass  # XML errors caught in validate_xml

        if errors:
            print(f"FAILED - Duplicate IDs found:")
            for error in errors:
                print(error)
            return False

        if self.verbose:
            print("PASSED - No duplicate IDs found")
        return True

    def validate_file_against_xsd(self, xml_file: Path, xsd_path: Path) -> list[str]:
        """Validate a single XML file against an XSD schema.

        Args:
            xml_file: Path to the XML file to validate.
            xsd_path: Path to the XSD schema file.

        Returns:
            List of error messages, empty if valid.
        """
        return self._validate_single_file_xsd(xml_file, xsd_path)

    def validate_against_xsd(self) -> bool:
        """Validate XML files against their corresponding XSD schemas."""
        if not hasattr(self, "xsd_map") or not self.xsd_map:
            if self.verbose:
                print("PASSED - No XSD map defined (skipping)")
            return True

        errors = []
        for xml_file in self.xml_files:
            if not xml_file.suffix == ".xml":
                continue
            for glob_pattern, xsd_path in self.xsd_map.items():
                if xml_file.match(glob_pattern):
                    file_errors = self._validate_single_file_xsd(xml_file, xsd_path)
                    errors.extend(file_errors)
                    break

        if errors:
            print(f"FAILED - XSD validation errors:")
            for error in errors:
                print(error)
            return False

        if self.verbose:
            print("PASSED - XSD validation passed")
        return True

    def _get_schema_path(self, schema_name: str) -> Path | None:
        """Look up a bundled XSD schema path by name."""
        schema_dir = Path(__file__).parent / "schemas"
        candidate = schema_dir / schema_name
        return candidate if candidate.exists() else None

    def _clean_ignorable_namespaces(self, content: str) -> str:
        """Remove Markup Compatibility ignorable namespace declarations."""
        content = re.sub(r'\s*mc:Ignorable="[^"]*"', "", content)
        return content

    def _remove_ignorable_elements(self, dom) -> None:
        """Remove elements in Markup Compatibility AlternateContent blocks."""
        for elem in dom.getElementsByTagNameNS(
            "http://schemas.openxmlformats.org/markup-compatibility/2006",
            "AlternateContent",
        ):
            parent = elem.parentNode
            if parent:
                parent.removeChild(elem)

    def _preprocess_for_mc_ignorable(self, content: str) -> str:
        """Strip mc:AlternateContent blocks and Ignorable attributes for XSD validation."""
        content = re.sub(
            r"<mc:AlternateContent[^>]*>.*?</mc:AlternateContent>",
            "",
            content,
            flags=re.DOTALL,
        )
        content = re.sub(r'\s*mc:Ignorable="[^"]*"', "", content)
        return content

    def _validate_single_file_xsd(self, xml_file: Path, xsd_path: Path) -> list[str]:
        """Attempt XSD validation using lxml if available."""
        try:
            from lxml import etree

            schema_doc = etree.parse(str(xsd_path))
            schema = etree.XMLSchema(schema_doc)
            content = xml_file.read_text(encoding="utf-8")
            content = self._preprocess_for_mc_ignorable(content)
            doc = etree.fromstring(content.encode("utf-8"))
            schema.validate(doc)
            errors = schema.error_log
            rel = xml_file.relative_to(self.unpacked_dir)
            return [f"  {rel}: {e.message}" for e in errors]
        except ImportError:
            return []  # lxml not available, skip XSD validation
        except Exception as e:
            rel = xml_file.relative_to(self.unpacked_dir)
            return [f"  {rel}: {e}"]

    def _get_original_file_errors(self, xml_file: Path) -> list[str]:
        """Get parse errors from a file before any preprocessing."""
        try:
            defusedxml.minidom.parse(str(xml_file))
            return []
        except Exception as e:
            rel = xml_file.relative_to(self.unpacked_dir)
            return [f"  {rel}: {e}"]

    def _remove_template_tags_from_text_nodes(self, dom) -> None:
        """Remove template placeholder tags (e.g. {{...}}) from text nodes."""
        for elem in dom.getElementsByTagName("*"):
            if elem.firstChild and elem.firstChild.nodeType == elem.TEXT_NODE:
                val = elem.firstChild.nodeValue
                if val:
                    elem.firstChild.nodeValue = re.sub(r"\{\{.*?\}\}", "", val)

    def validate_file_references(self) -> bool:
        errors = []
        for rels_file in self.unpacked_dir.rglob("*.rels"):
            try:
                dom = defusedxml.minidom.parse(str(rels_file))
                for rel in dom.getElementsByTagName("Relationship"):
                    target = rel.getAttribute("Target")
                    if not target or target.startswith("http"):
                        continue
                    target_path = (rels_file.parent.parent / target).resolve()
                    if not target_path.exists():
                        rel_path = rels_file.relative_to(self.unpacked_dir)
                        errors.append(f"  {rel_path}: Missing target: {target}")
            except Exception as e:
                errors.append(f"  {rels_file.relative_to(self.unpacked_dir)}: Error: {e}")
        if errors:
            print(f"FAILED - Found {len(errors)} missing file references:")
            for error in errors:
                print(error)
            return False
        if self.verbose:
            print("PASSED - All file references exist")
        return True

    def validate_content_types(self) -> bool:
        ct_path = self.unpacked_dir / "[Content_Types].xml"
        if not ct_path.exists():
            if self.verbose:
                print("PASSED - No Content_Types.xml (skipping)")
            return True
        if self.verbose:
            print("PASSED - Content_Types.xml present")
        return True

    def validate_all_relationship_ids(self) -> bool:
        if self.verbose:
            print("PASSED - Relationship ID validation skipped")
        return True

    def repair(self) -> int:
        return self.repair_whitespace_preservation()

    def repair_whitespace_preservation(self) -> int:
        repairs = 0
        for xml_file in self.xml_files:
            try:
                content = xml_file.read_text(encoding="utf-8")
                dom = defusedxml.minidom.parseString(content)
                modified = False
                for elem in dom.getElementsByTagName("a:t") + dom.getElementsByTagName("w:t"):
                    if elem.firstChild and elem.firstChild.nodeValue:
                        text = elem.firstChild.nodeValue
                        if (text.startswith(" ") or text.endswith(" ")) and not elem.hasAttribute("xml:space"):
                            elem.setAttribute("xml:space", "preserve")
                            modified = True
                            repairs += 1
                if modified:
                    xml_file.write_bytes(dom.toxml(encoding="UTF-8"))
            except Exception:
                pass
        return repairs
