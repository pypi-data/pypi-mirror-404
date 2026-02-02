import os
from pathlib import Path
import sys

import argparse

from .logs import configure_logger
from .converter.utils import backup_directory, create_target_directory
from .conf.settings import Settings


def build_parser() -> argparse.ArgumentParser:
    """Parse Zoommap-converter arguments."""
    parser = argparse.ArgumentParser(
        prog="zoommap-converter",
        description="Convert Zoommap configs in an Obsidian vault",
    )
    parser.add_argument("--settings", default=os.getenv("SETTINGS"), type=Path)
    # parser.add_argument("--in-place", action="store_true")
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    return parser


def main():
    # --- Phase 0: Parse arguments
    parser = build_parser()
    args = parser.parse_args()

    logger = configure_logger(args.log_level)

    settings = Settings(settings_path=args.settings).settings
    logger.debug("Settings: %s", settings)
    VAULT_PATH = Path(settings.get("vault_path", None))
    if not VAULT_PATH:
        logger.critical(
            "No Vault Path defined in Settings. Please check settings includes: vault_path: /path/to/vault"
        )
        sys.exit(1)

    TARGET_PATH = Path(settings.get("target_path", None))
    if not TARGET_PATH:
        logger.critical(
            "No Target Vault Path defined in Settings. Please check settings includes: target_path: /path/to/target"
        )
        sys.exit(1)

    backup_path = backup_directory(VAULT_PATH, VAULT_PATH.as_posix() + "_backup")
    logger.info("Backup created at: %s", backup_path)

    # --- Phase 1: Create Target Directory
    new_vault_path = create_target_directory(
        source_dir=VAULT_PATH, target_dir=TARGET_PATH
    )

    # --- Phase 2: Load settings from Vault
    from .bootstrap.loader import bootstrap_vault_defaults

    bootstrap_vault_defaults(
        vault_path=new_vault_path,
        source_path=new_vault_path
        / ".obsidian"
        / "plugins"
        / "obsidian-leaflet-plugin"
        / "data.json",
        target_path=new_vault_path / ".obsidian" / "plugins" / "zoom-map" / "data.json",
    )

    # --- Phase 3: Import and Run
    from zoommap_converter.app import run

    FILTERS = settings.get("filters", None)
    LEAFLET_JSON_PATH = (
        Path(".obsidian") / "plugins" / "obsidian-leaflet-plugin" / "data.json"
    )

    run(vault_path=new_vault_path, filters=FILTERS, json_path=LEAFLET_JSON_PATH)
