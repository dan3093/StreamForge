"""
StreamForge TUI - Keyboard-driven Terminal User Interface
"""
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, Input, 
    ListView, ListItem, Label, TextArea, OptionList,
    TabbedContent, TabPane, LoadingIndicator
)
from textual.binding import Binding
from textual.screen import Screen
from textual import work
from rich.text import Text
from rich.panel import Panel

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from streamforge import StreamForge, SmartParser, banner, CYAN, GREEN, YELLOW, RED, RESET
from gemini_bridge import get_song_recommendations, get_playlist_suggestions


# ==========================================
# 🎨 STYLES
# ==========================================
CSS = """
Screen {
    background: $surface;
}

#sidebar {
    width: 28;
    background: $surface-darken-1;
    border-right: solid $primary;
    padding: 1;
}

#main-content {
    padding: 1 2;
}

.nav-button {
    width: 100%;
    margin-bottom: 1;
}

.nav-button:focus {
    background: $primary;
}

#song-list {
    height: 1fr;
    border: solid $primary;
    padding: 1;
}

#preview-panel {
    height: 10;
    border: solid $secondary;
    margin-top: 1;
    padding: 1;
}

.recommendation-type {
    margin: 1 0;
}

#recommendation-results {
    height: 1fr;
    border: solid $success;
    margin-top: 1;
    padding: 1;
}

.title {
    text-style: bold;
    color: $text;
    margin-bottom: 1;
}

.subtitle {
    color: $text-muted;
    margin-bottom: 1;
}

#status-bar {
    dock: bottom;
    height: 1;
    background: $primary-darken-2;
    padding: 0 1;
}

.keyboard-hint {
    color: $text-muted;
    text-style: italic;
}

#welcome-banner {
    text-align: center;
    padding: 2;
    margin: 2;
    border: round $primary;
}

#quick-actions {
    margin-top: 2;
}

.action-button {
    margin: 0 1;
}

LoadingIndicator {
    height: 3;
}
"""


# ==========================================
# 📱 HOME SCREEN
# ==========================================
class HomeScreen(Static):
    """Home screen with welcome message and quick actions."""
    
    def compose(self) -> ComposeResult:
        yield Static(
            """[bold cyan]
   _____ __                            ______                       
  / ___// /_________  ____ _____ ___  / ____/___  _________  ___ 
  \\__ \\/ __/ ___/ _ \\/ __ `/ __ `__ \\/ /_  / __ \\/ ___/ __ \\/ _ \\
 ___/ / /_/ /  /  __/ /_/ / / / / / / __/ / /_/ / /  / /_/ /  __/
/____/\\__/_/   \\___/\\__,_/_/ /_/ /_/_/    \\____/_/   \\__, /\\___/ 
                                                    /____/       [/]

[bold]:: SOVEREIGN PLAYLIST COMPILER :: v2.0 TUI ::[/]
""",
            id="welcome-banner"
        )
        
        yield Static("[bold]Quick Actions[/]", classes="title")
        with Horizontal(id="quick-actions"):
            yield Button("📝 Create Playlist", id="btn-create", classes="action-button")
            yield Button("🤖 Get Recommendations", id="btn-recommend", classes="action-button")
            yield Button("⚙️  Settings", id="btn-settings", classes="action-button")
        
        yield Static("\n[dim italic]Use number keys 1-4 to navigate, or click buttons above[/]", classes="keyboard-hint")


