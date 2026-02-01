"""Spotipy Types - Pydantic models for the Spotify Web API.

This package provides complete Python type hints for the Spotify Web API
by auto-generating Pydantic v2 models from the official OpenAPI schema.

Example:
    >>> from spotipy_types import TrackObject, AlbumObject
    >>> import spotipy
    >>> sp = spotipy.Spotify(auth=token)
    >>> track: TrackObject = sp.track("track_id")
    >>> print(track.name)
    >>> print(track.artists[0].name)
"""

from spotipy_types._version import __version__, __schema_version__, __schema_source__
from spotipy_types.models import (
    # Core Objects
    TrackObject,
    AlbumObject,
    ArtistObject,
    PlaylistObject,
    EpisodeObject,
    ShowObject,
    DeviceObject,
    # User Objects (both private and public)
    PrivateUserObject,
    PublicUserObject,
    # Response Types
    PagingObject,
    CursorPagingObject,
    # Audio Features
    AudioFeaturesObject,
    AudioAnalysisObject,
    # Simplified Objects
    SimplifiedTrackObject,
    SimplifiedAlbumObject,
    SimplifiedArtistObject,
    SimplifiedPlaylistObject,
    SimplifiedEpisodeObject,
    SimplifiedShowObject,
    # Other Common Types
    ImageObject,
    FollowersObject,
    ExternalUrlObject,
    ExternalIdObject,
    # Restriction Objects
    TrackRestrictionObject,
    AlbumRestrictionObject,
    EpisodeRestrictionObject,
    ChapterRestrictionObject,
    # Error Handling
    ErrorObject,
    # Context and Playback
    ContextObject,
    CurrentlyPlayingObject,
    CurrentlyPlayingContextObject,
    PlayHistoryObject,
    QueueObject,
    # Playlist
    PlaylistTrackObject,
    # Saved Objects
    SavedTrackObject,
    SavedAlbumObject,
    SavedShowObject,
    SavedEpisodeObject,
    # Recommendations
    RecommendationsObject,
    RecommendationSeedObject,
    # Search (inline type - no separate SearchResponse class)
    # Copyright
    CopyrightObject,
    # Resume Point
    ResumePointObject,
    # Linked Track
    LinkedTrackObject,
    # Time Interval
    TimeIntervalObject,
    # Cursor
    CursorObject,
    # Disallows
    DisallowsObject,
    # Narrator and Author
    NarratorObject,
    AuthorObject,
    # Audiobooks and Chapters
    AudiobookObject,
    SimplifiedAudiobookObject,
    ChapterObject,
    SimplifiedChapterObject,
    SavedAudiobookObject,
    # Categories
    CategoryObject,
    # Section and Segment
    SectionObject,
    SegmentObject,
    # Playlist User/Owner
    PlaylistUserObject,
    PlaylistOwnerObject,
    # Playlist Tracks Reference
    PlaylistTracksRefObject,
    # Explicit Content Settings
    ExplicitContentSettingsObject,
    # Paging variants
    PagingTrackObject,
    PagingArtistObject,
    PagingPlaylistObject,
    PagingPlaylistTrackObject,
    PagingSavedTrackObject,
    PagingSavedAlbumObject,
    PagingSavedShowObject,
    PagingSavedEpisodeObject,
    PagingSimplifiedTrackObject,
    PagingSimplifiedAlbumObject,
    PagingSimplifiedShowObject,
    PagingSimplifiedAudiobookObject,
    PagingSimplifiedEpisodeObject,
    PagingSimplifiedChapterObject,
    PagingArtistDiscographyAlbumObject,
    PagingSavedAudiobookObject,
    CursorPagingSimplifiedArtistObject,
    CursorPagingPlayHistoryObject,
    # Featured playlists
    PagingFeaturedPlaylistObject,
    # Saved wrapper objects
    SavedTrackObject,
    SavedAlbumObject,
    SavedShowObject,
    SavedEpisodeObject,
    SavedAudiobookObject,
    # Discography
    ArtistDiscographyAlbumObject,
    # Enums and other types
    Reason,
    Type,
    Mode1,
    Pitch,
)

__all__ = [
    "__version__",
    "__schema_version__",
    "__schema_source__",
    # Core Objects
    "TrackObject",
    "AlbumObject",
    "ArtistObject",
    "PlaylistObject",
    "EpisodeObject",
    "ShowObject",
    "DeviceObject",
    # User Objects
    "PrivateUserObject",
    "PublicUserObject",
    # Response Types
    "PagingObject",
    "CursorPagingObject",
    # Audio Features
    "AudioFeaturesObject",
    "AudioAnalysisObject",
    # Simplified Objects
    "SimplifiedTrackObject",
    "SimplifiedAlbumObject",
    "SimplifiedArtistObject",
    "SimplifiedPlaylistObject",
    "SimplifiedEpisodeObject",
    "SimplifiedShowObject",
    "SimplifiedAudiobookObject",
    "SimplifiedChapterObject",
    # Other Common Types
    "ImageObject",
    "FollowersObject",
    "ExternalUrlObject",
    "ExternalIdObject",
    # Restriction Objects
    "TrackRestrictionObject",
    "AlbumRestrictionObject",
    "EpisodeRestrictionObject",
    "ChapterRestrictionObject",
    # Error Handling
    "ErrorObject",
    # Context and Playback
    "ContextObject",
    "CurrentlyPlayingObject",
    "CurrentlyPlayingContextObject",
    "PlayHistoryObject",
    "QueueObject",
    # Playlist
    "PlaylistTrackObject",
    # Saved Objects
    "SavedTrackObject",
    "SavedAlbumObject",
    "SavedShowObject",
    "SavedEpisodeObject",
    "SavedAudiobookObject",
    # Recommendations
    "RecommendationsObject",
    "RecommendationSeedObject",
    # Copyright
    "CopyrightObject",
    # Resume Point
    "ResumePointObject",
    # Linked Track
    "LinkedTrackObject",
    # Time Interval
    "TimeIntervalObject",
    # Cursor
    "CursorObject",
    # Disallows
    "DisallowsObject",
    # Narrator and Author
    "NarratorObject",
    "AuthorObject",
    # Audiobooks and Chapters
    "AudiobookObject",
    "ChapterObject",
    # Categories
    "CategoryObject",
    # Section and Segment
    "SectionObject",
    "SegmentObject",
    # Playlist User/Owner
    "PlaylistUserObject",
    "PlaylistOwnerObject",
    # Playlist Tracks Reference
    "PlaylistTracksRefObject",
    # Explicit Content Settings
    "ExplicitContentSettingsObject",
    # Paging variants
    "PagingTrackObject",
    "PagingArtistObject",
    "PagingPlaylistObject",
    "PagingPlaylistTrackObject",
    "PagingSavedTrackObject",
    "PagingSavedAlbumObject",
    "PagingSavedShowObject",
    "PagingSavedEpisodeObject",
    "PagingSimplifiedTrackObject",
    "PagingSimplifiedAlbumObject",
    "PagingSimplifiedShowObject",
    "PagingSimplifiedAudiobookObject",
    "PagingSimplifiedEpisodeObject",
    "PagingSimplifiedChapterObject",
    "PagingArtistDiscographyAlbumObject",
    "PagingSavedAudiobookObject",
    "CursorPagingSimplifiedArtistObject",
    "CursorPagingPlayHistoryObject",
    # Featured playlists
    "PagingFeaturedPlaylistObject",
    # Discography
    "ArtistDiscographyAlbumObject",
    # Enums and other types
    "Reason",
    "Type",
    "Mode1",
    "Pitch",
]
