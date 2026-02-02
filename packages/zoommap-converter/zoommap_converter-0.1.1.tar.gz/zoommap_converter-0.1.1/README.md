### Leaflet-to-Zoommap Converter

This repository contains a Python CLI tool to parse Obsidian Vaults and convert Leaflet codeblocks to Zoommap ([TTRPG Tools: Maps](https://github.com/Jareika/zoom-map)) format, supporting map scales, icons and shapes.

## Overview

ZoomMap Converter is designed to facilitate the migration from the Obsidian Leaflet plugin to the ZoomMap plugin. It handles the conversion of map notes, markers, and configurations while maintaining compatibility with Obsidian vault structures.

## Features

- **Note Conversion**: Converts Leaflet-formatted codeblocks to ZoomMap format.
- **Icon Processing**: Transforms custom SVG icons with color and size normalisation over to Zoommap.
- **Error Handling**: Validation and logging for troubleshooting.
- **Path Management**: Handles Obsidian vault file paths and structures.

## Installation

### Prerequisites

- Python 3.12+
- Obsidian vault with Leaflet plugin notes
- Leaflet Plug-In installed and enabled.
- Zoommap Plug-In installed and enabled.

### Setup

1. Download the CLI tool using `pip`.

```bash
pip install zoommap-converter
```

2. Once installed, you can test the install was successful using:

```bash
zoommap-converter --version
```


## Usage

### Basic Conversion

1. Create and configure the `settings.yaml` file and ensure to include the `vault_path` and `target_path`:

```yaml
vault_path: leaflet-vault
target_path: converted-leaflet-vault
```

**Note:** See the sample [`settings.yaml`](settings.yaml) for more configuration options.

2. Set the path to your settings.yaml via environment variables:

```bash
export SETTINGS=path/to/settings.yaml

zoommap-converter
```

Or pass it as an argument to the tool:

```bash
zoommap-converter --settings path/to/settings.yaml
```

## Development

### Project Structure

```
├── src
│   └── zoommap_converter
│       ├── __init__.py
│       ├── __main__.py
│       ├── app.py
│       ├── cli.py          # Command-line interface
│       ├── logs.py
│       ├── bootstrap/      # Initialisation and setup
│       ├── conf/           # Settings Config
│       ├── converter/      # Core conversion logic
│       └── models/         # Data models and schemas
tests/
```

### Developer Setup

1. Clone the repository:
   ```bash
   git clone https://codeberg.org/paddyd/zoommap-converter.git
   cd zoommap-converter
   ```

2. Install dependencies using `uv`:
   ```bash
   uv install
   ```

3. Configure the vault path in `settings.yaml` or via environment variables

### Running Tests

```bash
uv run pytest tests
```

### Building

```bash
uv build
```

## Contributing

Contributions are welcome. Please use the provided issue and pull request templates when contributing and follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with clear documentation
4. Include tests for new functionality

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions or feature requests, please file an [issue](https://codeberg.org/paddyd/zoommap-converter/issues/new).

## Acknowledgements

- [Jareika](https://github.com/Jareika) the creator of [TTRPG Tools: Maps](https://github.com/Jareika/zoom-map).
- Obsidian community for plugin development
- Font Awesome for icon assets
- Pydantic for data validation