# ==========================================
# 📝 CREATE PLAYLIST SCREEN
# ==========================================
class CreatePlaylistScreen(Static):
    """Screen for creating playlists from song lists."""
    
    def compose(self) -> ComposeResult:
        yield Static("[bold]📝 Create Playlist[/]", classes="title")
        yield Static("Paste your song list below (URLs, messy text, Spotify copies all work)", classes="subtitle")
        
        yield TextArea(id="song-input", language=None)
        yield Static("[dim]Preview will appear here...[/]", id="preview-panel")
        
        with Horizontal():
            yield Input(placeholder="Playlist name...", id="playlist-name")
            yield Button("🔥 Create", id="btn-create-playlist", variant="primary")
        
        yield Static("[dim italic]Tip: Paste your songs, then press Tab to preview[/]", classes="keyboard-hint")
    
    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Update preview when text changes."""
        text = event.text_area.text
        lines = text.split("\n")
        preview_lines = []
        
        for line in lines[:5]:  # Preview first 5
            if line.strip():
                clean = SmartParser.sanitize(line)
                if clean:
                    preview_lines.append(f"  ✓ {clean}")
        
        if len(lines) > 5:
            preview_lines.append(f"  ... and {len(lines) - 5} more")
        
        preview = "\n".join(preview_lines) if preview_lines else "[dim]No songs detected[/]"
        self.query_one("#preview-panel", Static).update(f"[bold]Preview:[/]\n{preview}")


# ==========================================
# 🤖 RECOMMENDATIONS SCREEN  
# ==========================================
class RecommendationsScreen(Static):
    """Screen for getting AI-powered recommendations."""
    
    def compose(self) -> ComposeResult:
        yield Static("[bold]🤖 Get Recommendations[/]", classes="title")
        yield Static("Use AI to discover new music", classes="subtitle")
        
        yield Static("[bold]Choose recommendation type:[/]", classes="recommendation-type")
        yield OptionList(
            "🎵 Similar songs - Find songs like an artist or track",
            "🎭 Mood playlist - Create a playlist for a mood/activity", 
            "🔍 Discover artists - Find new artists similar to one you like",
            "📝 Custom prompt - Describe what you want",
            id="rec-type-list"
        )
        
        yield Input(placeholder="Enter artist, song, mood, or description...", id="rec-query")
        yield Button("✨ Get Recommendations", id="btn-get-recs", variant="primary")
        
        yield ScrollableContainer(
            Static("[dim]Recommendations will appear here...[/]", id="rec-results-text"),
            id="recommendation-results"
        )
        
        yield Button("📋 Use These Songs", id="btn-use-songs", variant="success")

    @work(exclusive=True, thread=True)
    def fetch_recommendations(self, query: str, rec_type: int) -> None:
        """Fetch recommendations from Gemini (runs in thread)."""
        type_map = {0: "similar", 1: "mood", 2: "discover", 3: "custom"}
        prompt_type = type_map.get(rec_type, "similar")
        
        if prompt_type == "custom":
            songs = get_playlist_suggestions(query)
        else:
            songs = get_song_recommendations(query, prompt_type)
        
        # Update UI from main thread
        self.app.call_from_thread(self._display_results, songs)
    
    def _display_results(self, songs: list[str]) -> None:
        """Display recommendation results."""
        if songs and songs[0].startswith("Error:"):
            result_text = f"[red]{songs[0]}[/]"
        else:
            result_text = "[bold green]Recommendations:[/]\n"
            for i, song in enumerate(songs, 1):
                result_text += f"  {i}. {song}\n"
        
        self.query_one("#rec-results-text", Static).update(result_text)
        # Store songs for later use
        self._current_songs = songs


# ==========================================
# ⚙️ SETTINGS SCREEN
# ========================================== 
class SettingsScreen(Static):
    """Settings and configuration screen."""
    
    def compose(self) -> ComposeResult:
        yield Static("[bold]⚙️ Settings[/]", classes="title")
        
        # Auth status
        from streamforge import get_headers_path
        headers_path = get_headers_path()
        auth_status = "✅ Authenticated" if os.path.exists(headers_path) else "❌ Not authenticated"
        
        yield Static(f"[bold]Authentication:[/] {auth_status}")
        yield Static(f"[dim]Auth file: {headers_path}[/]")
        
        with Horizontal():
            yield Button("🔄 Re-authenticate", id="btn-reauth")
            yield Button("🗑️  Clear Auth", id="btn-clear-auth", variant="error")
        
        yield Static("\n[bold]Keyboard Shortcuts:[/]", classes="title")
        yield Static("""
  [cyan]1[/]  Home
  [cyan]2[/]  Create Playlist  
  [cyan]3[/]  Get Recommendations
  [cyan]4[/]  Settings
  [cyan]?[/]  Show this help
  [cyan]q[/]  Quit
  [cyan]↑/↓[/] or [cyan]j/k[/]  Navigate
  [cyan]Enter[/]  Select
  [cyan]Tab[/]  Next panel
  [cyan]Esc[/]  Back
