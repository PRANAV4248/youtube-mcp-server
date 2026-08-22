# 🎵 YouTube MCP Server: The Ultimate Media Controller

An MCP server for YouTube video playback control, search, and analytics.

Most YouTube MCP servers stop at just searching videos, extracting metadata, or fetching transcripts. **This one goes infinitely further.**

This MCP server transforms Claude Desktop (or any MCP client) into your personal, interactive media center. Not only does it seamlessly pull metadata and transcripts, but it provides full playback control giving you the ability to **play, pause, seek, loop, queue and summarize i.e. not just single videos, but entire playlists**, directly on your local machine with native hardware acceleration.

---

## 🎬 Demo: MCP Server in Action

Watch how to control your media simply by talking to Claude in natural language.

<video src="Youtube%20MCP%20demo.mp4" controls="controls" style="max-width: 100%;">
  Your browser does not support the video tag.
</video>

*(If the video player doesn't render in your markdown viewer, you can view the video file directly: [`Youtube MCP demo.mp4`](<./Youtube%20MCP%20demo.mp4>))*

> **Video Credits:** *Sapphire* by Ed Sheeran and Arijit Singh, and podcast by Nikhil Kamath.

---

## 🌟 Features

- **True Native Playback Control**: Tell Claude to *"pause the music," "skip to the next video," "seek forward 30 seconds,"* or *"loop this track."* Claude commands the local `mpv` player instantaneously.
- **HiDPI & Full-Screen Ready**: Built-in Windows Per-Monitor DPI awareness and automatic scaling so the player matches your laptop's native screen resolution (1080p, 2K, 4K).
- **Clean Window Management**: Resizable, non-locking aspect ratio with safe close handling (`[X]` stops playback cleanly without freezing the server).
- **Custom Theme Compatible**: Fully compatible with custom `mpv` scripts and OSC themes (like `ModernZ`).
- **Dynamic Playlist & Queue Management**: Have Claude build a playlist for you on the fly (*"Add the top 3 tech news videos to my queue"*). The MCP securely enqueues URLs in the background and plays them sequentially.
- **Deep Video Research**: Beyond playing media, ask Claude to *"summarize the latest video."* It extracts the full English transcript and analyzes it for you in seconds.
- **Analytics & Metadata**: Prompt Claude for granular details on any video: view count, exact likes, comment counts, and full description.

---

## 🛠️ Prerequisites

Before you start, make sure you have the following installed:

1. **Claude Desktop**: [Download it for free here](https://claude.ai/download) (or any MCP client like Cursor / Cline / Gemini).
2. **Python 3.12+**
3. **[uv](https://docs.astral.sh/uv/)**: Fast Python package installer and resolver.
4. **`mpv`**: The versatile media player (and `libmpv`). *See setup instructions below.*
5. **Google Cloud Account**: To generate a free API key for YouTube Data API v3.

---

## ⚙️ Setup & Installation

### 1. MPV Setup (Required for Playback)

The local video streaming is powered by `python-mpv`, which hooks directly into the underlying C library of the `mpv` media player.

#### Windows Setup

For visual instructions, refer to this detailed YouTube tutorial:
▶️ [MPV Installation Guide](https://youtu.be/wj9_gCack68?si=ElkJIZr0zg5hwlid)

> ⚠️ **Important Note**: You need **both** the normal MPV player installed AND the MPV dev library (`mpv-2.dll` or `libmpv-2.dll`).

1. **Download**: Go to [shinchiro&#39;s mpv-windows builds](https://sourceforge.net/projects/mpv-player-windows/files/libmpv/) and download the latest archive containing `mpv-2.dll` / `libmpv-2.dll`.
2. **Extract & Move**: Move the extracted `.dll` file directly into your `C:\Program Files\mpv\` directory.
3. **System Path**: Add `C:\Program Files\mpv` to your system's global `PATH` environment variable.

> *Alternatively, install with [scoop](https://scoop.sh/): `scoop install mpv`*

#### macOS:

```bash
brew install mpv
```

#### Linux (Debian/Ubuntu):

```bash
sudo apt install libmpv-dev mpv
```

---

### 2. YouTube API Key Setup

To enable YouTube search and metadata extraction:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Navigate to **APIs & Services** > **Library** and search for **YouTube Data API v3**. Enable it.
4. Go to **Credentials**, click **Create Credentials**, and choose **API Key**.
5. Copy your new API key.

---

### 3. Clone & Initialize

Clone the repository and create your `.env` file at the root:

```bash
git clone https://github.com/PRANAV4248/youtube-mcp-server.git
cd youtube-mcp-server
echo YOUTUBE_API_KEY=your_api_key_here > .env
```

Install dependencies with `uv`:

```bash
uv sync
```

---

## 🔌 Connecting to Claude Desktop (MCP Setup)

Add the server configuration to your `claude_desktop_config.json`:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "youtube-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "C:\\FILES\\Documents\\Coding\\Codespace\\Python\\Project\\YoutubeMCP",
        "python",
        "src/app/server.py"
      ],
      "env": {
        "YOUTUBE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

> 💡 *Replace the `--directory` path with the absolute path where you cloned the project.*

Restart Claude Desktop. You should now see the YouTube tools available in your chat!

---

## 🧰 Available Tools for Claude

### 🔍 Search & Data

- `search_youtube(query, limit)`: Search YouTube for top videos matching a query.
- `get_video_details(video_id)`: Fetches views, likes, comments, and full description.
- `get_transcript(video_id)`: Extracts spoken captions/transcripts.
- `open_video(video_id)`: Opens the video in the default web browser.

### 🎵 Playback & Control (MPV)

- `search_and_play(query)`: Finds the top video and plays it immediately in the native player.
- `play_video_mpv(video_id)`: Plays a specific video ID or URL.
- `pause_resume_video()`: Toggles playback pause/resume.
- `seek_video(seconds)`: Seeks forward or backward by a specified number of seconds.
- `playlist_next()` / `playlist_prev()`: Jumps between queued tracks.
- `stop_video()`: Stops playback and clears the playlist.
- `enqueue_video(query_or_url)`: Appends a video to the current playlist.
- `set_loop(mode)`: Set looping (`file`, `playlist`, or `none`).
- `set_playback_speed(speed)`: Adjust playback speed (0.25x - 4.0x).
- `set_volume(level)`: Adjust volume (0 - 100).

---

## ⚠️ Known Notes

- **Transcripts**: Transcript extraction uses `youtube-transcript-api`. If a video has subtitles disabled by the creator or lacks captions, the tool will return a friendly notification.
- **Windows Library Bindings**: Ensure `mpv-2.dll` or `libmpv-2.dll` is in `C:\Program Files\mpv` and added to your `PATH`.

---

**Created by - Pranav Choubey**
Reach me out on - [LinkedIn](https://www.linkedin.com/in/pranav-choubey)
