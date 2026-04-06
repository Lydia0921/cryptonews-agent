"""Remove unused files from an unpacked PPTX directory.

Cleans orphaned slides, media, and relationship files that are no longer
referenced by the presentation.

Usage:
    python clean.py <unpacked_dir> [--dry-run]

Examples:
    python clean.py unpacked/
    python clean.py unpacked/ --dry-run
"""

import argparse
import sys
from pathlib import Path

import defusedxml.minidom


def main():
    parser = argparse.ArgumentParser(
        description="Remove unused files from an unpacked PPTX directory."
    )
    parser.add_argument("unpacked_dir", help="Unpacked PPTX directory")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without deleting",
    )
    args = parser.parse_args()

    unpacked_dir = Path(args.unpacked_dir)
    if not unpacked_dir.exists():
        print(f"Error: {unpacked_dir} not found", file=sys.stderr)
        sys.exit(1)

    removed = clean_unused_files(unpacked_dir, dry_run=args.dry_run)
    action = "Would remove" if args.dry_run else "Removed"
    print(f"{action} {removed} file(s)")


def clean_unused_files(unpacked_dir: Path, dry_run: bool = False) -> int:
    removed = 0
    removed += remove_trash_directory(unpacked_dir, dry_run=dry_run)
    removed += remove_orphaned_slides(unpacked_dir, dry_run=dry_run)
    removed += remove_orphaned_rels_files(unpacked_dir, dry_run=dry_run)
    removed += remove_orphaned_files(unpacked_dir, dry_run=dry_run)
    if not dry_run:
        update_content_types(unpacked_dir)
    return removed


def remove_orphaned_slides(unpacked_dir: Path, dry_run: bool = False) -> int:
    pres_path = unpacked_dir / "ppt" / "presentation.xml"
    if not pres_path.exists():
        return 0

    pres_content = pres_path.read_text(encoding="utf-8")
    pres_dom = defusedxml.minidom.parseString(pres_content)

    referenced_slides = set()
    for sld_id in pres_dom.getElementsByTagName("p:sldId"):
        rid = sld_id.getAttribute("r:id")
        if rid:
            referenced_slides.add(rid)

    rels_path = unpacked_dir / "ppt" / "_rels" / "presentation.xml.rels"
    if not rels_path.exists():
        return 0

    rels_content = rels_path.read_text(encoding="utf-8")
    rels_dom = defusedxml.minidom.parseString(rels_content)

    referenced_targets = set()
    for rel in rels_dom.getElementsByTagName("Relationship"):
        rid = rel.getAttribute("Id")
        target = rel.getAttribute("Target")
        rel_type = rel.getAttribute("Type")
        if rid in referenced_slides and "slide" in rel_type:
            referenced_targets.add(target.replace("slides/", ""))

    slides_dir = unpacked_dir / "ppt" / "slides"
    removed = 0
    for slide_file in slides_dir.glob("slide*.xml"):
        if slide_file.name not in referenced_targets:
            print(f"  {'Would remove' if dry_run else 'Removing'}: {slide_file.relative_to(unpacked_dir)}")
            if not dry_run:
                slide_file.unlink()
                rels_file = slides_dir / "_rels" / f"{slide_file.name}.rels"
                if rels_file.exists():
                    rels_file.unlink()
            removed += 1

    return removed


def remove_trash_directory(unpacked_dir: Path, dry_run: bool = False) -> int:
    trash_dir = unpacked_dir / "__MACOSX"
    removed = 0
    if trash_dir.exists():
        files = list(trash_dir.rglob("*"))
        for f in files:
            if f.is_file():
                print(f"  {'Would remove' if dry_run else 'Removing'}: {f.relative_to(unpacked_dir)}")
                if not dry_run:
                    f.unlink()
                removed += 1
        if not dry_run:
            import shutil
            shutil.rmtree(trash_dir, ignore_errors=True)
    return removed


def get_slide_referenced_files(slide_rels_path: Path) -> set[str]:
    if not slide_rels_path.exists():
        return set()

    referenced = set()
    try:
        dom = defusedxml.minidom.parse(str(slide_rels_path))
        for rel in dom.getElementsByTagName("Relationship"):
            target = rel.getAttribute("Target")
            if target and not target.startswith("http"):
                referenced.add(target)
    except Exception:
        pass
    return referenced


def remove_orphaned_rels_files(unpacked_dir: Path, dry_run: bool = False) -> int:
    removed = 0
    for rels_file in unpacked_dir.rglob("*.rels"):
        parent_dir = rels_file.parent.parent
        base_name = rels_file.stem
        parent_file = parent_dir / base_name
        if not parent_file.exists():
            print(f"  {'Would remove' if dry_run else 'Removing'}: {rels_file.relative_to(unpacked_dir)}")
            if not dry_run:
                rels_file.unlink()
            removed += 1
    return removed


def get_referenced_files(unpacked_dir: Path) -> set[Path]:
    referenced = set()
    for rels_file in unpacked_dir.rglob("*.rels"):
        try:
            dom = defusedxml.minidom.parse(str(rels_file))
            for rel in dom.getElementsByTagName("Relationship"):
                target = rel.getAttribute("Target")
                if not target or target.startswith("http"):
                    continue
                base = rels_file.parent.parent
                resolved = (base / target).resolve()
                referenced.add(resolved)
        except Exception:
            pass
    return referenced


def remove_orphaned_files(unpacked_dir: Path, dry_run: bool = False) -> int:
    referenced = get_referenced_files(unpacked_dir)
    media_dir = unpacked_dir / "ppt" / "media"
    if not media_dir.exists():
        return 0

    removed = 0
    for media_file in media_dir.iterdir():
        if media_file.is_file() and media_file.resolve() not in referenced:
            print(f"  {'Would remove' if dry_run else 'Removing'}: {media_file.relative_to(unpacked_dir)}")
            if not dry_run:
                media_file.unlink()
            removed += 1
    return removed


def update_content_types(unpacked_dir: Path) -> None:
    content_types_path = unpacked_dir / "[Content_Types].xml"
    if not content_types_path.exists():
        return

    content_types = content_types_path.read_text(encoding="utf-8")
    dom = defusedxml.minidom.parseString(content_types)

    lines = []
    for override in dom.getElementsByTagName("Override"):
        part_name = override.getAttribute("PartName")
        if part_name.startswith("/ppt/slides/slide"):
            file_name = part_name.lstrip("/")
            file_path = unpacked_dir / file_name
            if not file_path.exists():
                continue
        lines.append(override)

    # Rewrite without orphaned overrides
    new_lines = content_types
    for override in dom.getElementsByTagName("Override"):
        part_name = override.getAttribute("PartName")
        if part_name.startswith("/ppt/slides/slide"):
            file_name = part_name.lstrip("/")
            file_path = unpacked_dir / file_name
            if not file_path.exists():
                tag = override.toxml()
                new_lines = new_lines.replace(tag, "").replace(tag + "\n", "")

    content_types_path.write_text(new_lines, encoding="utf-8")


if __name__ == "__main__":
    main()
