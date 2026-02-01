"""Tests for spotipy-types Pydantic models."""

import pytest
from spotipy_types import (
    TrackObject,
    AlbumObject,
    ArtistObject,
    PlaylistObject,
    PrivateUserObject,
    PublicUserObject,
    DeviceObject,
    PagingObject,
    AudioFeaturesObject,
    ImageObject,
    ErrorObject,
)


class TestModelInstantiation:
    """Test basic model instantiation with valid data."""

    def test_track_object_minimal(self) -> None:
        """Test creating TrackObject with minimal required fields."""
        data = {
            "id": "test-track-123",
            "name": "Test Track",
            "type": "track",
            "uri": "spotify:track:test-track-123",
            "duration_ms": 180000,
            "explicit": False,
            "popularity": 50,
            "preview_url": None,
            "track_number": 1,
            "disc_number": 1,
            "is_local": False,
            "is_playable": True,
            "external_ids": {},
            "external_urls": {},
            "available_markets": ["US", "CA"],
            "artists": [],
            "album": None,
        }
        track = TrackObject.model_validate(data)
        assert track.id == "test-track-123"
        assert track.name == "Test Track"
        assert track.type == "track"

    def test_simplified_album_object_minimal(self) -> None:
        """Test creating SimplifiedAlbumObject with minimal required fields."""
        from spotipy_types import SimplifiedAlbumObject

        data = {
            "id": "test-album-456",
            "name": "Test Album",
            "type": "album",
            "uri": "spotify:album:test-album-456",
            "album_type": "album",
            "total_tracks": 10,
            "release_date": "2024-01-15",
            "release_date_precision": "day",
            "external_urls": {},
            "href": "https://api.spotify.com/v1/albums/test-album-456",
            "available_markets": ["US"],
            "artists": [],
            "images": [],
        }
        album = SimplifiedAlbumObject.model_validate(data)
        assert album.id == "test-album-456"
        assert album.name == "Test Album"
        assert album.album_type == "album"

    def test_artist_object_minimal(self) -> None:
        """Test creating ArtistObject with minimal required fields."""
        data = {
            "id": "test-artist-789",
            "name": "Test Artist",
            "type": "artist",
            "uri": "spotify:artist:test-artist-789",
            "external_urls": {},
            "images": [],
            "genres": [],
            "popularity": 80,
            "followers": {"total": 1000000, "href": None},
        }
        artist = ArtistObject.model_validate(data)
        assert artist.id == "test-artist-789"
        assert artist.name == "Test Artist"
        assert artist.type == "artist"

    def test_private_user_object(self) -> None:
        """Test creating PrivateUserObject."""
        data = {
            "id": "test-user-abc",
            "display_name": "Test User",
            "type": "user",
            "uri": "spotify:user:test-user-abc",
            "external_urls": {},
            "followers": {"total": 100, "href": None},
            "images": [],
            "country": "US",
            "email": "test@example.com",
            "explicit_content": {"filter_enabled": False, "filter_locked": False},
            "product": "premium",
        }
        user = PrivateUserObject.model_validate(data)
        assert user.id == "test-user-abc"
        assert user.display_name == "Test User"
        assert user.email == "test@example.com"

    def test_device_object(self) -> None:
        """Test creating DeviceObject."""
        data = {
            "id": "test-device-xyz",
            "name": "Test Device",
            "type": "Computer",
            "is_active": True,
            "is_private_session": False,
            "is_restricted": False,
            "supports_volume": True,
            "volume_percent": 50,
        }
        device = DeviceObject.model_validate(data)
        assert device.id == "test-device-xyz"
        assert device.name == "Test Device"
        assert device.type == "Computer"


