import os
from pathlib import Path

import spotipy
from dotenv import load_dotenv
from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyPKCE
from time import monotonic,sleep
from script_tools import open_app

PROJECT_DIR = Path(__file__).resolve().parent

SCOPES = " ".join([
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-library-read",
    "playlist-read-private",
    "playlist-read-collaborative",
])

_client = None
_ducked_playback = None

CONVERSATION_VOLUME = 10

def get_spotify() -> spotipy.Spotify:
    """Create one Spotify client and reuse it."""
    global _client

    if _client is None:
        load_dotenv(PROJECT_DIR / ".env")

        client_id = os.getenv("SPOTIFY_CLIENT_ID")

        redirect_uri = os.getenv(
            "SPOTIFY_REDIRECT_URI",
            "http://127.0.0.1:8888/callback",
        )

        if not client_id:
            raise RuntimeError(
                "Missing SPOTIFY_CLIENT_ID in the .env file."
            )

        cache_dir = (
            Path(os.environ["LOCALAPPDATA"])
            / "JarvisAssistant"
        )

        cache_dir.mkdir(parents=True, exist_ok=True)

        auth_manager = SpotifyPKCE(
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=SCOPES,
            cache_handler=CacheFileHandler(
                cache_path=str(
                    cache_dir / "spotify_token.json"
                )
            ),
            open_browser=True,
        )

        _client = spotipy.Spotify(
            auth_manager=auth_manager,
            requests_timeout=10,
        )

    return _client

def spotify_now_playing() -> str:
    """Get the current Spotify track and playback status."""
    playback = get_spotify().current_playback()

    if not playback:
        return "Nothing is currently playing on Spotify."

    item = playback.get("item")

    if not item:
        return "Spotify did not provide the current track."

    if playback.get("currently_playing_type") != "track":
        return "The current Spotify item is not a music track."

    title = item.get("name", "Unknown track")

    artists = ", ".join(
        artist["name"]
        for artist in item.get("artists", [])
    ) or "Unknown artist"

    if playback.get("is_playing"):
        return f"{title} by {artists}."

    return f"Playing {title} by {artists}."

PREFERRED_SPOTIFY_DEVICE = "DESKTOP-K641TTQ"
SPOTIFY_SHORTCUT = "Spotify.lnk"

def _get_active_device() -> dict:
    """Use an active device or activate the preferred computer."""
    client = get_spotify()
    devices = client.devices().get("devices", [])

    # Zachowujemy dotychczasowe zachowanie, jeśli urządzenie jest aktywne.
    active = next(
        (
            device
            for device in devices
            if device.get("is_active")
        ),
        None,
    )

    if active is not None:
        if active.get("is_restricted"):
            raise RuntimeError(
                "The active Spotify device does not allow API control."
            )

        if not active.get("id"):
            raise RuntimeError("Spotify did not provide a device ID.")

        return active

    # Brak aktywnego urządzenia: szukamy naszego komputera.
    preferred = next(
        (
            device
            for device in devices
            if device.get("name", "").casefold()
            == PREFERRED_SPOTIFY_DEVICE.casefold()
        ),
        None,
    )

    if preferred is None:
        print("[Spotify] Opening application...")

        launch_result = open_app(SPOTIFY_SHORTCUT)
        print(f"[Spotify] {launch_result}")

        # Czekamy na pojawienie się komputera w Spotify API.
        # Kończymy od razu, gdy urządzenie będzie dostępne.
        deadline = monotonic() + 15

        while monotonic() < deadline:
            sleep(1)

            devices = client.devices().get("devices", [])

            preferred = next(
                (
                    device
                    for device in devices
                    if device.get("name", "").casefold()
                    == PREFERRED_SPOTIFY_DEVICE.casefold()
                ),
                None,
            )

            if preferred is not None:
                break

        if preferred is None:
            raise RuntimeError(
                "Spotify was asked to open, but this computer "
                "did not become available in time. "
                "Check that Spotify is running and signed in."
            )

    if preferred.get("is_restricted") or not preferred.get("id"):
        raise RuntimeError(
            "The preferred Spotify device does not allow API control."
        )

    device_id = preferred["id"]

    print(f"[Spotify] Activating: {preferred['name']}")

    client.transfer_playback(
        device_id=device_id,
        force_play=False,
    )

    # Transfer nie musi zakończyć się natychmiast.
    # Czekamy maksymalnie około 5 sekund, nie licząc czasu żądań HTTP.
    deadline = monotonic() + 5

    while monotonic() < deadline:
        sleep(0.5)

        devices = client.devices().get("devices", [])

        activated = next(
            (
                device
                for device in devices
                if device.get("id") == device_id
                and device.get("is_active")
                and not device.get("is_restricted")
            ),
            None,
        )

        if activated is not None:
            return activated

    raise RuntimeError(
        "Spotify did not activate the computer in time. Try again."
    )


