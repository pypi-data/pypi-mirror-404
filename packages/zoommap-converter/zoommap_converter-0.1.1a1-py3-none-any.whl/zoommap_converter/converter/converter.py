import logging
from obsidian_parser import Note
from pathlib import Path
from PIL import Image
import re
import uuid

from ..models.models import ParsedBlock, ZoommapBlock, ParsedNote, ZoommapConversion
from ..models.leaflet import (
    LeafletJsonData,
    LeafletShape,
    LeafletMarkerIcon,
    LeafletMapMarker,
)
from ..models.zoommap import (
    ZoommapJsonData,
    ZoommapMarker,
    ZoommapPolyShape,
    ZoommapImage,
    ZoommapMeasurement,
    ZoommapDrawShape,
    ZoommapShapeStyle,
    ZoommapLayer,
)
from .utils import decode_utf8_url_encoded, clean_image_name

logger = logging.getLogger(__name__)

DEFAULT_MARKER_TYPE = "pinRed"

METER_CONVERSION = {"m": 1, "km": 1000, "mi": 1609.34, "ft": 0.3048}


def convert_note(
    leaflet_note: ParsedNote,
    leaflet_data: LeafletJsonData,
    non_note_files: list,
    vault_path: Path,
):
    """Convert Leaflet blocks in Obsidian Note to Zoommap."""
    logger.debug("Executing Conversion Process for Leaflet to Zoommap...")
    leaflet_data = LeafletJsonData(**leaflet_data)
    leaflet_marker_icons = leaflet_data.markerIcons
    leaflet_marker_icons.append(leaflet_data.defaultMarker)
    return [
        convert_leaflet_to_zoommap(
            leaflet_block=leaflet_block,
            leaflet_data=leaflet_data,
            leaflet_marker_icons=leaflet_marker_icons,
            non_note_files=non_note_files,
            note=leaflet_note.note,
            vault_path=vault_path,
        )
        for leaflet_block in leaflet_note.leaflet_blocks
    ]


def convert_leaflet_to_zoommap(
    leaflet_block: ParsedBlock,
    leaflet_data: LeafletJsonData,
    leaflet_marker_icons: list[LeafletMarkerIcon],
    non_note_files: list,
    note: Note,
    vault_path: Path,
):
    """Processes Leaflet codeblock and converts it to an equivalent Zoommap block."""
    logger.debug("Converting Leaflet to Zoommap for Note: %s", note.name)

    # Handle Images
    images = []
    logger.debug("Converting Leaflet Block: %s", leaflet_block)
    image_wikilinks = leaflet_block.data.image
    logger.debug("Leaflet Image Wikilinks: %s", image_wikilinks)
    for image_link in image_wikilinks:
        image_name = re.sub(r"\[\[|\]\]", "", image_link)
        images.append(
            {
                "path": get_image_path(
                    file_list=non_note_files,
                    image_name=image_name,
                    vault_path=vault_path,
                ),
                "name": clean_image_name(image_name),
            }
        )

    # Image Size for base Layer
    size = None
    measurement_scales = {}
    meters_per_px = None
    try:
        for image in images:
            width, height = get_image_dimensions(image_path=vault_path / image["path"])
            if width is None or height is None:
                logger.error("Invalid image dimensions for %s", image["path"])
                raise ValueError(f"Invalid image dimensions for {image['path']}")
            
            if not size:
                size = {"w": width, "h": height}
                logger.debug("Image Size: %s", size)

                meters_per_px = convert_scale(
                    leaflet_block.data.scale, leaflet_block.data.unit
                )
                measurement_scales[image["path"]] = meters_per_px
            else:
                if size["w"] == 0 or size["h"] == 0:
                    logger.error("Invalid base image dimensions: %s", size)
                    raise ValueError("Invalid base image dimensions")
                measurement_scales[image["path"]] = meters_per_px * (size["w"] / width)
    except (ValueError, KeyError, TypeError) as e:
        logger.error(
            "Scale conversion failed for Map ID '%s': %s", leaflet_block.data.id, e
        )
        raise  # Re-raise to let caller handle the error

    if meters_per_px is None:
        logger.error("Meters per pixel not calculated for Map ID '%s'", leaflet_block.data.id)
        raise ValueError("Failed to calculate meters per pixel")

    measurement = ZoommapMeasurement(
        **{
            "scales": measurement_scales,
            "travelDaysEnabled": False,
            "displayUnit": leaflet_block.data.unit,
            "metersPerPixel": meters_per_px,
        }
    )

    # Handle Markers and Marker Layers
    # logger.debug(leaflet_data)
    leaflet_markers = next(
        (
            markers
            for markers in leaflet_data.mapMarkers
            if markers["id"] == leaflet_block.data.id
        ),
        None,
    )
    if not leaflet_markers:
        logger.info(
            "No markers found in %s for map id: %s", note.name, leaflet_block.data.id
        )
        # Initialize empty lists for markers and drawings
        zoommap_drawings = []
    else:
        logger.debug("Leaflet Markers: %s", leaflet_markers)
        leaflet_markers = LeafletMapMarker(**leaflet_markers)
    zoommap_markers, zoommap_layers = convert_markers(
        leaflet_markers, leaflet_marker_icons, size
    )
    # Handle Drawings
    if hasattr(leaflet_markers, "shapes") and leaflet_markers.shapes:
        logger.debug("Note '%s' has shapes: %s", note, leaflet_markers.shapes)
        drawing_layer = create_layer(layer_type="draw", name="Region Layer")
        zoommap_drawings = convert_drawings(
            leaflet_markers, layer_id=drawing_layer.id, size=size
        )
    else:
        drawing_layer = None
        zoommap_drawings = []
        logger.debug("No shapes found for map id: %s", leaflet_block.data.id)

    zoommap_block = process_leafblock(
        leaflet_block=leaflet_block,
        images=images,
        layers=[layer.name for layer in zoommap_layers],
    )

    zoommap_json = build_zoommap_json(
        zoommap_block=zoommap_block,
        markers=zoommap_markers,
        measurement=measurement,
        layers=zoommap_layers,
        drawing_layers=[drawing_layer],
        drawings=zoommap_drawings,
        size=size,
    )

    base_image_path = zoommap_block.imageBases[0]["path"]
    json_path = base_image_path.with_name(
        f"{base_image_path.name}_{zoommap_block.id}.markers.json"
    )

    zoommap_block.markers = json_path

    return ZoommapConversion(
        **{
            "note": note,
            "leaflet_block": leaflet_block,
            "zoommap_block": zoommap_block,
            "zoommap_json": zoommap_json,
            "marker_json_path": vault_path / json_path,
        }
    )


