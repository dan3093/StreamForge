import json
import argparse
import sys
import time
import re
import os

# ==========================================
# 🎨 UI (The Hacker Vibe)
# ==========================================
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def banner():
    print(rf"""{CYAN}
   _____ __                            ______                       
  / ___// /_________  ____ _____ ___  / ____/___  _________  ___ 
  \__ \/ __/ ___/ _ \/ __ `/ __ `__ \/ /_  / __ \/ ___/ __ \/ _ \
 ___/ / /_/ /  /  __/ /_/ / / / / / / __/ / /_/ / /  / /_/ /  __/
/____/\__/_/   \___/\__,_/_/ /_/ /_/_/    \____/_/   \__, /\___/ 
                                                    /____/       {RESET}
{BOLD}:: SOVEREIGN PLAYLIST COMPILER :: v1.0 ::{RESET}
""")

# ==========================================
# 🧠 SMART PARSER (The Cleaning Logic)
# ==========================================
class SmartParser:
    @staticmethod
    def extract_id_from_url(text):
        regex = r'(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})'
        match = re.search(regex, text)
        return match.group(1) if match else None

    @staticmethod
    def sanitize(text):
        """
        Intelligently removes junk like [Official Video] but keeps (Don't Fear) The Reaper.
        """
        # 1. Remove URLs
        text = re.sub(r'http\S+', '', text)
        
        # 2. Remove Leading Numbers (1. Song)
        text = re.sub(r'^\d+[\.\-\)]\s*', '', text)

        # 3. Remove Timestamps [3:20]
        text = re.sub(r'\[\d+:\d+\]', '', text)
        text = re.sub(r'\(\d+:\d+\)', '', text)

        # 4. Remove Metadata Keywords inside Brackets/Parens
        # This regex looks for parens containing specific "junk" words
        junk_words = r'official|video|audio|lyrics|hq|4k|hd|remastered|visualizer'
        text = re.sub(r'[\(\[][^\)\]]*(' + junk_words + r')[^\)\]]*[\)\]]', '', text, flags=re.IGNORECASE)

        # 5. Collapse spaces
        return re.sub(r'\s+', ' ', text).strip()

# ==========================================
# ⚙️ ENGINE
# ==========================================
import shutil
from ytmusicapi import YTMusic

def get_config_dir():
    """Get the secure config directory in user's home."""
    config_dir = os.path.join(os.path.expanduser("~"), ".streamforge")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_headers_path():
    """Get the browser headers path."""
    return os.path.join(get_config_dir(), "streamforge_auth.json")

def parse_curl_command(curl_cmd):
    """Extract headers from a curl command."""
    headers = {}
    
    # Clean up Windows curl escaping
    curl_cmd = curl_cmd.replace('^"', '"').replace('^^', '^')
    
    # Extract -H headers
    import re
    header_pattern = r'-H\s+"([^"]+)"'
    for match in re.finditer(header_pattern, curl_cmd):
        header = match.group(1)
        if ':' in header:
            key, value = header.split(':', 1)
            headers[key.strip().lower()] = value.strip()
    
    # Extract -b cookie
    cookie_pattern = r'-b\s+"([^"]+)"'
    cookie_match = re.search(cookie_pattern, curl_cmd)
    if cookie_match:
        # Unescape the cookie value
        cookie = cookie_match.group(1).replace('%3D', '=').replace('%3B', ';')
        headers['cookie'] = cookie
    
    return headers

def setup_browser_auth():
    """Run the browser authentication setup wizard."""
    print(f"\n{YELLOW}🔐 First-time Browser Auth Setup Required{RESET}")
    print("-" * 50)
    print(f"{CYAN}YouTube Music requires browser-based authentication.{RESET}")
    print()
    print("Follow these steps:")
    print("1. Open https://music.youtube.com in your browser")
    print("2. Log in to your Google account if needed")
    print("3. Press F12 to open Developer Tools → Network tab")
    print("4. Click on any request to 'music.youtube.com'")
    print("5. Right-click the request → Copy → Copy as cURL")
    print("-" * 50)
    
    headers_path = get_headers_path()
    
    print(f"\n{BOLD}Paste the curl command (then press Enter twice):{RESET}")
    
    # Read multiline input until we get a blank line
    lines = []
    while True:
        try:
            line = input()
            if not line.strip() and lines:  # Empty line after content = done
                break
            lines.append(line)
        except EOFError:
            break
    
    curl_cmd = ' '.join(lines)
    
    if not curl_cmd or 'curl' not in curl_cmd.lower():
        print(f"{RED}❌ Invalid curl command.{RESET}")
        sys.exit(1)
    
    # Parse the curl command
    headers = parse_curl_command(curl_cmd)
    
    if 'cookie' not in headers:
        print(f"{RED}❌ Could not find cookie in curl command.{RESET}")
        sys.exit(1)
    
    # Ensure we have the required headers
    if 'authorization' not in headers:
        headers['authorization'] = ''
    
    # Fill in any missing standard headers
    defaults = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://music.youtube.com",
        "x-goog-authuser": "0",
        "x-origin": "https://music.youtube.com"
    }
    for key, value in defaults.items():
        if key not in headers:
            headers[key] = value
    
    with open(headers_path, 'w') as f:
        json.dump(headers, f, indent=2)
    
    print(f"\n{GREEN}✅ Authentication saved!{RESET}")
    print(f"   Found {len(headers)} headers including cookie.")
    return headers_path

