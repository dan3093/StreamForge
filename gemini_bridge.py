"""
Gemini CLI Bridge - Integration layer for AI-powered recommendations
"""
import subprocess
import json
import re
import shutil
from typing import Optional


def find_gemini_cli() -> Optional[str]:
    """Find the gemini-cli executable."""
    # Check if npx is available
    npx_path = shutil.which("npx")
    if npx_path:
        return "npx"
    return None


def call_gemini(prompt: str, timeout: int = 60) -> str:
    """
    Call gemini-cli with a prompt and return the response.
    
    Args:
        prompt: The prompt to send to Gemini
        timeout: Timeout in seconds
        
    Returns:
        The AI response text
    """
    cli = find_gemini_cli()
    if not cli:
        return "Error: gemini-cli not found. Install with: npm install -g @google/gemini-cli"
    
    try:
        # Use npx to run gemini-cli in non-interactive mode
        result = subprocess.run(
            [cli, "@google/gemini-cli", "--prompt", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=True  # Needed for Windows
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr or 'Unknown error'}"
        
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Error: Request timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def get_song_recommendations(query: str, prompt_type: str = "similar") -> list[str]:
    """
    Get song recommendations from Gemini.
    
    Args:
        query: The artist, song, or mood to base recommendations on
        prompt_type: One of "similar", "mood", "discover"
        
    Returns:
        List of song strings in "Artist - Song Title" format
    """
    prompts = {
        "similar": f"""Suggest 10 songs similar to "{query}". 
Format: One song per line as "Artist - Song Title" with no numbering or extra text.
Only output the song list, nothing else.""",
        
        "mood": f"""Create a playlist of 10 songs for this mood/activity: "{query}".
Format: One song per line as "Artist - Song Title" with no numbering or extra text.
Only output the song list, nothing else.""",
        
        "discover": f"""Suggest 10 new artists similar to "{query}" with one of their best songs.
Format: One song per line as "Artist - Song Title" with no numbering or extra text.
Only output the song list, nothing else."""
    }
    
    prompt = prompts.get(prompt_type, prompts["similar"])
    response = call_gemini(prompt)
    
    if response.startswith("Error:"):
        return [response]
    
    # Parse response into list of songs
    songs = []
    for line in response.split("\n"):
        line = line.strip()
        # Skip empty lines and lines that look like metadata
        if not line:
            continue
        # Remove common prefixes like "1.", "- ", etc.
        line = re.sub(r'^[\d]+[\.\)\-]\s*', '', line)
        line = re.sub(r'^[\-\*]\s*', '', line)
        if line and " - " in line:
            songs.append(line)
    
    return songs if songs else ["No recommendations found"]


def get_playlist_suggestions(description: str) -> list[str]:
    """
    Get playlist suggestions based on a description.
    
    Args:
        description: Free-form description of desired playlist
        
    Returns:
        List of song strings
    """
    prompt = f"""Based on this description: "{description}"
Create a playlist of 15 songs that match this vibe.
Format: One song per line as "Artist - Song Title" with no numbering or extra text.
Only output the song list, nothing else."""

    response = call_gemini(prompt)
    
    if response.startswith("Error:"):
        return [response]
    
    songs = []
    for line in response.split("\n"):
        line = line.strip()
        if not line:
            continue
        line = re.sub(r'^[\d]+[\.\)\-]\s*', '', line)
        line = re.sub(r'^[\-\*]\s*', '', line)
        if line and " - " in line:
            songs.append(line)
    
    return songs if songs else ["No suggestions found"]
