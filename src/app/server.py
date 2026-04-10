import os
import queue
import urllib.parse
import threading
import webbrowser
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

try:
    import mpv
    mpv_config_dir = os.path.join(os.environ.get('APPDATA', ''), 'mpv')
    
    player = mpv.MPV(
        ytdl=True, 
        input_default_bindings=True, 
        input_vo_keyboard=True,
        config=True,
        config_dir=mpv_config_dir,
        load_scripts=True,
        osc=False
    )
except Exception as e:
    player = None
    print(f"Warning: Failed to initialize mpv player ({e}). Video playback tools will not work.")

_player_queue: queue.Queue = queue.Queue()

def _player_worker():
    """Persistent background thread that processes all player commands sequentially."""
    while True:
        fn = _player_queue.get()
        if fn is None:
            break
        try:
            fn()
        except Exception as e:
            print(f"Player worker error: {e}")
        finally:
            _player_queue.task_done()

_worker_thread = threading.Thread(target=_player_worker, daemon=True)
_worker_thread.start()

def enqueue_player_cmd(fn):
    """Submit a callable to the player worker queue."""
    _player_queue.put(fn)

load_dotenv()

mcp = FastMCP("YouTube MCP Server")

def get_youtube_client():
    """Helper to get the authenticated YouTube Data API client."""
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY environment variable is not set. Please set it to use the YouTube API.")
    return build('youtube', 'v3', developerKey=api_key)

def extract_video_id(url_or_id: str) -> str:
    """Extracts the video ID from a YouTube URL, or returns the string if it's already an ID."""
    if "youtu.be" in url_or_id or "youtube.com" in url_or_id:
        parsed_url = urllib.parse.urlparse(url_or_id)
        if parsed_url.netloc == "youtu.be":
            return parsed_url.path[1:]
        if parsed_url.netloc in ("www.youtube.com", "youtube.com", "m.youtube.com", "music.youtube.com"):
            if parsed_url.path == "/watch":
                query_params = urllib.parse.parse_qs(parsed_url.query)
                return query_params.get("v", [url_or_id])[0]
            if parsed_url.path.startswith("/embed/"):
                return parsed_url.path.split("/")[2]
            if parsed_url.path.startswith("/v/"):
                return parsed_url.path.split("/")[2]
            if parsed_url.path.startswith("/shorts/"):
                return parsed_url.path.split("/")[2]
    return url_or_id

@mcp.tool()
def search_youtube(query: str, limit: int = 5) -> str:
    """Search for YouTube videos by query using the official YouTube Data API."""
    try:
        youtube = get_youtube_client()
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=limit
        )
        response = request.execute()
        
        output = []
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            channel = item["snippet"]["channelTitle"]
            link = f"https://www.youtube.com/watch?v={video_id}"
            output.append(f"- {title} | Channel: {channel} | URL: {link}")
            
        return "\n".join(output) if output else "No results found."
    except Exception as e:
        return f"Error searching YouTube: {str(e)}"

@mcp.tool()
def search_and_play(query: str) -> str:
    """
    Search YouTube for a song/video and immediately play the top result in MPV.

    WHEN TO USE:
    - ALWAYS use this when the user asks to "play [song/video name]".
    - Prefer this over calling search_youtube + play_video_mpv separately.

    USAGE INSTRUCTIONS:
    - Pass the song or video name as `query`.
    - This tool handles everything: search, pick best result, and play — in one call.
    - Returns instantly. MPV will start playing within a few seconds in the background.
    """
    if player is None:
        return "Error: MPV player is not initialized."
    try:
        youtube = get_youtube_client()
        response = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=1
        ).execute()

        items = response.get("items", [])
        if not items:
            return f"No results found for: {query}"

        item = items[0]
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        channel = item["snippet"]["channelTitle"]
        url = f"https://www.youtube.com/watch?v={video_id}"

        def _force_play():
            try:
                player.command('stop')
            except Exception:
                pass
            player.play(url)

        enqueue_player_cmd(_force_play)
        return f"Now playing: {title} by {channel}\n{url}"
    except Exception as e:
        return f"Error in search_and_play: {str(e)}"