""")


# ==========================================
# 🎮 MAIN APP
# ==========================================
class StreamForgeApp(App):
    """StreamForge TUI Application."""
    
    CSS = CSS
    TITLE = "StreamForge"
    SUB_TITLE = "Sovereign Playlist Compiler"
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("1", "show_home", "Home", show=True),
        Binding("2", "show_create", "Create", show=True),
        Binding("3", "show_recommend", "Recommend", show=True),
        Binding("4", "show_settings", "Settings", show=True),
        Binding("?", "show_help", "Help"),
        Binding("escape", "go_back", "Back"),
        Binding("j", "focus_next", "Down", show=False),
        Binding("k", "focus_previous", "Up", show=False),
    ]
    
    def __init__(self):
        super().__init__()
        self.current_screen = "home"
        self._forge = None
    
    @property
    def forge(self) -> StreamForge:
        """Lazy-load StreamForge engine."""
        if self._forge is None:
            self._forge = StreamForge()
        return self._forge
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal():
            # Sidebar
            with Vertical(id="sidebar"):
                yield Static("[bold cyan]Navigation[/]", classes="title")
                yield Button("🏠 Home", id="nav-home", classes="nav-button")
                yield Button("📝 Create", id="nav-create", classes="nav-button")
                yield Button("🤖 Recommend", id="nav-recommend", classes="nav-button")
                yield Button("⚙️  Settings", id="nav-settings", classes="nav-button")
            
            # Main content area
            with ScrollableContainer(id="main-content"):
                yield HomeScreen(id="screen-home")
                yield CreatePlaylistScreen(id="screen-create")
                yield RecommendationsScreen(id="screen-recommend")
                yield SettingsScreen(id="screen-settings")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the app."""
        self._show_screen("home")
    
    def _show_screen(self, screen_name: str) -> None:
        """Show a specific screen and hide others."""
        screens = ["home", "create", "recommend", "settings"]
        for name in screens:
            widget = self.query_one(f"#screen-{name}")
            widget.display = (name == screen_name)
        self.current_screen = screen_name
    
    def action_show_home(self) -> None:
        self._show_screen("home")
    
    def action_show_create(self) -> None:
        self._show_screen("create")
    
    def action_show_recommend(self) -> None:
        self._show_screen("recommend")
    
    def action_show_settings(self) -> None:
        self._show_screen("settings")
    
    def action_show_help(self) -> None:
        self._show_screen("settings")  # Settings has the keybindings
    
    def action_go_back(self) -> None:
        if self.current_screen != "home":
            self._show_screen("home")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        # Navigation buttons
        if button_id == "nav-home" or button_id == "btn-home":
            self._show_screen("home")
        elif button_id == "nav-create" or button_id == "btn-create":
            self._show_screen("create")
        elif button_id == "nav-recommend" or button_id == "btn-recommend":
            self._show_screen("recommend")
        elif button_id == "nav-settings" or button_id == "btn-settings":
            self._show_screen("settings")
        
        # Action buttons
        elif button_id == "btn-create-playlist":
            self._create_playlist()
        elif button_id == "btn-get-recs":
            self._get_recommendations()
        elif button_id == "btn-use-songs":
            self._use_recommendation_songs()
        elif button_id == "btn-reauth":
            self.notify("Re-authentication: Run 'python streamforge.py' in terminal")
        elif button_id == "btn-clear-auth":
            self._clear_auth()
    
    def _create_playlist(self) -> None:
        """Create a playlist from the input."""
        try:
            song_input = self.query_one("#song-input", TextArea)
            name_input = self.query_one("#playlist-name", Input)
            
            songs = song_input.text.split("\n")
            songs = [s.strip() for s in songs if s.strip()]
            
            if not songs:
                self.notify("No songs entered!", severity="error")
                return
            
            name = name_input.value or "StreamForge Mix"
            
            self.notify(f"Creating playlist '{name}' with {len(songs)} songs...")
            
            # Run in background
            self._execute_playlist_creation(name, songs)
            
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
    
    @work(exclusive=True, thread=True)
    def _execute_playlist_creation(self, name: str, songs: list[str]) -> None:
        """Execute playlist creation in background thread."""
        try:
            self.forge.execute(name, songs)
            self.app.call_from_thread(
                self.notify, 
                f"✅ Playlist '{name}' created successfully!",
                severity="information"
            )
        except Exception as e:
            self.app.call_from_thread(
                self.notify,
                f"❌ Error: {e}",
                severity="error"
            )
    
    def _get_recommendations(self) -> None:
        """Get recommendations from Gemini."""
        try:
            query_input = self.query_one("#rec-query", Input)
            type_list = self.query_one("#rec-type-list", OptionList)
            
            query = query_input.value
            if not query:
                self.notify("Enter a query first!", severity="warning")
                return
            
            # Get selected type (default to 0)
            selected = type_list.highlighted or 0
            
            self.notify("🤖 Fetching recommendations from Gemini...")
            
            # Trigger the recommendation fetch
            rec_screen = self.query_one("#screen-recommend", RecommendationsScreen)
            rec_screen.fetch_recommendations(query, selected)
            
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
    
    def _use_recommendation_songs(self) -> None:
        """Copy recommended songs to create playlist screen."""
        try:
            rec_screen = self.query_one("#screen-recommend", RecommendationsScreen)
            if hasattr(rec_screen, '_current_songs') and rec_screen._current_songs:
                songs = rec_screen._current_songs
                if not songs[0].startswith("Error:"):
                    song_text = "\n".join(songs)
                    song_input = self.query_one("#song-input", TextArea)
                    song_input.text = song_text
                    self._show_screen("create")
                    self.notify("Songs copied to Create Playlist!")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
    
    def _clear_auth(self) -> None:
        """Clear authentication file."""
        from streamforge import get_headers_path
        path = get_headers_path()
        if os.path.exists(path):
            os.remove(path)
            self.notify("Auth cleared! Restart to re-authenticate.", severity="warning")
        else:
            self.notify("No auth file found.", severity="information")


def main():
    """Run the TUI application."""
    app = StreamForgeApp()
    app.run()


if __name__ == "__main__":
    main()
