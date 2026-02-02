from pathlib import Path
import re
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)


def convert_icon_from_svg(icon: dict, target_icons: list[dict], icon_index) -> dict:
    logger.debug("Source Object: %s", icon)
    icon_name = icon["iconName"]
    color = icon["color"]
    for target_icon in target_icons:
        if target_icon["key"].lower().strip() == icon_name.lower().strip():
            return

    base_size = icon.get("transform", {}).get("size", 6)
    size_px = base_size * 4

    logger.debug("Icon Details: %s", [icon_name, color, base_size, size_px])
    # logger.debug("Icon Index: %s", '\n'.join([f"{k}: {v}" for k, v in list(icon_index.items())[:10]]))
    svg_path = find_icon_path(icon_index, icon_name)
    if not svg_path:
        return
    logger.debug("%s icon found at path: %s", icon_name, svg_path)
    raw_svg = svg_path.read_text(encoding="utf-8")

    normalized_svg = normalize_svg(
        raw_svg,
        size=size_px,
        color=color,
    )

    return {
        "key": icon_name,
        "pathOrDataUrl": svg_to_data_url(normalized_svg),
        "size": size_px,
        "anchorX": size_px // 2,
        "anchorY": size_px // 2,
        "inCollections": True,
    }


def normalize_svg(
    svg: str,
    *,
    size: int,
    color: str,
) -> str:
    # remove existing width/height
    svg = re.sub(r'\s(width|height)="[^"]+"', "", svg)

    # inject width/height on <svg>
    svg = svg.replace("<svg", f'<svg width="{size}" height="{size}"', 1)

    # force fill color
    svg = re.sub(r'fill="[^"]+"', f'fill="{color}"', svg)

    # if no fill at all, inject into paths
    if 'fill="' not in svg:
        svg = svg.replace("<path", f'<path fill="{color}"', 1)

    return svg.strip()


def svg_to_data_url(svg: str) -> str:
    return "data:image/svg+xml;charset=UTF-8," + quote(svg, safe="")


def find_icon_path(icon_index: dict[str, Path], icon_key: str) -> Path:
    try:
        return icon_index[icon_key]
    except KeyError:
        logger.warning(f"SVG for iconKey '{icon_key}' not found in any branch")
        return