@mcp.tool()
def get_video_details(video_id: str) -> str:
    """Get detailed information about a YouTube video including view count, likes, and full description."""
    try:
        vid = extract_video_id(video_id)
        youtube = get_youtube_client()
        request = youtube.videos().list(
            part="snippet,statistics",
            id=vid
        )
        response = request.execute()
        
        items = response.get("items", [])
        if not items:
            return "Video not found."
            
        item = items[0]
        snippet = item["snippet"]
        stats = item["statistics"]
        
        details = (
            f"Title: {snippet['title']}\n"
            f"Channel: {snippet['channelTitle']}\n"
            f"Published: {snippet['publishedAt']}\n"
            f"Views: {stats.get('viewCount', 'N/A')}\n"
            f"Likes: {stats.get('likeCount', 'N/A')}\n"
            f"Comment Count: {stats.get('commentCount', 'N/A')}\n"
            f"\nDescription:\n{snippet['description']}"
        )
        return details
    except Exception as e:
        return f"Error fetching video details: {str(e)}"

@mcp.tool()
def get_transcript(video_id: str) -> str:
    """Get the transcript of a YouTube video as soon as it's been played.
    Use this transcript to summarize the video.
    Note: This does not use your API key as the official API restricts transcript access.
    """
    try:
        vid = extract_video_id(video_id)
        transcript_list = YouTubeTranscriptApi.get_transcript(vid)
        full_text = " ".join([item['text'] for item in transcript_list])
        return full_text
    except Exception as e:
        return f"Error fetching transcript: {str(e)}\nNote: Many videos do not have English transcripts or have disabled them."

@mcp.tool()
def open_videor(video_id: str) -> str:
    """Open a YouTube video URL in the default web browser to start playing it."""
    try:
        vid = extract_video_id(video_id)
        url = f"https://www.youtube.com/watch?v={vid}"
        webbrowser.open(url)
        return f"Successfully opened {url} in the default browser."
    except Exception as e:
        return f"Error opening browser: {str(e)}"

@mcp.tool()
def play_video_mpv(video_id: str) -> str:
    """Play a YouTube video locally using mpv."""
    if player is None:
        return "Error: MPV player is not initialized. Ensure mpv is installed on your system."
    try:
        vid = extract_video_id(video_id)
        url = f"https://www.youtube.com/watch?v={vid}"
        
        def _force_play2():
            try:
                player.command('stop')
            except Exception:
                pass
            player.play(url)
            
        enqueue_player_cmd(_force_play2)
        return f"Playing {url}"
    except Exception as e:
        return f"Error playing video: {str(e)}"

@mcp.tool()
def pause_resume_video() -> str:
    """Pause or resume the currently playing video in mpv."""
    if player is None:
        return "Error: MPV player is not initialized."
    try:
        def _toggle():
            if not getattr(player, 'idle_active', True):
                player.pause = not player.pause
        enqueue_player_cmd(_toggle)
        return "Toggle playback command sent."
    except Exception as e:
        return f"Error toggling playback state: {str(e)}"

@mcp.tool()
def seek_video(seconds: int) -> str:
    """Seek the currently playing video forward or backward by a specific number of seconds (e.g. 10 or -10)."""
    if player is None:
        return "Error: MPV player is not initialized."
    try:
        enqueue_player_cmd(lambda: player.seek(seconds) if not getattr(player, 'idle_active', True) else None)
        direction = "forward" if seconds > 0 else "backward"
        return f"Seek {direction} by {abs(seconds)} seconds command sent."
    except Exception as e:
        return f"Error seeking video: {str(e)}"

