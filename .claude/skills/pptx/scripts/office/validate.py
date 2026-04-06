"""Validate an unpacked PPTX or DOCX directory against Office Open XML schemas.

Runs structural, schema, and relationship validation checks.

Usage:
    python -m office.validate <unpacked_dir> [--verbose] [--repair]

Examples:
    python -m office.validate presentation_unpacked/
    python -m office.validate presentation_unpacked/ --verbose
    python -m office.validate presentation_unpacked/ --repair
"""

import argparse
import sys
from pathlib import Path

from office.validators import DOCXSchemaValidator, PPTXSchemaValidator, RedliningValidator


def main():
    parser = argparse.ArgumentParser(
        description="Validate an unpacked PPTX/DOCX directory."
    )
    parser.add_argument("unpacked_dir", help="Unpacked PPTX/DOCX directory to validate")
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output for passing checks",
    )
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Attempt to repair fixable issues (e.g. whitespace preservation)",
    )
    parser.add_argument(
        "--redlines",
        action="store_true",
        help="Also check for redlining/tracked-changes issues",
    )
    args = parser.parse_args()

    unpacked_dir = Path(args.unpacked_dir)
    if not unpacked_dir.exists():
        print(f"Error: {unpacked_dir} not found", file=sys.stderr)
        sys.exit(1)

    # Detect file type
    if (unpacked_dir / "ppt").exists():
        validator = PPTXSchemaValidator(unpacked_dir, verbose=args.verbose)
        file_type = "PPTX"
    elif (unpacked_dir / "word").exists():
        validator = DOCXSchemaValidator(unpacked_dir, verbose=args.verbose)
        file_type = "DOCX"
    else:
        print(f"Error: Cannot determine file type from directory structure", file=sys.stderr)
        sys.exit(1)

    print(f"Validating {file_type}: {unpacked_dir}")
    print()

    if args.repair:
        repairs = validator.repair()
        print(f"Repaired {repairs} issue(s)")
        print()

    passed = True

    print("--- Namespace validation ---")
    if not validator.validate_namespaces():
        passed = False

    print()
    print("--- Unique ID validation ---")
    if not validator.validate_unique_ids():
        passed = False

    print()
    print("--- File reference validation ---")
    if not validator.validate_file_references():
        passed = False

    print()
    print("--- Content types validation ---")
    if not validator.validate_content_types():
        passed = False

    print()
    print("--- Relationship ID validation ---")
    if not validator.validate_all_relationship_ids():
        passed = False

    print()
    print("--- XSD schema validation ---")
    if not validator.validate_xml():
        passed = False

    if args.redlines:
        print()
        print("--- Redlining validation ---")
        redline_validator = RedliningValidator(unpacked_dir, verbose=args.verbose)
        if not redline_validator.validate():
            passed = False

    print()
    if passed:
        print("All validation checks PASSED")
        sys.exit(0)
    else:
        print("One or more validation checks FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