class TestNestedObjects:
    """Test nested object validation."""

    def test_track_with_artist(self) -> None:
        """Test TrackObject with nested ArtistObject."""
        data = {
            "id": "track-123",
            "name": "Test Track",
            "type": "track",
            "uri": "spotify:track:track-123",
            "duration_ms": 180000,
            "explicit": False,
            "popularity": 50,
            "preview_url": None,
            "track_number": 1,
            "disc_number": 1,
            "is_local": False,
            "is_playable": True,
            "external_ids": {},
            "external_urls": {},
            "available_markets": ["US"],
            "artists": [
                {
                    "id": "artist-456",
                    "name": "Test Artist",
                    "type": "artist",
                    "uri": "spotify:artist:artist-456",
                    "external_urls": {},
                    "images": [],
                    "genres": [],
                    "popularity": 80,
                    "followers": {"total": 1000000, "href": None},
                }
            ],
            "album": None,
        }
        track = TrackObject.model_validate(data)
        assert len(track.artists) == 1
        assert track.artists[0].name == "Test Artist"

    def test_album_with_image(self) -> None:
        """Test SimplifiedAlbumObject with nested ImageObject."""
        from spotipy_types import SimplifiedAlbumObject

        data = {
            "id": "album-123",
            "name": "Test Album",
            "type": "album",
            "uri": "spotify:album:album-123",
            "album_type": "album",
            "total_tracks": 10,
            "release_date": "2024-01-15",
            "release_date_precision": "day",
            "external_urls": {},
            "href": "https://api.spotify.com/v1/albums/album-123",
            "available_markets": ["US"],
            "artists": [],
            "images": [
                {
                    "url": "https://example.com/image.jpg",
                    "height": 640,
                    "width": 640,
                }
            ],
        }
        album = SimplifiedAlbumObject.model_validate(data)
        assert len(album.images) == 1
        assert album.images[0].url == "https://example.com/image.jpg"
        assert album.images[0].height == 640


class TestSerialization:
    """Test JSON serialization and deserialization."""

    def test_track_roundtrip(self) -> None:
        """Test TrackObject serialization roundtrip."""
        original_data = {
            "id": "track-123",
            "name": "Test Track",
            "type": "track",
            "uri": "spotify:track:track-123",
            "duration_ms": 180000,
            "explicit": False,
            "popularity": 50,
            "preview_url": None,
            "track_number": 1,
            "disc_number": 1,
            "is_local": False,
            "is_playable": True,
            "external_ids": {},
            "external_urls": {},
            "available_markets": ["US"],
            "artists": [],
            "album": None,
        }
        track = TrackObject.model_validate(original_data)
        json_str = track.model_dump_json()
        assert "track-123" in json_str
        assert "Test Track" in json_str

    def test_model_dump(self) -> None:
        """Test model_dump produces dict."""
        data = {
            "id": "device-123",
            "name": "Test Device",
            "type": "Computer",
            "is_active": True,
            "is_private_session": False,
            "is_restricted": False,
            "supports_volume": True,
            "volume_percent": 50,
        }
        device = DeviceObject.model_validate(data)
        dumped = device.model_dump()
        assert isinstance(dumped, dict)
        assert dumped["id"] == "device-123"


class TestErrorHandling:
    """Test error handling and validation."""

    def test_missing_required_field(self) -> None:
        """Test that missing required fields raise validation error."""
        data = {
            "status": 404,
            # Missing required 'message' field
        }
        with pytest.raises(Exception):  # pydantic.ValidationError
            ErrorObject.model_validate(data)

    def test_error_object(self) -> None:
        """Test ErrorObject model."""
        data = {
            "status": 404,
            "message": "Not found",
        }
        error = ErrorObject.model_validate(data)
        assert error.status == 404
        assert error.message == "Not found"


class TestPaging:
    """Test paging object models."""

    def test_paging_object(self) -> None:
        """Test PagingObject with tracks."""
        data = {
            "href": "https://api.spotify.com/v1/me/tracks",
            "limit": 20,
            "next": "https://api.spotify.com/v1/me/tracks?offset=20&limit=20",
            "offset": 0,
            "previous": "",
            "total": 100,
        }
        paging = PagingObject.model_validate(data)
        assert paging.total == 100
        assert paging.limit == 20
        assert paging.offset == 0


class TestImport:
    """Test that all models can be imported."""

    def test_import_all_models(self) -> None:
        """Test that all models from __all__ can be imported."""
        from spotipy_types import __all__

        # Import everything from __all__
        import spotipy_types as st

        for name in __all__:
            if not name.startswith("__"):
                assert hasattr(st, name), f"Missing export: {name}"

    def test_version_info(self) -> None:
        """Test version information is accessible."""
        from spotipy_types import __version__, __schema_version__, __schema_source__

        assert __version__ == "2025.5.18"
        assert __schema_version__ == "2025.5.18"
        assert "github.com" in __schema_source__
