import ast
import logging
import re

from obsidian_parser import Note

from ..models.models import ParsedBlock, ParsedNote, LeafletYamlBlock

logger = logging.getLogger(__name__)


def parse_leaflet_notes(notes: list) -> list[ParsedNote]:
    """Parses Leaflet Codeblocks from notes."""
    logger.debug("Parsing Leaflet Notes")
    return [parse_note(note) for note in notes]


def parse_note(note: Note) -> ParsedNote:
    """Scrape note for leaflet code blocks.

    :param note: Description
    :type note: Note
    """
    logger.debug("Parsing Note: %s", note.name)
    pattern = r"(^\s*(?:>+\s*)?```leaflet[\s\S]*?^\s*(?:>+\s*)?```)"

    matches = re.findall(pattern, note.content, re.DOTALL | re.MULTILINE)

    parsed_codeblocks = [parse_leaflet_block(item) for item in matches]

    logger.debug(
        "Number of Parsed Codeblocks for %s: %s", note.name, len(parsed_codeblocks)
    )

    return ParsedNote(note=note, leaflet_blocks=parsed_codeblocks)


def parse_leaflet_block(raw_block: str) -> ParsedBlock:
    """Parse Leaflet Code Block for parameters.

    :param text: Description
    :type text: str
    :return: Description
    :rtype: dict
    """
    lines = raw_block.splitlines()
    try:
        first_content_line = next(line for line in lines if line.strip())
    except StopIteration:
        return ParsedBlock({}, False, 0, raw_block)
    callout_depth = get_callout_depth(first_content_line)
    in_callout = callout_depth > 0
    logger.debug("Callout Depth: %s", callout_depth)
    data = {}
    current_key = None
    collecting_list = False

    for raw_line in lines:
        line = re.sub(rf"^\s*>{{0,{callout_depth}}}\s?", "", raw_line)
        line = line.strip()

        # skip blanks
        if not line or line.startswith("```"):
            continue

        # remove comments
        if "#" in line:
            line, _ = line.split("#", 1)

        if not line.strip() or line.strip().startswith("```"):
            continue

        if collecting_list and re.match(r"^\s*-\s+", line):
            item = line.lstrip()[2:].strip()
            data[current_key].append(parse_value(item))
            continue

        # skip malformed lines
        # if ":" not in line:
        #     continue

        if ":" in line:
            key, value = map(str.strip, line.split(":", 1))

            # Collect list of items, such as image layers
            if value == "":
                data[key] = []
                current_key = key
                collecting_list = True
                continue

            data[key] = parse_value(value)
            collecting_list = False
            current_key = None
            continue

    logger.debug("Data: %s", data)

    return ParsedBlock(
        data=LeafletYamlBlock(**data),
        in_callout=in_callout,
        callout_depth=callout_depth,
        raw_block=raw_block,
    )


def parse_value(value: str):
    """
    Parse values in for a given key.

    :param value: Description
    :type value: str
    """
    # booleans
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    # try number
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass

    # list / array syntax (e.g. [[0,0], [6600, 10200]])
    try:
        return ast.literal_eval(value)
    except Exception:
        pass

    # fallback: string
    return value


def get_callout_depth(line: str) -> int:
    """
    Count leading Markdown blockquote markers.
    """
    return len(re.findall(r"^\s*(>+)", line)[0]) if re.match(r"^\s*>", line) else 0


def check_leafblock_exists(note: Note):
    """Checks note for a leaflet codeblock."""
    PATTERN = r"```leaflet\s*[\s\S]*?```"

    return True if re.findall(PATTERN, note.content) else False
