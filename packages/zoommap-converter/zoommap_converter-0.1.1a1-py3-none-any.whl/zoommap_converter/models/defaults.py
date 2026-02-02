import logging
import os
from pathlib import Path
from functools import lru_cache
from ..conf.settings import Settings
from ..converter.utils import read_json

logger = logging.getLogger(__name__)

settings = Settings(settings_path=os.getenv("SETTINGS")).settings

VAULT_PATH = Path(settings.get("vault_path", None))
DEFAULTS_DIR = VAULT_PATH / ".obsidian" / "plugins"


def set_vault_root(path: Path) -> None:
    global VAULT_PATH
    VAULT_PATH = path


@lru_cache
def load_defaults(file_path: Path) -> dict:
    f = DEFAULTS_DIR / file_path
    logger.debug("Loading defaults from %s", f)
    return read_json(f)
