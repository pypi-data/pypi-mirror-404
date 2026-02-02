import json
from pathlib import Path
import logging
from .svg import convert_icon_from_svg

logger = logging.getLogger(__name__)


def bootstrap_vault_defaults(
    vault_path: Path,
    source_path: Path,
    target_path: Path,
) -> None:
    """
    Ensures target JSON contains all fields from source JSON.
    """

    source = json.loads(source_path.read_text(encoding="utf-8"))
    target = json.loads(target_path.read_text(encoding="utf-8"))

    leaflet_marker_icons = source["markerIcons"]
    leaflet_marker_icons.append(source["defaultMarker"])
    fa_folder_path = vault_path / target["faFolderPath"]

    icon_index = build_icon_index(fa_folder_path=fa_folder_path)

    logger.debug("Original Target Icons: %s", target["icons"])

    merged = merge_default_icons(leaflet_marker_icons, icon_index, target)

    logger.debug("Updated Target JSON: %s", merged)

    # merged = deep_merge_defaults(source, target)

    target_path.write_text(json.dumps(merged, indent=2), encoding="utf-8")


def merge_default_icons(
    default_icons: dict, icon_index: dict[str, Path], target: dict
) -> dict:
    """Copy missing fields from source → target."""
    target_icons = target["icons"]
    logger.debug("Default Icons: %s", default_icons)
    converted_icons = [
        icon
        for icon in (
            convert_icon_from_svg(
                icon=icon,
                target_icons=target_icons,
                icon_index=icon_index,
            )
            for icon in default_icons
        )
        if icon is not None
    ]

    target_icons.extend(converted_icons)
    logger.debug("Updated Icons: %s", converted_icons)
    return target


def build_icon_index(fa_folder_path: Path) -> dict[str, Path]:
    """
    Walk the folder and subfolders and build an index:
    iconKey -> full Path
    """
    index = {}
    for svg_file in fa_folder_path.rglob("*.svg"):
        key = svg_file.stem  # file name without .svg
        index[key] = svg_file
    return index