def spotify_next_track() -> str|None:
    """Skip to the next track on the active Spotify device."""
    device = _get_active_device()

    get_spotify().next_track(device_id=device["id"])

    return None


def spotify_previous_track() -> str|None:
    """Request the previous track on the active Spotify device."""
    device = _get_active_device()

    get_spotify().previous_track(device_id=device["id"])

    return None

def _set_music_volume(device: dict, target_volume: int) -> None:
    """Set music volume and update the conversation restore level."""
    client = get_spotify()

    client.volume(
        target_volume,
        device_id=device["id"],
    )

    # Aktualizujemy zapis dopiero po udanym żądaniu API.
    if (
        _ducked_playback is not None
        and _ducked_playback["device_id"] == device["id"]
    ):
        _ducked_playback["original_volume"] = target_volume

        # Muzyka jest już na docelowym poziomie.
        # Restore może bezpiecznie rozpoznać ten stan.
        _ducked_playback["quiet_volume"] = target_volume

    print(f"[Spotify] Music volume: {target_volume}%")


def spotify_set_volume(volume_percent: int) -> str | None:
    """Set normal Spotify music volume to an exact percentage.

    Args:
        volume_percent: Integer volume from 0 to 100.
    """
    if type(volume_percent) is not int:
        return "Volume must be a whole number from 0 to 100."

    if not 0 <= volume_percent <= 100:
        return "Volume must be between 0 and 100 percent."

    device = _get_active_device()

    if not device.get("supports_volume"):
        return "The active Spotify device does not support volume control."

    _set_music_volume(device, volume_percent)

    return None


def spotify_adjust_volume(change_percent: int) -> str | None:
    """Change normal Spotify music volume by percentage points.

    Temporary conversation ducking is excluded from the calculation.

    Args:
        change_percent: Signed integer change, such as 10 or -10.
    """
    if type(change_percent) is not int:
        return "The volume change must be a whole number."

    if not -100 <= change_percent <= 100:
        return "The volume change must be between -100 and 100."

    device = _get_active_device()

    if not device.get("supports_volume"):
        return "The active Spotify device does not support volume control."

    if (
        _ducked_playback is not None
        and _ducked_playback["device_id"] == device["id"]
    ):
        # Liczymy od poziomu muzyki sprzed ściszenia.
        current_volume = _ducked_playback["original_volume"]
    else:
        current_volume = device.get("volume_percent")

    if current_volume is None:
        return "Spotify did not provide the current volume."

    target_volume = max(
        0,
        min(100, current_volume + change_percent),
    )

    _set_music_volume(device, target_volume)

    return None
def duck_spotify() -> None:
    """Lower Spotify volume for the conversation, remembering its level."""
    global _ducked_playback

    # Nie zapisujemy ściszonego poziomu jako nowej głośności początkowej.
    if _ducked_playback is not None:
        return

    try:
        client = get_spotify()
        playback = client.current_playback()

        if not playback or not playback.get("is_playing"):
            return

        device = playback.get("device") or {}

        device_id = device.get("id")
        original_volume = device.get("volume_percent")

        if (
            not device_id
            or original_volume is None
            or not device.get("supports_volume")
            or device.get("is_restricted")
        ):
            return

        quiet_volume = min(original_volume, CONVERSATION_VOLUME)

        if quiet_volume == original_volume:
            return

        client.volume(
            quiet_volume,
            device_id=device_id,
        )

        _ducked_playback = {
            "device_id": device_id,
            "original_volume": original_volume,
            "quiet_volume": quiet_volume,
        }

        print(
            f"[Spotify] Conversation volume: "
            f"{original_volume}% -> {quiet_volume}%"
        )

    except Exception as error:
        # Problem Spotify nie powinien blokować rozmowy.
        print(f"[Spotify] Could not lower music volume: {error}")


def restore_spotify_volume() -> None:
    """Restore volume unless it was changed during the conversation."""
    global _ducked_playback

    if _ducked_playback is None:
        return

    saved = _ducked_playback

    try:
        client = get_spotify()
        devices = client.devices().get("devices", [])

        device = next(
            (
                device
                for device in devices
                if device.get("id") == saved["device_id"]
            ),
            None,
        )

        if device is None:
            print("[Spotify] Original device is no longer available.")
            return

        # Zachowujemy zmianę dokonaną przez użytkownika podczas rozmowy.
        if device.get("volume_percent") != saved["quiet_volume"]:
            print("[Spotify] Volume changed during conversation; keeping it.")
            return

        client.volume(
            saved["original_volume"],
            device_id=saved["device_id"],
        )

        print(
            f"[Spotify] Volume restored to "
            f"{saved['original_volume']}%"
        )

    except Exception as error:
        print(f"[Spotify] Could not restore music volume: {error}")

    finally:
        _ducked_playback = None