@mcp.tool()
def playlist_next() -> str:
    """Skip to the next video in the mpv playlist. Works even just by saying next."""
    if player is None:
        return "Error: MPV player is not initialized."
    try:
        enqueue_player_cmd(lambda: player.playlist_next() if not getattr(player, 'idle_active', True) else None)
        return "Skip to next video command sent."
    except Exception as e:
        return f"Error skipping to next video: {str(e)}"

@mcp.tool()
def playlist_prev() -> str:
    """Skip to the previous video in the mpv playlist."""
    if player is None:
        return "Error: MPV player is not initialized."
    try:
        enqueue_player_cmd(lambda: player.playlist_prev() if not getattr(player, 'idle_active', True) else None)
        return "Skip to previous video command sent."
    except Exception as e:
        return f"Error skipping to previous video: {str(e)}"

@mcp.tool()
def stop_video() -> str:
    """Stop the current video playback and clear the playlist."""
    if player is None:
        return "Error: MPV player is not initialized."
    try:
        enqueue_player_cmd(lambda: player.command('stop'))
        return "Stop video command sent."
    except Exception as e:
        return f"Error stopping video: {str(e)}"

@mcp.tool()
def enqueue_video(query_or_url: str) -> str:
    """Add a YouTube video to the queue securely by searching for it or passing a URL."""
    if player is None:
        return "Error: MPV player is not initialized."
    try:
        if "youtu.be" in query_or_url or "youtube.com" in query_or_url:
            vid = extract_video_id(query_or_url)
            url = f"https://www.youtube.com/watch?v={vid}"
            enqueue_player_cmd(lambda: player.loadfile(url, mode='append-play'))
            return f"Queued URL: {url}"
        else:
            youtube = get_youtube_client()
            response = youtube.search().list(part="snippet", q=query_or_url, type="video", maxResults=1).execute()
            items = response.get("items", [])
            if not items:
                return f"No results found for: {query_or_url}"
            item = items[0]
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={video_id}"
            enqueue_player_cmd(lambda: player.loadfile(url, mode='append-play'))
            return f"Queued: {title}\n{url}"
    except Exception as e:
        return f"Error queuing video: {str(e)}"

@mcp.tool()
def set_loop(mode: str) -> str:
    """Set the looping behavior of the MPV player (file, playlist, or none)."""
    if player is None:
        return "Error: Player not initialized."
    try:
        m = mode.lower()
        if m not in ['file', 'playlist', 'none']:
            return "Invalid mode. Use 'file', 'playlist', or 'none'."
        def _set_loop():
            if m == 'file':
                player.loop_file = 'inf'
                player.loop_playlist = 'no'
            elif m == 'playlist':
                player.loop_file = 'no'
                player.loop_playlist = 'inf'
            elif m == 'none':
                player.loop_file = 'no'
                player.loop_playlist = 'no'
        enqueue_player_cmd(_set_loop)
        return f"Loop mode {m} command sent."
    except Exception as e:
        return f"Error setting loop mode: {str(e)}"

@mcp.tool()
def set_playback_speed(speed: float) -> str:
    """Set the playback speed (e.g. 1.0, 1.5, 2.0)."""
    if player is None:
        return "Error: Player not initialized."
    try:
        enqueue_player_cmd(lambda: setattr(player, 'speed', float(speed)))
        return f"Set playback speed to {speed}x command sent."
    except Exception as e:
        return f"Error setting playback speed: {str(e)}"

@mcp.tool()
def set_volume(level: int) -> str:
    """Set the playback volume level (0 to 100)."""
    if player is None:
        return "Error: MPV player is not initialized."
    try:
        level = max(0, min(100, int(level)))
        enqueue_player_cmd(lambda: setattr(player, 'volume', level))
        return f"Set volume to {level}% command sent."
    except Exception as e:
        return f"Error setting volume: {str(e)}"

if __name__ == "__main__":
    mcp.run()