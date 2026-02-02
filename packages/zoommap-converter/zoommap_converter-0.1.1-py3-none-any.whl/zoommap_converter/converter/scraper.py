import logging

from obsidian_parser import Vault

from .parser import check_leafblock_exists

logger = logging.getLogger(__name__)


def scrape_vault(vault: Vault, filters: dict):
    """Scrape Obsidian Vault for notes containing leaflet blocks.

    :param vault: Vault Object
    """
    logger.debug("Scraping Vault")
    valid_notes = remove_excluded_notes(vault.notes, filters=filters)
    logger.debug("Valid Notes: %s", [note.name for note in valid_notes])
    return scrape_for_leafblocks(valid_notes)


def remove_excluded_notes(vault, filters: dict[str, list[str]]):
    """Removes notes which contain paths matching the exclusion filter.

    :param vault: Vault
    """
    folder_filters = filters.get("folders", ())
    pattern_filters = filters.get("notes_patterns", ())
    specific_filters = filters.get("specific_notes", ())

    def _is_allowed(note):
        path = note.path.as_posix()
        parent = note.path.parent.as_posix()

        return not (
            any(f in parent for f in folder_filters)
            or any(f in path for f in pattern_filters)
            or any(f in path for f in specific_filters)
        )

    return [note for note in vault if _is_allowed(note)]


def scrape_for_leafblocks(notes: list):
    """Scrapes notes to find notes which contain leaflet codeblocks.

    :param notes: Description
    :type notes: Vault
    """
    leafblock_notes = []
    for note in notes:
        if check_leafblock_exists(note):
            leafblock_notes.append(note)
    return [note for note in notes if check_leafblock_exists(note)]
