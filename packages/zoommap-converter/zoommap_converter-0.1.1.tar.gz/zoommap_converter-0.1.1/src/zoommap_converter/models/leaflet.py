import os
from pydantic import BaseModel, ConfigDict, Field
from pathlib import Path
from typing import Any

from ..conf.settings import Settings
from .defaults import load_defaults

settings = Settings(settings_path=os.getenv("SETTINGS")).settings

VAULT_PATH = settings.get("vault_path", None)


class LeafletMarker(BaseModel):
    id: str
    type: str
    loc: list[float]
    link: str | None = None
    layer: str
    mutable: bool | None = None
    command: bool | None = None
    percent: Any | None = None
    description: str | None = None
    minZoom: Any | None = None
    maxZoom: Any | None = None
    tooltip: str | None = None

    model_config = ConfigDict(extra="allow")


class LeafletMarkerIcon(BaseModel):
    type: str = Field(
        default_factory=lambda: load_defaults(
            Path("obsidian-leaflet-plugin") / "data.json"
        )["defaultMarker"]["type"]
    )
    iconName: str = Field(
        default_factory=lambda: load_defaults(
            Path("obsidian-leaflet-plugin") / "data.json"
        )["defaultMarker"]["iconName"]
    )
    color: str = Field(
        default_factory=lambda: load_defaults(
            Path("obsidian-leaflet-plugin") / "data.json"
        )["defaultMarker"]["color"]
    )
    alpha: int = None
    layer: bool = None
    transform: dict = Field(
        default_factory=lambda: load_defaults(
            Path("obsidian-leaflet-plugin") / "data.json"
        )["defaultMarker"]["transform"]
    )
    isImage: bool = None
    tags: list = None
    minZoom: float | None = None
    maxZoom: float | None = None

    model_config = ConfigDict(extra="allow")


class LeafletVertex(BaseModel):
    lat: float
    lng: float
    id: str
    targets: dict

    model_config = ConfigDict(extra="allow")


class LeafletShape(BaseModel):
    type: str
    color: str
    vertices: list[LeafletVertex]
    arrows: bool = None
    reversed: bool = None

    model_config = ConfigDict(extra="allow")


class LeafletJsonData(BaseModel):
    mapMarkers: list
    defaultMarker: LeafletMarkerIcon
    markerIcons: list[LeafletMarkerIcon]
    defaultUnitType: str
    defaultTile: str
    defaultTileDark: str
    defaultAttribution: str
    defaultTileSubdomains: str
    color: str = "#dddddd"
    lat: float = 39.983334
    long: float = -82.98333
    notePreview: bool = False
    layerMarkers: bool = True
    previousVersion: str = "6.0.5"
    version: dict = {"major": 6, "minor": 0, "patch": 5}
    warnedAboutMapMarker: bool = False
    copyOnClick: bool = False
    displayMarkerTooltips: str = "hover"
    displayOverlayTooltips: bool = True
    configDirectory: str | None = None
    mapViewEnabled: bool = True
    mapViewParameters: dict = {}
    enableDraw: bool = True

    model_config = ConfigDict(extra="allow")


class LeafletMapMarker(BaseModel):
    id: str
    lastAccessed: int
    markers: list[LeafletMarker]
    overlays: list
    shapes: list
    files: list

    model_config = ConfigDict(extra="allow")
