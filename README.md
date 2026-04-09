# 🎵 YouTube MCP Server: The Ultimate Media Controller

Most YouTube MCP servers stop at just searching videos, extracting metadata, or fetching transcripts. **This one goes infinitely further.**

This MCP server transforms Claude Desktop into your personal, fully interactive media center. Not only does it seamlessly pull metadata and transcripts, but it embeds a native remote control giving you the ability to **play, pause, seek, loop, and queue—not just single videos, but entire playlists**—directly in the background.

---

## 🎬 Demo: MCP server in Action

Watch how to control your media simply by talking to Claude in natural language.

<video src="Youtube%20MCP%20demo.mp4" controls="controls" style="max-width: 100%;">
  Your browser does not support the video tag.
</video>

*(If the video player doesn't render in your markdown viewer, you can view the video file directly: [`Youtube MCP demo.mp4`](./Youtube%20MCP%20demo.mp4))*

> **Video Credits:** *Sapphire* by Ed Sheeran and Arijit Singh, and podcast by Nikhil Kamath.

---

## 🌟 Why This Server Stands Out

- **True Native Playback Control**: Tell Claude to *"pause the music," "skip to the next video," "seek forward 30 seconds,"* or *"loop this track."* Claude commands the local `mpv` player instantaneously.
- **Dynamic Playlist & Queue Management**: Have Claude build a playlist for you on the fly. *"Add the top 3 tech news videos to my queue."* The MCP securely enqueues URLs in the background and plays them sequentially.
- **Zero-Distraction Background Player**: Claude launches audio and video streams invisibly. Ask for background jazz while you work, and the music just starts playing without a browser opening.
- **Deep Video Research**: Beyond playing media, ask Claude to *"summarize the latest MKBHD video."* It searches the video, extracts the full English transcript, and analyzes it for you in seconds.
- **Analytics Check**: Prompt Claude for granular details on any video: view count, exact likes, real comment counts, and the raw description text.

---

## 🛠️ Prerequisites

Before you start, make sure you have the following installed on your system:

1. **Claude Desktop**: [Download it for free here](https://claude.ai/download) if you haven't already. It is required to interface with the MCP server.
2. **Python 3.12+**
3. **[uv](https://docs.astral.sh/uv/)**: Fast Python package installer and resolver.
4. **`mpv`**: The versatile media player (and its accompanying library `libmpv`). *See below for simple setup instructions.*
5. **Google Cloud Account**: To generate a free API key for the YouTube Data API v3.

---

## ⚙️ Setup & Installation

### 1. MPV Setup (Crucial for Video Playback)

The local video streaming is powered by `python-mpv`, which directly hooks into the underlying C library of the `mpv` media player.

**Windows Setup (Manual)**
For visual instructions, refer to this detailed YouTube tutorial:
▶️ [MPV Installation Guide](https://youtu.be/wj9_gCack68?si=ElkJIZr0zg5hwlid)

> ⚠️ **Important Note**: Do not get confused! You need **both** the normal MPV player installed (as shown in the video) AND the MPV dev library (the `.dll` file from the steps below) to use this code.

Follow these short steps to install the library manually:

1. **Download**: Go to [shinchiro&#39;s mpv-windows builds](https://sourceforge.net/projects/mpv-player-windows/files/libmpv/) and download the latest archive containing the library file (which includes `mpv-2.dll` or `libmpv-2.dll`).
2. **Extract**: Extract the downloaded archive.
3. **Move to MPV Folder**: Move the extracted `mpv-2.dll` file directly into your existing `C:\Program Files\mpv\` directory (which was created during the video installation step).
4. **System Path**: Search Windows for "Environment Variables" and add `C:\Program Files\mpv` to your system's global `PATH`.

> *Alternatively, for a one-click automatic installation, use [scoop](https://scoop.sh/): `scoop install mpv`*

**macOS:**

```bash
brew install mpv
```

**Linux (Debian/Ubuntu):**

```bash
sudo apt install libmpv-dev mpv
```

### 2. YouTube API Key Setup

To enable search functionality, you need a YouTube Data API v3 key:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Navigate to **APIs & Services** > **Library** and search for **YouTube Data API v3**. Enable it.
4. Go to **Credentials**, click **Create Credentials**, and choose **API Key**.
5. Copy your new API key.

### 3. Clone & Initialize

Clone the project locally and add your newly minted API key to a `.env` file at the root of the project:

```bash
git clone <your-repo-link>
cd "Youtube MCP"
echo "YOUTUBE_API_KEY=your_api_key_here" > .env
```

Install dependencies instantly with `uv`:

```bash
uv sync
```

---

## 🔌 Connecting to Claude Desktop (MCP Setup)

To use this server inside Claude, you must add it to your `claude_desktop_config.json` file.

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the following configuration. Make sure to replace `[ABSOLUTE_PATH_TO_THIS_PROJECT]` with the actual full directory path to where you cloned this folder:

```json
{
  "mcpServers": {
    "youtube": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "ABSOLUTE_PATH_TO_THIS_PROJECT",
        "src/app/server.py"
      ],
      "env": {
        "YOUTUBE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

> 💡 *Note: Providing the API key inside the json `env` object is completely valid and overrides the `.env` file. Choose whatever method works best!*

Restart the Claude Desktop app. If configured correctly, you should see the new tools under the plugin icon in your chat window.

---

## 🧰 Available Tools for Claude

Once configured, Claude automatically understands how to leverage these tools based on your prompts.

### 🔍 Data & Search

- `search_youtube(query, limit)`: Standard search for videos natively.
- `get_video_details(video_id)`: Fetches view counts, likes, comment counts, and the text description.
- `get_transcript(video_id)`: Extracts the spoken transcript silently *(does not consume your API quota)*.
- `open_video(video_id)`: Fallback method to open the video inside the system's default web browser.

### 🎵 Playback & Control (MPV)

- `search_and_play(query)`: Finds a video and instantly launches it in the background player.
- `play_video_mpv(video_id)`: Plays an exact video ID locally.
- `enqueue_video(query_or_url)`: Adds a query or URL to your playlist line-up.
- `pause_resume_video()`: Toggles play/pause state.
- `seek_video(seconds)`: Seeks forwards or backwards by exact seconds.
- `playlist_next()` / `playlist_prev()`: Jumps between enqueued playlist tracks.
- `stop_video()`: Immediately stops playback and drops the queue.
- `set_loop(mode)`: Loop the playlist, single track, or disable looping.
- `set_playback_speed(speed)`: Adjust the speed multiplier natively.
- `set_volume(level)`: Adjust the playback volume between 0 and 100.

> 🔒 *All playback controls are fully shielded by a dedicated asynchronous message queue, making them completely thread-safe and resilient against Claude connection timeouts.*

---

## ⚠️ Known Limitations

- **Transcripts**: The transcript extraction relies on the public API layer (`youtube-transcript-api`). It is powerful but might fail if a video lacks an English transcript or has captions disabled by the creator.
- **Windows Library Bindings**: For `python-mpv` to work properly on Windows, it requires `libmpv`. If you get an mpv initialization warning inside Claude, ensure `mpv` is fully accessible in your device's global `PATH`!