def spotify_play() -> str | None:
    """Resume music playback on Spotify.

    Use for "play music", "resume music", or "resume Spotify".
    This does not open or launch the Spotify application.
    For a named song or playlist, use the corresponding playback tool.
    """
    device = _get_active_device()

    get_spotify().start_playback(
        device_id=device["id"],
    )

    return None


def spotify_pause() -> str|None:
    """Pause current Spotify playback, preserving its position."""
    device = _get_active_device()

    get_spotify().pause_playback(
        device_id=device["id"],
    )

    return None

def spotify_play_track(
    track_name: str,
    artist_name: str = "",
) -> str | None:
    """Find and play a Spotify song by title and optional artist.

    Args:
        track_name: Song title, without the artist name.
        artist_name: Artist or band name, if specified by the user.
    """
    track_name = track_name.strip()
    artist_name = artist_name.strip()

    if not track_name:
        return "Please specify a song title."

    # Usuwamy podwójne cudzysłowy, żeby nie zaburzały zapytania.
    title = track_name.replace('"', " ")
    artist = artist_name.replace('"', " ")

    query = f'track:"{title}"'

    if artist:
        query += f' artist:"{artist}"'

    client = get_spotify()

    response = client.search(
        q=query,
        type="track",
        limit=5,
    )

    tracks = (response.get("tracks") or {}).get("items") or []

    # Pomijamy wyniki, których Spotify jawnie nie pozwala odtworzyć.
    tracks = [
        track
        for track in tracks
        if track
        and track.get("uri")
        and track.get("is_playable") is not False
    ]

    if not tracks:
        description = (
            f"{track_name} by {artist_name}"
            if artist_name
            else track_name
        )
        return f"I couldn't find a playable track matching {description}."

    # W tej wersji wybieramy pierwszy pasujący wynik Spotify.
    selected = tracks[0]

    device = _get_active_device()

    album_uri = (selected.get("album") or {}).get("uri")

    if not album_uri:
        return "Spotify did not provide the album for this track."

    client.start_playback(
        device_id=device["id"],
        context_uri=album_uri,
        offset={"uri": selected["uri"]},
        position_ms=0,
)


    artists = ", ".join(
        artist["name"]
        for artist in selected.get("artists", [])
    )

    return None


def _normalize_spotify_name(value: str) -> str:
    """Compare names without case differences or repeated spaces."""
    return " ".join(value.casefold().split())


def spotify_play_playlist(playlist_name: str) -> str | None:
    """Play a playlist from the user's Spotify library by name.

    Args:
        playlist_name: Name of a playlist owned or followed by the user.
    """
    playlist_name = playlist_name.strip()

    if not playlist_name:
        return "Please specify a playlist name."

    client = get_spotify()
    playlists = []

    page = client.current_user_playlists(limit=50)

    # API zwraca playlisty stronami, więc pobieramy również kolejne strony.
    while page:
        playlists.extend(
            playlist
            for playlist in page.get("items", [])
            if playlist and playlist.get("uri")
        )

        if not page.get("next"):
            break

        page = client.next(page)

    requested = _normalize_spotify_name(playlist_name)

    # Najpierw szukamy dokładnej nazwy.
    matches = [
        playlist
        for playlist in playlists
        if _normalize_spotify_name(playlist["name"]) == requested
    ]

    # Jeśli nie ma dokładnej nazwy, dopuszczamy jej fragment.
    if not matches:
        matches = [
            playlist
            for playlist in playlists
            if requested in _normalize_spotify_name(playlist["name"])
        ]

    if not matches:
        return f"I couldn't find {playlist_name} in your Spotify playlists."

    if len(matches) > 1:
        names = "; ".join(
            dict.fromkeys(playlist["name"] for playlist in matches)
        )

        return (
            f"Several playlists match: {names}. "
            "Please use a unique playlist name."
        )

    selected = matches[0]
    device = _get_active_device()

    client.start_playback(
        device_id=device["id"],
        context_uri=selected["uri"],
        offset={"position": 0},
    )

    print(f"[Spotify] Selected playlist: {selected['name']}")

    return None


def spotify_play_liked_songs() -> str | None:
    """Report that Liked Songs playback is not available in version 1.0."""
    return (
        "Liked Songs playback is not available in this version. "
        "Please request a song or a named playlist."
    )

if __name__ == "__main__":
    print("Connecting to Spotify...")
    print(spotify_now_playing())