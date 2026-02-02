import logging
from obsidian_parser import Vault

from .converter.parser import parse_leaflet_notes
from .converter.scraper import scrape_vault
from .converter.converter import convert_note
from .converter.render import render_zoommap
from .converter.utils import read_json

logger = logging.getLogger(__name__)

NON_IMAGE_SUFFIXES = (
    # Code/files
    ".md",
    ".json",
    ".js",
    ".py",
    ".ts",
    ".jsx",
    ".tsx",
    ".html",
    ".css",
    ".scss",
    ".less",
    ".php",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rb",
    ".sh",
    ".bat",
    ".ps1",
    ".sql",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".log",
    ".txt",
    ".csv",
    ".tsv",
    ".xml",
    # Documents
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".odt",
    ".ods",
    ".odp",
    ".rtf",
    # Archives/compressed
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".rar",
    ".xz",
    # System/files
    ".gitignore",
    ".gitattributes",
    ".gitkeep",
    ".gitmodules",
    ".dockerignore",
    ".env",
    ".htaccess",
    ".htpasswd",
    # Build/config
    ".lock",
    ".min.js",
    ".min.css",
    ".map",
    ".d.ts",
    ".dll",
    ".exe",
    ".so",
    ".dylib",
    ".a",
    ".o",
    ".class",
    # Temporary/cache
    ".tmp",
    ".temp",
    ".bak",
    ".backup",
    ".swp",
    ".swo",
    ".cache",
    # Media (non-image)
    ".mp3",
    ".wav",
    ".ogg",
    ".flac",
    ".m4a",
    ".aac",
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".flv",
    ".wmv",
)


def run(vault_path, filters, json_path):
    vault = Vault(vault_path)
    NON_NOTE_FILES = [
        file
        for file in vault.file_paths
        if not file.as_posix().endswith(NON_IMAGE_SUFFIXES)
    ]
    logger.info("Hello from zoommap-converter!")
    logger.debug("Vault Path: %s", vault.path.as_posix())
    logger.debug("Filters: %s", filters)
    notes_with_leaflet_blocks = scrape_vault(vault, filters)
    logger.debug("-" * 50)
    logger.debug(
        "Filtered Notes: %s", [note.name for note in notes_with_leaflet_blocks]
    )
    logger.debug("-" * 50)
    parsed_notes = parse_leaflet_notes(notes_with_leaflet_blocks)
    # logger.debug("Leaflet Dicts: %s", [item.note.name for item in leaflet_dict])
    # logger.debug("Sample Leaflet Objects: %s", [item.leaflet_blocks[0] for item in leaflet_dict])
    logger.debug("Leaflet Dicts: %s", parsed_notes)
    logger.debug("-" * 50)
    leaflet_json_data = read_json(file_path=vault.path / json_path)
    logger.debug("Leaflet's data.json: %s", leaflet_json_data)
    zoommap_data = [
        convert_note(
            leaflet_note=note,
            leaflet_data=leaflet_json_data,
            non_note_files=NON_NOTE_FILES,
            vault_path=vault.path,
        )
        for note in parsed_notes
    ]
    logger.debug("Sample Converted Zoommap Data: %s", zoommap_data[0])
    zoommap_data_flat = [item for sublist in zoommap_data for item in sublist]
    replacements = {data.note.name: render_zoommap(data) for data in zoommap_data_flat}
    logger.info("The following codeblock replacements failed.")
    logger.info("Replacements: %s", replacements)
    if replacements:
        logger.info("%s", replacements)
    logger.info("Conversion Complete!")