def build_zoommap_json(
    zoommap_block: ZoommapBlock,
    markers: list[ZoommapMarker],
    measurement: ZoommapMeasurement,
    layers: list[ZoommapLayer],
    drawing_layers: list[ZoommapLayer],
    drawings: list[ZoommapDrawShape],
    size: dict,
) -> ZoommapJsonData:
    """Builds the Zoommap JSON for the corresponding block."""
    logger.debug(
        "Building Zoommap JSON file for image: %s", zoommap_block.imageBases[0]
    )

    logger.debug("Zoommap Image Bases: %s", zoommap_block.imageBases)

    bases = [
        ZoommapImage(
            path=str(base["path"]) if isinstance(base["path"], Path) else base["path"],
            name=base["name"]
        )
        for base in zoommap_block.imageBases
    ]

    if not all(draw_layer is None for draw_layer in drawing_layers):
        logger.debug("Drawing Layers populated: %s", drawing_layers)
    else:
        logger.warning(
            "No drawing layers found for %s: %s", zoommap_block.id, drawing_layers
        )
        drawing_layers = []

    return ZoommapJsonData(
        size=size,
        layers=layers,
        markers=markers,
        bases=bases,
        overlays=[],  # TODO
        activeBase=bases[0].path,
        measurement=measurement,
        pinSizeOverrides={},
        panClamp=False,
        drawLayers=drawing_layers,
        drawings=drawings,
        textLayers=None,
    )


def process_leafblock(
    leaflet_block: ParsedBlock, layers: list, images: list
) -> ZoommapBlock:
    """Extracts incompatible elements from Leaflet codeblock to be Zoommap-compatible."""
    logger.debug(
        "Converting Leaflet to Zoommap Codeblock for block ID: %s",
        leaflet_block.data.id,
    )
    # Create a dictionary excluding the fields we don't want
    # Use model_dump() to get dictionary representation of the Pydantic model
    block_data = {
        k: v for k, v in leaflet_block.data.model_dump().items() 
        if k not in ["minZoom", "maxZoom", "image"]
    }
    logger.debug("Block Data: %s", block_data)
    logger.debug("Block Data Type: %s", type(block_data))
    image = images[0]

    return ZoommapBlock(
        imageBases=images,
        markerLayers=layers,
        imageOverlays=None,
        image=image["path"].as_posix(),
        **block_data,
    )


