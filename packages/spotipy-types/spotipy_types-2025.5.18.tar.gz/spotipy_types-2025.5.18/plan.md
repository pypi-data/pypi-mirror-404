# Spotipy Types - Implementation Plan

A standalone type stub package for spotipy using Pydantic models generated from the official Spotify Web API OpenAPI schema.

## Overview

This repository provides complete Python type hints for the Spotify Web API by auto-generating Pydantic v2 models from the official OpenAPI schema. This enables full IDE autocomplete, type checking, and runtime validation when working with spotipy.

## Repository Structure

```
spotipy-types/
├── src/
│   └── spotipy_types/          # Generated package
│       ├── __init__.py         # Re-exports all models
│       ├── models.py           # Generated from OpenAPI (~3K lines)
│       └── _version.py         # Version info (matches schema date)
├── schemas/
│   └── spotify_openapi.yaml    # Official Spotify OpenAPI schema
├── scripts/
│   └── generate_models.py      # Code generation automation
├── tests/
│   └── test_models.py          # Validation tests
├── .github/
│   └── workflows/
│       ├── generate.yml        # Auto-regenerate on schema updates
│       └── publish.yml         # PyPI publishing
├── pyproject.toml              # Package configuration
├── README.md                   # Usage documentation
├── LICENSE                     # MIT License
└── Makefile                    # Convenience commands
```

## Phase 1: Repository Setup

### 1.1 Initialize Package Structure
- Create `pyproject.toml` with hatchling build backend
- Set package metadata:
  - Name: `spotipy-types`
  - Version: `2025.5.18` (matches schema version)
  - Python: `>=3.11`
  - Dependencies: `pydantic>=2.0.0`

### 1.2 Configuration Files
- `.gitignore` - Standard Python ignores + generated files
- `LICENSE` - MIT License
- `Makefile` with commands:
  - `make generate` - Run datamodel-codegen
  - `make test` - Run pytest
  - `make lint` - Run ruff and mypy
  - `make build` - Build wheel
  - `make publish` - Publish to PyPI

## Phase 2: Code Generation Setup

### 2.1 Install datamodel-codegen
```bash
pip install datamodel-code-generator
```

### 2.2 Generation Script (`scripts/generate_models.py`)
```bash
datamodel-codegen \
  --input schemas/spotify_openapi.yaml \
  --input-file-type openapi \
  --output src/spotipy_types/models.py \
  --output-model-type pydantic_v2.BaseModel \
  --use-union-operator \
  --use-standard-collections \
  --use-default-kwarg \
  --target-python-version 3.11 \
  --use-field-description \
  --wrap-string-literal \
  --field-constraints \
  --collapse-root-models \
  --set-default-enum-member
```

### 2.3 Post-Generation Processing
- Add module docstring with version info
- Ensure all imports are properly organized
- Verify no circular import issues
- Add `__all__` export list

## Phase 3: Package Implementation

### 3.1 Generated Models (`src/spotipy_types/models.py`)
Expected content:
- ~120 Pydantic model classes
- ~3,000 lines of generated code
- All Spotify API response types:
  - TrackObject, AlbumObject, ArtistObject
  - PlaylistObject, EpisodeObject, ShowObject
  - UserObject, DeviceObject, ContextObject
  - AudioFeaturesObject, AudioAnalysisObject
  - SearchResponse, PagingObject, CursorPagingObject
  - And 100+ more...

### 3.2 Package Initialization (`src/spotipy_types/__init__.py`)
```python
"""Spotipy Types - Pydantic models for the Spotify Web API."""

from spotipy_types._version import __version__
from spotipy_types.models import (
    TrackObject,
    AlbumObject,
    ArtistObject,
    # ... all 120+ models
)

__all__ = [
    "__version__",
    "TrackObject",
    "AlbumObject",
    "ArtistObject",
    # ... all exports
]
```

### 3.3 Version Module (`src/spotipy_types/_version.py`)
```python
"""Version information."""

__version__ = "2025.5.18"
__schema_version__ = "2025.5.18"
__schema_source__ = "https://github.com/sonallux/spotify-web-api"
```

## Phase 4: Testing & Validation

### 4.1 Test Suite (`tests/test_models.py`)
Tests should cover:
- Model instantiation with valid data
- Required field validation
- Optional field handling
- Nested object validation
- Enum validation
- Union type handling (TrackObject | EpisodeObject)
- JSON serialization/deserialization roundtrip

### 4.2 Type Checking
- Run mypy on generated code
- Verify no typing errors
- Check import resolution

## Phase 5: CI/CD Automation

### 5.1 GitHub Actions: Generate Workflow (`.github/workflows/generate.yml`)
Triggered on:
- PRs that modify `schemas/spotify_openapi.yaml`
- Manual dispatch

Steps:
1. Checkout code
2. Install datamodel-codegen
3. Run generation script
4. Check if models changed
5. Create PR with regenerated models
6. Run tests on regenerated code

### 5.2 GitHub Actions: Publish Workflow (`.github/workflows/publish.yml`)
Triggered on:
- Tags matching `v*` pattern

Steps:
1. Checkout code
2. Install build tools
3. Run tests
4. Build wheel and sdist
5. Publish to PyPI

## Phase 6: Documentation

### 6.1 README.md Sections
1. **Installation**
   ```bash
   pip install spotipy-types
   ```

