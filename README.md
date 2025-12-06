# StreamForge 🔥

**Sovereign Playlist Compiler** - Turn messy song lists into YouTube Music playlists instantly.

## Overview

StreamForge consists of three parts:

1. **The Keymaster** - Browser extension for secure auth key extraction
2. **StreamForge Engine** - Python CLI that cleans input, searches songs, and builds playlists
3. **The Agent Protocol** - Instructions for AI assistants to generate compatible lists

---

## Part 1: Keymaster Extension

### Installation

1. Go to `chrome://extensions`
2. Enable **Developer Mode** (top right)
3. Click **Load Unpacked**
4. Select the `keymaster_ext` folder

### Usage

1. Log into [music.youtube.com](https://music.youtube.com)
2. Click the Keymaster extension icon
3. Click **EXTRACT KEYS**
4. Just save to your **Downloads** folder (default)
   - StreamForge will auto-detect and move it to a secure location on first run

---

## Part 2: StreamForge Engine

### Requirements

```bash
pip install ytmusicapi
```

### Usage

**Interactive Mode (Wizard):**
```bash
python streamforge.py
```
Then paste your song list and type `GO` when done.

**File Mode (For Agents):**
```bash
python streamforge.py playlist.txt
```

### Features

- **Smart Parser** - Strips "(Official Video)", timestamps, numbering, and junk text
- **Fuzzy Search** - Finds songs even with messy formatting
- **URL Support** - Paste YouTube URLs directly
- **Dual Priority** - Searches "Songs" first, falls back to "Videos"

---

## Part 3: The Agent Protocol

Copy this instruction block into your AI assistant (ChatGPT, Gemini, Claude):

```
SYSTEM INSTRUCTION: STREAMFORGE COMPATIBILITY

I use a tool called StreamForge to generate music playlists from text. When I ask you to create a playlist, please Output a Code Block containing a plain text list.

Formatting Rules:
- One song per line.
- Format: Artist - Song Title
- Do not add numbering (1., 2.) or bullets.
- Do not include extra text like "(Official Video)".

Example Output:

Father of Peace - Enemy
System of a Down - B.Y.O.B.
Maneskin - Beggin

Tell me to save this list as playlist.txt and run python streamforge.py playlist.txt.
```

---

## Quick Start

1. ✅ Install the Keymaster extension
2. ✅ Extract your auth keys (click extension → EXTRACT KEYS)
3. ✅ Save to Downloads (StreamForge auto-migrates it securely)
4. ✅ Run `python streamforge.py`
5. ✅ Paste your songs and type `GO`
6. 🔥 Watch your playlist compile in real-time!

---

## License

MIT - Do whatever you want with it.
