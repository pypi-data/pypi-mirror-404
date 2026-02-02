from pathlib import Path
import json
import logging
import re
import urllib.parse
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)


def get_data(file_path):
    """
    Reads a txt file.

    Args:
        file_path (str): Path to the txt file.

    Returns:
        str: A string representation of the file contents.
    """
    try:
        with Path.open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        logger.error("File %s not found.", file_path)
        return []
    except Exception as e:
        logger.error("An error occurred: %s", e)
        return []


def read_json(file_path):
    """
    Reads a JSON file.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        dict or list: The JSON data parsed into a Python object.
    """
    try:
        with Path.open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error("File %s not found.", file_path)
        return {}
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON: %s", e)
        return {}
    except Exception as e:
        logger.error("An error occurred: %s", e)
        return {}


def clean_image_name(filename):
    """Function to clean up the filenames of images for Zoommap's imageBase name field."""
    # Remove file extension
    name = re.sub(r"\.[a-zA-Z0-9]+$", "", filename)

    # Remove common patterns (timestamps, IDs, etc.)
    name = re.sub(
        r"[-_](\d{10,}|[a-f0-9]{8,}|[a-z0-9]{8,})$", "", name, flags=re.IGNORECASE
    )

    # Remove trailing separators
    name = name.rstrip("-_ ")

    return name.strip()


def decode_utf8_url_encoded(data: str) -> str:
    """Decode URL-encoded UTF-8 strings in dictionary values."""
    result = data

    try:
        result = urllib.parse.unquote_plus(result)
    except Exception:
        # If decoding fails, keep original value
        pass

    return result


def backup_directory(
    source_dir: str | Path,
    backup_root: str | Path,
) -> Path:
    source_dir = Path(source_dir).resolve()
    backup_root = Path(backup_root).resolve()

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / f"{source_dir.name}_backup_{timestamp}"

    shutil.copytree(
        src=source_dir,
        dst=backup_dir,
        copy_function=shutil.copy2,  # preserves metadata
        dirs_exist_ok=False,  # fail loudly if exists
    )

    return backup_dir


def create_target_directory(
    source_dir: str | Path,
    target_dir: str | Path,
) -> Path:
    """Creates Target Directory to perform conversion on, and avoid risk of overwriting data."""
    source_dir = Path(source_dir).resolve()
    target_dir = Path(target_dir).resolve()

    # Check source exists
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")
    # Check target directory state
    if target_dir.exists():
        # Check if target is populated with files
        try:
            if any(target_dir.iterdir()):
                raise FileExistsError(
                    f"Target directory exists and is not empty: {target_dir}"
                )
        except PermissionError:
            raise FileExistsError(f"Cannot access target directory: {target_dir}")
        # Target exists but is empty, use it directly
        return target_dir
    # Target doesn't exist, create it
    try:
        shutil.copytree(
            src=source_dir,
            dst=target_dir,
            copy_function=shutil.copy2,  # preserves metadata
            dirs_exist_ok=False,  # fail loudly if exists
        )
    except PermissionError:
        raise PermissionError(f"Cannot create target directory: {target_dir}")

    return target_dir