def check_downloads_for_auth():
    """Check if browser.json was downloaded by the extension and move it."""
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads", "streamforge_auth.json")
    if os.path.exists(downloads_path):
        import shutil
        dest_path = get_headers_path()
        shutil.move(downloads_path, dest_path)
        print(f"{GREEN}✅ Found streamforge_auth.json in Downloads - moved to secure location!{RESET}")
        return True
    return False

class StreamForge:
    def __init__(self):
        headers_path = get_headers_path()
        
        # Check if auth is set up
        if not os.path.exists(headers_path):
            # Check if extension downloaded to Downloads folder
            if not check_downloads_for_auth():
                setup_browser_auth()
        
        try:
            self.yt = YTMusic(headers_path)
            print(f"{GREEN}🔑 Authenticated via browser headers.{RESET}")
        except Exception as e:
            print(f"{RED}❌ Auth Error: {e}{RESET}")
            print(f"   Try deleting {CYAN}{headers_path}{RESET} and running again.")
            sys.exit(1)

    def search(self, query):
        print(f"   🔎 Searching: {CYAN}'{query}'{RESET}...", end="\r")
        
        # Priority 1: Songs (High Quality)
        res = self.yt.search(query, filter="songs", limit=1)
        # Priority 2: Videos (Coverage)
        if not res:
            res = self.yt.search(query, filter="videos", limit=1)
        
        if res:
            title = res[0]['title']
            artist = res[0]['artists'][0]['name'] if 'artists' in res[0] else "Unknown"
            print(f"   ✅ {GREEN}Found:{RESET} {title[:30]:<30} {YELLOW}({artist}){RESET}")
            return res[0]['videoId']
        
        print(f"   ⚠️  {RED}No results:{RESET} '{query}'" + " "*10)
        return None

    def execute(self, title, raw_lines):
        banner()
        print(f"🔨 {BOLD}Compiling:{RESET} {title}")
        print("-" * 50)
        
        final_ids = []
        for line in raw_lines:
            if not line.strip(): continue
            
            # Check URL first
            vid_id = SmartParser.extract_id_from_url(line)
            if vid_id:
                final_ids.append(vid_id)
                print(f"   📌 {CYAN}Direct ID:{RESET} {vid_id}")
            else:
                clean_q = SmartParser.sanitize(line)
                if clean_q:
                    vid = self.search(clean_q)
                    if vid: final_ids.append(vid)
            
            time.sleep(0.1)

        if not final_ids:
            print(f"\n{RED}❌ Failed. No valid tracks.{RESET}")
            return

        print("-" * 50)
        try:
            pl_id = self.yt.create_playlist(title, "Generated via StreamForge", "PUBLIC", final_ids)
            print(f"\n{GREEN}🔥 SUCCESS! Playlist Active.{RESET}")
            print(f"🔗 {BOLD}Link:{RESET} https://music.youtube.com/playlist?list={pl_id}")
        except Exception as e:
            print(f"{RED}❌ API Error: {e}{RESET}")

# ==========================================
# 🎮 INTERFACE
# ==========================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", help="Text file with song list")
    args = parser.parse_args()
    
    app = StreamForge()

    # FILE MODE (For Agents)
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        name = f"Forge: {os.path.basename(args.file)}"
        app.execute(name, lines)
        return

    # WIZARD MODE (For Humans)
    banner()
    print("Paste your list below. (Messy text, Spotify copies, URLs allowed).")
    print(f"{CYAN}Type 'GO' on a new line to finish.{RESET}")
    print("-" * 50)
    
    lines = []
    while True:
        try:
            l = input()
            if l.strip().upper() == "GO": break
            lines.append(l)
        except EOFError: break
    
    if lines:
        name = input(f"\n{BOLD}Playlist Name:{RESET} ").strip() or "StreamForge Mix"
        app.execute(name, lines)

if __name__ == "__main__":
    main()
