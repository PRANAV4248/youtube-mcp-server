import ctypes
import os
import re
import webbrowser
from dotenv import load_dotenv
from googleapiclient.discovery import build
from mcp.server import MCPServer
from youtube_transcript_api import YouTubeTranscriptApi

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

load_dotenv()
mcp = MCPServer("YouTube MCP Server")

# Initialize mpv player
player = None

def get_player():
    global player
    try:
        if player and player.idle_active is not None:
            return player
    except Exception:
        pass
    try:
        import mpv
        player = mpv.MPV(ytdl=True, input_default_bindings=True, input_vo_keyboard=True, config=True, load_scripts=True, osc=False, hidpi_window_scale=True, keepaspect_window=False, autofit="100%x100%")
        try:
            player.command("keybind", "CLOSE_WIN", "stop")
            player.command("keybind", "q", "stop")
        except Exception:
            pass
        return player
    except Exception:
        return None

# Helper functions

def yt():
    """Return an authenticated YouTube Data API client."""
    return build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))

def get_id(text: str) -> str:
    """Extract the 11-character video ID from a URL or raw ID."""
    match = re.search(r"(?:v=|\/embed\/|\/shorts\/|youtu\.be\/|^)([A-Za-z0-9_-]{11})(?:[?&#]|$)", text.strip())
    return match.group(1) if match else text.strip()

def get_url(text: str) -> str:
    """Get a playable YouTube URL from a video ID, URL, or search query."""
    if "youtu" in text or re.fullmatch(r"[A-Za-z0-9_-]{11}", text.strip()):
        return f"https://www.youtube.com/watch?v={get_id(text)}"

    # If it's a search term, find the top video match
    res = yt().search().list(q=text, part="snippet", type="video", maxResults=1).execute()
    items = res.get("items", [])
    if not items:
        raise LookupError(f"No results found for: {text}")
    return f"https://www.youtube.com/watch?v={items[0]['id']['videoId']}"

def player_action(fn, msg: str = "Success") -> str:
    """Safely execute an action on the mpv player instance."""
    player = get_player()
    if not player:
        return "Error: MPV player is not initialized. Ensure mpv is installed on this system."
    try:
        fn(player)
        return msg
    except Exception as e:
        return f"Error: {e}"

# YouTube Data Tools

@mcp.tool()
def search_youtube(query: str, limit: int = 5) -> str:
    """Search for YouTube videos by query using the official YouTube Data API."""
    try:
        res = yt().search().list(q=query, part="snippet", type="video", maxResults=limit).execute()
        lines = [
            f"- {i['snippet']['title']} | Channel: {i['snippet']['channelTitle']} | https://youtu.be/{i['id']['videoId']}"
            for i in res.get("items", [])
        ]
        return "\n".join(lines) or "No results found."
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_video_details(video_id: str) -> str:
    """Get detailed information about a YouTube video including view count, likes, and full description."""
    try:
        vid = get_id(video_id)
        res = yt().videos().list(id=vid, part="snippet,statistics").execute()
        items = res.get("items", [])
        if not items:
            return "Video not found."
        s, st = items[0]["snippet"], items[0]["statistics"]
        return (
            f"Title: {s['title']}\n"
            f"Channel: {s['channelTitle']}\n"
            f"Published: {s['publishedAt']}\n"
            f"Views: {st.get('viewCount', 'N/A')} | Likes: {st.get('likeCount', 'N/A')} | Comments: {st.get('commentCount', 'N/A')}\n\n"
            f"Description:\n{s['description']}"
        )
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_transcript(video_id: str) -> str:
    """Get the text transcript/captions/summary of a YouTube video."""
    try:
        transcript = YouTubeTranscriptApi().fetch(get_id(video_id))
        return " ".join(s.text for s in transcript)
    except Exception as e:
        return f"Error fetching transcript: {e}\nNote: many videos don't have English transcripts."

@mcp.tool()
def open_video(video_id: str) -> str:
    """Open a YouTube video in the default web browser."""
    try:
        url = get_url(video_id)
        webbrowser.open(url)
        return f"Opened {url} in the default browser."
    except Exception as e:
        return f"Error: {e}"

# Playback Tools (mpv)

@mcp.tool()
def search_and_play(query: str) -> str:
    """Search YouTube and immediately play the top result locally in mpv. Try to play video songs if available instead of lyrical songs. Use this for 'play [song/video]' requests."""
    try:
        url = get_url(query)
        return player_action(lambda player: player.play(url), f"Now playing: {url}")
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def play_video_mpv(video_id: str) -> str:
    """Play a specific YouTube video (URL or ID) locally using mpv."""
    return search_and_play(video_id)

@mcp.tool()
def pause_resume_video() -> str:
    """Pause or resume the currently playing video."""
    return player_action(lambda player: setattr(player, "pause", not player.pause), "Toggled playback pause/resume.")

@mcp.tool()
def seek_video(seconds: int) -> str:
    """Seek forward/backward in the current video by a number of seconds (e.g. 10 or -10)."""
    return player_action(lambda player: player.seek(seconds), f"Seeked {seconds} seconds.")

@mcp.tool()
def playlist_next() -> str:
    """Skip to the next video in the mpv playlist."""
    return player_action(lambda player: player.playlist_next(), "Skipped to next video.")

@mcp.tool()
def playlist_prev() -> str:
    """Skip to the previous video in the mpv playlist."""
    return player_action(lambda player: player.playlist_prev(), "Skipped to previous video.")

@mcp.tool()
def stop_video() -> str:
    """Stop playback and clear the mpv playlist."""
    return player_action(lambda player: player.command("stop"), "Playback stopped.")

@mcp.tool()
def enqueue_video(query_or_url: str) -> str:
    """Add a YouTube video to the mpv playlist by searching for it or passing a URL/ID."""
    try:
        url = get_url(query_or_url)
        return player_action(lambda player: player.loadfile(url, mode="append-play"), f"Queued: {url}")
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def set_loop(mode: str) -> str:
    """Set looping behavior: 'file' (loop current track), 'playlist' (loop playlist), or 'none'."""
    mode = mode.strip().lower()
    if mode not in ("file", "playlist", "none"):
        return "Invalid mode. Use 'file', 'playlist', or 'none'."

    def apply_loop(player):
        player.loop_file = "inf" if mode == "file" else "no"
        player.loop_playlist = "inf" if mode == "playlist" else "no"

    return player_action(apply_loop, f"Loop mode set to '{mode}'.")

@mcp.tool()
def set_playback_speed(speed: float) -> str:
    """Set playback speed, clamped to 0.25x-4.0x."""
    clamped = max(0.25, min(4.0, speed))
    return player_action(lambda player: setattr(player, "speed", clamped), f"Set playback speed to {clamped}x.")

@mcp.tool()
def set_volume(level: int) -> str:
    """Set volume (0-100)."""
    clamped = max(0, min(100, level))
    return player_action(lambda player: setattr(player, "volume", clamped), f"Set volume to {clamped}%.")


if __name__ == "__main__":
    mcp.run()