# Spotipy Types

Complete Python type hints for the Spotify Web API using Pydantic v2 models.

[![PyPI version](https://badge.fury.io/py/spotipy-types.svg)](https://badge.fury.io/py/spotipy-types)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This package provides complete Python type hints for the Spotify Web API by auto-generating Pydantic v2 models from the official OpenAPI schema. This enables full IDE autocomplete, type checking, and runtime validation when working with [spotipy](https://github.com/spotipy-dev/spotipy).

- **103 Pydantic v2 models** auto-generated from the official Spotify OpenAPI schema
- **Full IDE autocomplete** for all API response fields
- **Runtime validation** of API responses with detailed error messages
- **Type-safe** development with mypy support
- **JSON serialization** for caching and storage

## Installation

```bash
pip install spotipy-types
```

Requires Python 3.11+ and Pydantic v2.

## Quick Start

### Type-Safe Track Access

```python
from spotipy_types import TrackObject
import spotipy

# Initialize spotipy as usual
sp = spotipy.Spotify(auth=token)

# Add type annotation for IDE autocomplete
track: TrackObject = sp.track("11dFghVXANMlKmJXsNCbNl")

# Full autocomplete support!
print(track.name)              # "Cut To The Feeling"
print(track.artists[0].name)   # "Carly Rae Jepsen"
print(track.duration_ms)       # 207959
print(track.explicit)          # False
```

### Validation

```python
from spotipy_types import TrackObject

# Runtime validation of API responses
raw_data = {
    "id": "abc123",
    "name": "Song Name",
    "type": "track",
    "uri": "spotify:track:abc123",
    "duration_ms": 180000,
    "explicit": False,
    "popularity": 50,
}

track = TrackObject.model_validate(raw_data)
# ValidationError if data doesn't match schema
```

### Search Results

```python
from spotipy_types import PagingTrackObject

results = sp.search(q="radiohead", type="track")
tracks_page: PagingTrackObject = PagingTrackObject.model_validate(results['tracks'])

# Type-safe access to paginated results
for track in tracks_page.items:
    print(f"{track.name} by {track.artists[0].name}")
```

### Playlist Management

```python
from spotipy_types import PlaylistObject, PlaylistTrackObject

playlist: PlaylistObject = sp.playlist("playlist_id")
tracks: list[PlaylistTrackObject] = playlist.tracks.items

for item in tracks:
    track = item.track
    added_by = item.added_by.display_name
    print(f"{track.name} added by {added_by}")
```

## Supported Models

### Core Objects
- `TrackObject` - Full track information
- `AlbumObject` - Full album information
- `ArtistObject` - Full artist information
- `PlaylistObject` - Full playlist information
- `EpisodeObject` - Podcast episode
- `ShowObject` - Podcast show
- `AudiobookObject` - Audiobook
- `ChapterObject` - Audiobook chapter

### User Objects
- `PrivateUserObject` - Current user profile
- `PublicUserObject` - Public user profile

### Simplified Objects
- `SimplifiedTrackObject`
- `SimplifiedAlbumObject`
- `SimplifiedArtistObject`
- `SimplifiedPlaylistObject`
- `SimplifiedEpisodeObject`
- `SimplifiedShowObject`

### Response Types
- `PagingObject` - Paginated results
- `CursorPagingObject` - Cursor-based pagination
- `AudioFeaturesObject` - Track audio features
- `AudioAnalysisObject` - Detailed audio analysis
- `RecommendationsObject` - Recommendation results

### Common Types
- `ImageObject` - Album/artist images
- `FollowersObject` - Follower counts
- `ExternalUrlObject` - External links
- `ExternalIdObject` - External IDs (ISRC, EAN, UPC)
- `CopyrightObject` - Copyright information
- `ErrorObject` - API error responses

Plus 70+ additional models covering all Spotify API responses.

## Type Checking with mypy

```python
# mypy will catch type errors
from spotipy_types import TrackObject

track: TrackObject = sp.track("some_id")

# This will fail mypy - id is a string, not int
print(track.id + 1)  # Error: Unsupported operand types for + ("str" and "int")

# This works
track_id: str = track.id
```

## Development

### Regenerating Models

If you have an updated OpenAPI schema:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Generate models
python scripts/generate_models.py

# Or use Make
make generate
```

### Running Tests

```bash
make test
# or
pytest tests/ -v
```

### Type Checking

```bash
make lint
# or
mypy src/spotipy_types/
```

## Versioning

The package version follows the Spotify Web API schema version. For example:
- Package version `2025.5.18` corresponds to schema version `2025.5.18`

Pin to specific versions for reproducibility:

```bash
pip install spotipy-types==2025.5.18
```

## Migration from Untyped Spotipy

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

## Why Pydantic v2?

- **Best-in-class** Python data validation
- **Excellent IDE support** via type hints
- **JSON Schema compatibility**
- **Active development** and large ecosystem
- **Performance** - Pydantic v2 is significantly faster than v1

## Requirements

- Python 3.11+
- Pydantic 2.0+

We require Python 3.11+ to use:
- Union operator syntax (`X | Y` instead of `Union[X, Y]`)
- Better performance
- Modern typing features
- Cleaner generated code

## Schema Source

Models are generated from the official Spotify Web API OpenAPI schema:
- Repository: https://github.com/sonallux/spotify-web-api
- Schema version: 2025.5.18

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Note**: This is a community-maintained package and is not officially affiliated with Spotify.
