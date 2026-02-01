# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Shoggoth is a card creation desktop application for Arkham Horror: The Card Game. Built with Python 3.11+ and PySide6 (Qt), it enables users to design and render custom homebrew cards.

## Build & Run Commands

```bash
# Install dependencies
uv sync

# Run the application (UI mode)
uv run shoggoth

# Run in viewer mode (live-reloading for text editor workflow)
uv run shoggoth -v project.json

# Run in render mode (headless card image export)
uv run shoggoth -r project.json

# Build standalone executable
uv run --dev pyinstaller ShoggothStandalone.spec
```

No test or lint framework is currently configured.

## Architecture

### Application Modes
- **UI Mode** (default): Interactive card designer with visual preview
- **Viewer Mode** (`-v`): Live-reloading project viewer
- **Render Mode** (`-r`): Headless card image exporter

### Core Components

**Entry Point**: `shoggoth/__main__.py` → `tool.py:run()` → `main_qt.py:main()`

**Main Window** (`main_window.py` - largest module):
- `ShoggothMainWindow` - main application window with dockable panels
- `FileBrowser` - tree view of project cards and encounter sets
- Manages menu bar, card selection, and event handling

**Data Model** (`project.py`, `card.py`):
- `Project` - JSON file wrapper containing cards, encounter sets, guides
- `Card` - single card with front/back `Face` objects
- `Face` - card side with template inheritance and type-specific fields

**Rendering Pipeline** (`renderer.py`, `rich_text.py`):
- `CardRenderer` - main rendering engine with image caching
- `RichTextRenderer` - Arkham text syntax parsing and symbol rendering
- Exports to JPEG/PNG/WebP via PIL

**Editor System** (`editors.py`, `face_editors.py`):
- `FieldWidget` base class for property binding
- Dynamic editor generation per card type (enemy, asset, location, etc.)
- Signal/slot connections sync UI with card data

**Asset Management**:
- Asset pack downloaded at runtime from Dropbox to `platformdirs` user data directory
- Contains templates, overlays, icons, fonts, defaults

### Key Modules by Function

| Module | Purpose |
|--------|---------|
| `main_window.py` | Main GUI window and application state |
| `renderer.py` | Card image rendering engine |
| `rich_text.py` | Text formatting and symbol parsing |
| `face_editors.py` | Type-specific card property editors |
| `editors.py` | Base editor widget framework |
| `project.py` | Project file I/O and card access |
| `card.py` | Card/Face data classes with template inheritance |
| `preview_widget.py` | Real-time card preview display |
| `tree_context_menu.py` | Right-click CRUD operations |
| `settings.py` | Cross-platform settings persistence |
| `file_monitor.py` | Watchdog-based file change detection |

### Template Inheritance

Cards use a fallback chain for properties: Face → Type Template → Class Override → Defaults. Template types include: enemy, asset, location, treachery, event, skill, investigator, etc.

### Threading Model

Preview updates run in separate threads to keep UI responsive. File monitoring uses watchdog with debouncing for live reload.