def get_image_path(file_list: list, image_name: str, vault_path: str | Path):
    """Fetches the full path for the image from the wikilink."""
    logger.debug("Fetching full path for image: %s", image_name)
    vault_path = Path(vault_path)
    try:
        if "/" in image_name:
            image_path = next(path for path in file_list if image_name in path.as_posix())
        else:
            image_path = next(
                path for path in file_list if image_name in path.as_posix().split("/")[-1]
            )
    except StopIteration:
        logger.error("Image not found: %s", image_name)
        raise FileNotFoundError(f"Image '{image_name}' not found in vault")

    # Convert to relative path
    try:
        relative_path = image_path.relative_to(vault_path)
        return relative_path
    except ValueError:
        # Fallback to absolute path if relative conversion fails
        logger.warning(f"Could not make path relative to vault: {image_path}")
        return image_path


def convert_zoom_level(zoom_level):
    """Converts min/max Zoom to be Zoommap-compatible."""
    pass


def get_image_dimensions(image_path: str | Path):
    """Quickly reads image metadata to get dimensions."""
    logger.debug("Reading image dimensions for path: %s", image_path)
    try:
        with Image.open(image_path) as img:
            return img.size
    except (FileNotFoundError, ValueError) as e:
        logger.error("Error getting image dimensions: %s", e)
        return None, None


def convert_scale(scale_value, scale_unit):
    """Converts Leaflet's units/px to Zoommap's meters/px."""
    logger.debug("Converting Scale")
    try:
        return scale_value * METER_CONVERSION[scale_unit]
    except KeyError as e:
        logger.error("Invalid scale unit '%s': %s", scale_unit, e)
        raise ValueError(f"Invalid scale unit: {scale_unit}") from e
    except TypeError as e:
        logger.error("Invalid scale value type: %s", e)
        raise ValueError(f"Invalid scale value: {scale_value}") from e


def convert_markers(
    leaflet_markers: LeafletMapMarker, marker_icons: list[LeafletMarkerIcon], size: dict
) -> list[ZoommapMarker]:
    """Converts Leaflet Markers to Zoommap format."""
    logger.debug("Converting Markers")
    new_markers = []
    new_layers = [create_layer(layer_type="layer", name="Default")]
    if leaflet_markers:
        for marker in leaflet_markers.markers:
            # Get the marker icon type
            marker_type = marker.type

            # Identify the marker_icon to match icon and colours
            logger.debug("Marker Icons: %s", marker_icons)
            logger.debug("Marker Type: %s", marker_type)
            marker_icon = next(
                (icon for icon in marker_icons if icon.type == marker_type), 
                None
            )
            if marker_icon is None:
                logger.warning(f"No marker icon found for type '{marker_type}', using default")
                marker_icon = LeafletMarkerIcon()  # Use default marker icon
            if marker_type == "default":
                marker_type = DEFAULT_MARKER_TYPE

            # Deduce the x/y coords
            # Leaflet goes from [0,0] at the bottom-left and coords in y,x (long, lat?) format
            # Zoommap has [0, 0] at the top-left
            y, x = marker.loc
            if size["w"] == 0 or size["h"] == 0:
                logger.error("Invalid size dimensions for marker conversion: %s", size)
                raise ValueError(f"Invalid size dimensions: {size}")
            x /= size["w"]
            y = (size["h"] - y) / size["h"]

            # Find existing layer or create new one
            layer_name = clean_image_name(decode_utf8_url_encoded(marker.layer))
            existing_layer = next(
                (layer for layer in new_layers if layer.name == layer_name), None
            )
            if existing_layer is None:
                new_layer = create_layer(layer_type="layer", name=layer_name)
                new_layers.append(new_layer)
                layer_id = new_layer.id
            else:
                layer_id = existing_layer.id

            new_markers.append(
                ZoommapMarker(
                    id=marker.id,
                    type="pin",
                    x=x,
                    y=y,
                    layer=layer_id,
                    link=marker.link,
                    iconKey=marker_type,
                    tooltip=marker.description,
                    minZoom=marker.minZoom,
                    maxZoom=marker.maxZoom,
                    iconColor=marker_icon.color,
                    scaleLikeSticker=False,
                )
            )

    return new_markers, new_layers


