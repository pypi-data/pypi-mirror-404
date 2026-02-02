from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional
from .defaults import load_defaults


class ZoommapMeasurement(BaseModel):
    displayUnit: str  # Typically "mi", "ft", "m" or "km"
    scales: dict  # {mapPath: Scale}
    customUnitPxPerUnit: Optional[dict] = None
    travelTimePresetIds: Optional[list] = None
    travelDaysEnabled: Optional[bool] = None
    metersPerPixel: float  # Unclear what the difference is between this and scales?


class ZoommapLayer(BaseModel):
    id: str  # "layer_futa3d",
    name: str  # "DM Map",
    visible: bool = False
    locked: bool = False
    boundBase: Optional[str] = None


class ZoommapImage(BaseModel):
    path: str | Path
    name: str
    visible: Optional[bool] = None


class ZoommapMarker(BaseModel):
    type: str  # e.g "pin",
    id: str  # e.g "marker_kpmfya",
    x: float  # Coord e.g 0.2830597117355392,
    y: float  # e.g 0.7718351364034027,
    layer: str | None = (
        "default"  # Layer ID corresponds to ZoommapLayer id e.g "layer_4dw50q",
    )
    link: str | None = ""  # Link to a note,
    iconKey: str = Field(
        default_factory=lambda: load_defaults(Path("zoom-map") / "data.json")[
            "defaultIconKey"
        ]
    )  # e.g "pinRed",
    tooltip: str | None = ""  # Description e.g "Entrance to Hideout",
    scaleLikeSticker: bool | None = Field(
        default_factory=lambda: load_defaults(Path("zoom-map") / "data.json")[
            "defaultScaleLikeSticker"
        ]
    )  # e.g true
    maxZoom: float | None = None
    minZoom: float | None = None
    tooltipAlwaysOn: bool | None = None


class ZoommapPolyShape(BaseModel):
    x: float = None
    y: float = None


class ZoommapRectShape(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class ZoommapCircleShape(BaseModel):
    cx: float
    cy: float
    r: float


class ZoommapShapeStyle(BaseModel):
    strokeColor: str  # e.g. "#ff0000",
    strokeWidth: float  # e.g. 2,
    fillColor: Optional[str] = None  # e.g. "#ff0000",
    fillOpacity: Optional[float] = None  # e.g. 0.15,
    fillPattern: Optional[str] = None  # e.g. "solid",
    label: Optional[str] = None  # e.g. "Klarg is here"
    arrowEnd: Optional[bool] = None
    distanceLabel: Optional[bool] = None


class ZoommapDrawShape(BaseModel):
    id: str  # "draw_ucrbt6",
    layerId: str  # "draw_bt6opv",
    kind: str  # "polygon",
    visible: bool  # true,
    style: ZoommapShapeStyle
    polygon: Optional[list[ZoommapPolyShape]] = None
    polyline: Optional[list[ZoommapPolyShape]] = None
    rect: Optional[ZoommapRectShape] = None
    circle: Optional[ZoommapCircleShape] = None


class ZoommapTextLines(BaseModel):
    id: str
    x0: float
    y0: float
    x1: float
    y1: float
    text: str


class ZoommapTextStyle(BaseModel):
    fontFamily: str
    fontSize: float
    color: str
    fontWeight: str
    baselineOffset: float
    padLeft: float
    padRight: float


class ZoommapTextLayer(BaseModel):
    id: str
    name: str
    locked: bool
    showGuides: bool
    rect: ZoommapRectShape
    lines: list[ZoommapTextLines]
    allowAngledBaselines: bool
    style: ZoommapTextStyle


class ZoommapJsonData(BaseModel):
    size: dict[str, int]
    layers: list[ZoommapLayer]  # Seems to be marker layers?
    markers: list[ZoommapMarker] = None
    bases: list[ZoommapImage]
    overlays: list[ZoommapImage]
    activeBase: str | Path
    measurement: Optional[ZoommapMeasurement]
    pinSizeOverrides: dict
    panClamp: bool
    drawLayers: Optional[list[ZoommapLayer | None] | None] = None
    drawings: Optional[list[ZoommapDrawShape]] = None
    textLayers: Optional[list[ZoommapTextLayer]] = None
    image: Optional[str] = None
