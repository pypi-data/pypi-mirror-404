import logging
import re
import yaml

from pathlib import Path

from ..models.models import ZoommapConversion, ZoommapBlock
from ..models.zoommap import ZoommapJsonData

logger = logging.getLogger(__name__)

FIELD_ORDER = [
    "render",
    "imageBases",
    "minZoom",
    "maxZoom",
    "height",
    "width",
    "resizable",
    "align",
    "wrap",
    "resizeHandle",
    "image",
    "markers",
    "markerLayers",
    "responsive",
    "id",
    "imageOverlays",
]


def yaml_equivalent_of_path(dumper, data):
    return dumper.represent_str(str(data))


yaml.SafeDumper.add_multi_representer(Path, yaml_equivalent_of_path)


def render_zoommap(data: ZoommapConversion):
    """Render the Zoommap Codeblock ```zoommap \nrender: canvas..., etc."""

    logger.debug("Zoommap Input Data: %s", data.zoommap_block)
    zoommap_codeblock = create_zoommap_block(data)

    logger.debug("Created Zoomap YAML: %s", zoommap_codeblock)

    # Create the JSON file
    logger.debug("Creating JSON File: %s", data.marker_json_path)
    Path(data.marker_json_path).write_text(
        create_zoommap_json(data.zoommap_json),
        encoding="utf-8",
    )

    data.leaflet_block.raw_block

    codeblock_replaced = replace_codeblock(
        path=data.note.path,
        leaflet_block=data.leaflet_block.raw_block,
        zoommap_block=zoommap_codeblock,
    )

    if not codeblock_replaced:
        logger.error(
            "Error encountered when replacing codeblock in Note: %s",
            data.note.path.as_posix(),
        )

    return codeblock_replaced


def zoommap_to_dict(block: ZoommapBlock) -> dict:
    """Convert Zoommap Pydantic object to a dict."""
    data = block.model_dump(exclude_none=True)
    logger.debug("Pydantic Model Dump Data: %s", data)

    # Ensure empty lists stay empty lists (YAML: [])
    for k, v in data.items():
        if isinstance(v, list) and not v:
            data[k] = []

    # Optional: reorder keys
    ordered = {}
    for key in FIELD_ORDER:
        if key in data:
            ordered[key] = data[key]
    logger.debug("Reordered Data: %s", ordered)

    # Include anything you forgot to order
    for k, v in data.items():
        if k not in ordered:
            ordered[k] = v

    return ordered


def dump_zoommap_yaml(data: dict) -> str:
    """Dumps Zoommap fields into yaml string."""
    yaml.add_multi_representer(Path, yaml_equivalent_of_path)

    return yaml.safe_dump(
        data, sort_keys=False, default_flow_style=False, indent=2, width=4096
    ).strip()


def create_zoommap_block(render_data: ZoommapConversion) -> str:
    """Creates Zoommap block with indentations."""
    logger.debug("Creating Zoommap block with indentation.")
    depth = render_data.leaflet_block.callout_depth
    prefix = ">" * depth + " " if depth else ""
    logger.debug("Callout Depth: %s", depth)

    block_dict = zoommap_to_dict(render_data.zoommap_block)
    logger.debug("Zoommap Dict: %s", block_dict)
    yaml_body = dump_zoommap_yaml(block_dict)
    logger.debug("Zoommap Yaml: %s", yaml_body)

    lines = [
        f"{prefix}```zoommap",
        *[f"{prefix}{line}" for line in yaml_body.splitlines()],
        f"{prefix}```",
    ]

    return "\n".join(lines)


def create_zoommap_json(data: ZoommapJsonData) -> str:
    """Dumps Zoommap object into JSON string."""
    logger.debug("Dumping into JSON string.")
    logger.debug("JSON Data: %s", data)
    return data.model_dump_json(
        indent=2,
        ensure_ascii=False,
        exclude_none=True,
        exclude_unset=True,
    )


# def dump_zoommap_json(data: dict) -> str:

#     return json.dumps(
#         data,
#         indent=2,
#         ensure_ascii=False,
#     )


def replace_codeblock(
    path: Path,
    leaflet_block: str,
    zoommap_block: str,
) -> None:
    """Replaces a specific codeblock in a Markdown file."""
    text = normalize(path.read_text(encoding="utf-8"))
    leaflet_block = normalize(leaflet_block)
    zoommap_block = normalize(zoommap_block)
    logger.debug("Raw Leaflet Block: %s", leaflet_block)

    pattern = re.compile(re.escape(leaflet_block))

    new_text, replacements = pattern.subn(zoommap_block, text, count=1)

    if replacements == 0:
        return False

    # if leaflet_block not in text:
    #     raise ValueError("Target codeblock not found in file")

    # new_text = text.replace(leaflet_block, zoommap_block, 1)

    path.write_text(new_text, encoding="utf-8")
    return True


def normalize(text: str) -> str:
    """Normalises text to remove rogue newlines from being replaced."""
    return text.replace("\r\n", "\n").strip()