2. **Basic Usage**
   ```python
   from spotipy_types import TrackObject, AlbumObject
   import spotipy
   from spotipy.oauth2 import SpotifyClientCredentials

   # Get typed results from spotipy
   sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
   
   # Type hint for IDE autocomplete
   track: TrackObject = sp.track("11dFghVXANMlKmJXsNCbNl")
   
   print(track.name)              # IDE suggests this
   print(track.artists[0].name)   # Full nested type support
   ```

3. **Validation**
   ```python
   from spotipy_types import TrackObject

   # Runtime validation of API responses
   raw_data = {"id": "abc123", "name": "Song Name", ...}
   track = TrackObject.model_validate(raw_data)
   ```

4. **Type Checking with mypy**
   ```python
   # mypy will catch type errors
   track: TrackObject = sp.track("some_id")
   
   # This will fail mypy - id is a string, not int
   print(track.id + 1)  # Error: can't add int to str
   ```

5. **Supported Models**
   - List all 120+ generated models
   - Link to full API reference

6. **Versioning**
   - Package version matches schema version
   - Pin to specific version for reproducibility

7. **Development**
   - How to regenerate models
   - How to contribute

### 6.2 Changelog.md
Track changes between schema versions:
- Added fields
- Removed fields
- Type changes
- Breaking changes

## Technical Decisions

### Why Pydantic v2?
- Best-in-class Python data validation
- Excellent IDE support via type hints
- JSON Schema compatibility
- Active development and large ecosystem

### Why Python 3.11+?
- Union operator syntax (`X | Y` vs `Union[X, Y]`)
- Better performance
- Modern typing features
- Cleaner generated code

### Why Full Models vs Stubs?
- Runtime validation catches API changes
- Serialization/deserialization support
- Better than static stubs for dynamic data

## Schema Analysis

### Source Schema: `spotify_schema.txt`
- Format: OpenAPI 3.0.3 (already converted)
- Size: ~260KB, 6,945 lines
- Components section: Line 3,525
- Schemas section: Line 4,085

### Key Schema Patterns
1. **Heavy Reference Usage**: Deep chains (AlbumObject → ArtistObject → ImageObject)
2. **Union Types**: `items: TrackObject | EpisodeObject` for polymorphic responses
3. **Inheritance via allOf**: Composition pattern for shared fields
4. **Nullable Fields**: `display_name: string | null` with `nullable: true`

### Expected Generated Code Stats
- Total lines: ~3,000
- Model classes: ~120
- Average class size: 15-30 fields
- Most complex models: TrackObject, AlbumObject, EpisodeObject

## Usage Examples

### Example 1: Type-Safe Track Access
```python
from spotipy_types import TrackObject
import spotipy

sp = spotipy.Spotify(auth=token)
track: TrackObject = sp.track("track_id")

# Full autocomplete support
artist_names = [a.name for a in track.artists]
duration_ms = track.duration_ms
is_explicit = track.explicit
```

### Example 2: Search Response Handling
```python
from spotipy_types import SearchResponse

results = sp.search(q="radiohead", type="track")
search_response = SearchResponse.model_validate(results)

# Type-safe access to paginated results
tracks = search_response.tracks.items
for track in tracks:
    print(f"{track.name} by {track.artists[0].name}")
```

### Example 3: Playlist Management
```python
from spotipy_types import PlaylistObject, PlaylistTrackObject

playlist: PlaylistObject = sp.playlist("playlist_id")
tracks: list[PlaylistTrackObject] = playlist.tracks.items

for item in tracks:
    track = item.track
    added_by = item.added_by.display_name
```

## Migration Path for Existing Spotipy Users

### Before (no types)
```python
import spotipy

sp = spotipy.Spotify(auth=token)
track = sp.track("id")  # Returns dict
print(track["name"])    # No autocomplete, typo-prone
```

### After (with spotipy-types)
```python
import spotipy
from spotipy_types import TrackObject

sp = spotipy.Spotify(auth=token)
track: TrackObject = sp.track("id")  # Same call, typed result
print(track.name)                    # IDE autocomplete works!
```

## Future Enhancements

1. **Async Support**: Models work with async spotipy clients
2. **Optional Validation**: Allow passthrough mode for performance
3. **Partial Models**: Generate subset models for specific use cases
4. **Documentation Links**: Add docstring links to Spotify API docs
5. **Example Data**: Include example instances for each model

## Timeline

- **Phase 1**: 15 minutes - Repository setup
- **Phase 2**: 20 minutes - Code generation configuration
- **Phase 3**: 15 minutes - Package structure and exports
- **Phase 4**: 20 minutes - Testing and validation
- **Phase 5**: 20 minutes - CI/CD automation
- **Phase 6**: 15 minutes - Documentation

**Total: ~2 hours** to fully functional package

## Success Metrics

- [ ] Package installs successfully via pip
- [ ] All 120+ models import without errors
- [ ] mypy passes with zero errors
- [ ] Basic smoke tests pass
- [ ] Example usage works in IDE with autocomplete
- [ ] Published to PyPI

## Notes

- Schema source: https://github.com/sonallux/spotify-web-api
- Package will be community-maintained
- Follows semantic versioning for schema updates
- Generated code is committed for transparency
- Original schema preserved for regeneration

---

**Next Step**: Proceed to Phase 1 - Create pyproject.toml and repository structure