def convert_drawings(
    leaflet_shapes: LeafletMapMarker, layer_id: str, size
) -> list[ZoommapDrawShape]:
    """Convert shapes/drawings to be zoommap-compatible."""
    logger.debug("Converting Drawings")
    zoommap_shapes = []
    if leaflet_shapes:
        for shape_data in leaflet_shapes.shapes:
            shape = LeafletShape(**shape_data)
            shape_type = shape.type.lower().strip()

            # Generate ID and create base style
            shape_id = f"draw_{generate_uuid()}"
            style = ZoommapShapeStyle(
                strokeColor=shape.color,
                strokeWidth=2,
                fillColor=shape.color if shape_type != "polyline" else None,
                fillOpacity=0.15 if shape_type != "polyline" else None,
                fillPattern="solid" if shape_type != "polyline" else None,
            )
            # Initialize shape-specific data
            shape_specific_data = {
                "polygon": None,
                "polyline": None,
                "rect": None,
                "circle": None,
            }

            # Process based on shape type
            if shape_type == "rectangle":
                shape_type = "rect"
                if size["w"] == 0 or size["h"] == 0:
                    logger.error("Invalid size dimensions for rectangle conversion: %s", size)
                    raise ValueError(f"Invalid size dimensions for rectangle: {size}")
                coords = [
                    [(size["h"] - vertex.lat) / size["h"], vertex.lng / size["w"]]
                    for vertex in shape.vertices
                ]
                x_coords = sorted({sublist[1] for sublist in coords})
                y_coords = sorted({sublist[0] for sublist in coords})

                shape_specific_data["rect"] = {
                    "x0": x_coords[0],
                    "x1": x_coords[1],
                    "y0": y_coords[0],
                    "y1": y_coords[1],
                }

            elif shape_type == "polygon":
                if size["w"] == 0 or size["h"] == 0:
                    logger.error("Invalid size dimensions for polygon conversion: %s", size)
                    raise ValueError(f"Invalid size dimensions for polygon: {size}")
                shape_specific_data["polygon"] = [
                    ZoommapPolyShape(
                        y=(size["h"] - vertex.lat) / size["h"], x=vertex.lng / size["w"]
                    )
                    for vertex in shape.vertices
                ]

            elif shape_type == "polyline":
                style.arrowEnd = shape.arrows
                style.distanceLabel = False

                if size["w"] == 0 or size["h"] == 0:
                    logger.error("Invalid size dimensions for polyline conversion: %s", size)
                    raise ValueError(f"Invalid size dimensions for polyline: {size}")
                polyline_vertices = [
                    ZoommapPolyShape(
                        y=(size["h"] - vertex.lat) / size["h"], x=vertex.lng / size["w"]
                    )
                    for vertex in shape.vertices
                ]

                if shape.reversed:
                    polyline_vertices = polyline_vertices[::-1]

                shape_specific_data["polyline"] = polyline_vertices

            # There is no 'circle' shape implemented in Leaflet, so this block is redundant.
            # Will leave it here in unlikely case it is implemented in future.
            # elif shape_type == 'circle':
            #     center = shape.vertices[0]
            #     circle_data = {
            #         'cx': center['lng']/size['w'],
            #         'cy': center['lat']/size['h'],
            #         'r': center['rad']
            #     }

            zoommap_shapes.append(
                ZoommapDrawShape(
                    id=shape_id,
                    layerId=layer_id,
                    kind=shape_type,
                    visible=True,
                    style=style,
                    **shape_specific_data,
                )
            )

    return zoommap_shapes


def create_layer(
    id: str = None,
    name: str = "Region Layer",
    layer_type: str = "draw",
    bound_base: str = None,
    visible: bool = True,
    locked: bool = False,
) -> ZoommapLayer:
    """Generates a Zoommap layer object"""
    logger.debug("Creating Drawing Layer")
    return ZoommapLayer(
        id=id if id else layer_type + "_" + generate_uuid(),
        name=name,
        visible=visible,
        locked=locked,
        boundBase=bound_base,
    )


def generate_uuid() -> str:
    """Generate a UUID with the format 'draw_' + str(uuid)."""
    logger.debug("Creating UUID")
    return f"{uuid.uuid4().hex}"
