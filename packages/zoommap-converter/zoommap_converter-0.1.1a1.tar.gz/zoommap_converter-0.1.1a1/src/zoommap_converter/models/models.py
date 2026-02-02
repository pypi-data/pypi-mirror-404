import os
from obsidian_parser import Note
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, Any
from ..conf.settings import Settings
from .defaults import load_defaults

settings = Settings(settings_path=os.getenv("SETTINGS")).settings

VAULT_PATH = settings.get("vault_path", None)

############# PARSING OBJECTS #############


class LeafletYamlBlock(BaseModel):
    id: str
    image: list[str]
    bounds: list | None = None
    height: str | int | None = None
    width: str | int | None = None
    lat: str | float | None = None
    long: str | float | None = None
    minZoom: str | float | None = None
    maxZoom: str | float | None = None
    defaultZoom: str | float | None = None
    zoomDelta: str | float | None = None
    unit: str | None = None
    scale: str | float | None = None
    recenter: bool | None = None
    darkmode: bool | None = None

    @field_validator("image", mode="before")
    def parse_image_field(cls, v):
        if isinstance(v, str):
            return [v]
        return v


class ParsedBlock(BaseModel):
    data: LeafletYamlBlock
    in_callout: bool
    callout_depth: int
    raw_block: str


class ParsedNote(BaseModel):
    note: Note
    leaflet_blocks: list[ParsedBlock]

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ZoommapBlock(BaseModel):
    id: str
    imageBases: list[dict]
    minZoom: float = 0.25
    maxZoom: float = 3.0
    height: str = Field(
        default_factory=lambda: load_defaults(Path("zoom-map") / "data.json")[
            "defaultHeight"
        ]
    )  # Set the map viewport size. If the checkbox is enabled,
    width: str = Field(
        default_factory=lambda: load_defaults(Path("zoom-map") / "data.json")[
            "defaultWidth"
        ]
    )  # the value is stored in YAML and the map will always reopen in that size
    markerLayers: list = ["Default"]
    imageOverlays: Optional[list] = None
    render: str = "canvas"  # canvas | dom
    resizable: bool = Field(
        default_factory=lambda: load_defaults(Path("zoom-map") / "data.json")[
            "defaultResizable"
        ]
    )  # If enabled, you can resize the map window by dragging in the note.
    resizeHandle: str = Field(
        default_factory=lambda: load_defaults(Path("zoom-map") / "data.json")[
            "defaultResizeHandle"
        ]
    )  # Only appears if Resizable is enabled. Options are left, right, both, and native.
    responsive: bool = False  # Always sets width to 100% of the window and keeps the image aspect ratio.
    align: str = "center"  # Show the map left/right/center in the note.
    wrap: bool = False  # Allows text to wrap around map
    markers: str = None
    image: Optional[str] = None


class ZoommapConversion(BaseModel):
    note: Note
    leaflet_block: ParsedBlock
    zoommap_block: ZoommapBlock
    zoommap_json: Any
    marker_json_path: Any

    model_config = ConfigDict(arbitrary_types_allowed=True)


def find_all_extras(obj: Any, path=""):
    extras = {}
    if isinstance(obj, BaseModel):
        if obj.model_extra:
            extras[path or "<root>"] = obj.model_extra
        for field_name in obj.model_fields:
            value = getattr(obj, field_name)
            new_path = f"{path}.{field_name}" if path else field_name
            extras.update(find_all_extras(value, new_path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            extras.update(find_all_extras(item, f"{path}[{i}]"))
    return extras
