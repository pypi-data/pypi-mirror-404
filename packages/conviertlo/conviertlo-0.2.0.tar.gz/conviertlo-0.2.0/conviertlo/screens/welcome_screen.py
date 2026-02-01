"""Welcome screen for Conviertlo"""
import shutil
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Container, VerticalScroll
from conviertlo.screens.file_browser_screen import FileBrowserScreen


class WelcomeScreen(Screen):
    """Initial landing screen with branding and file selection prompt"""

    CSS = """
    WelcomeScreen {
        background: $background;
    }

    #welcome-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    #content {
        width: auto;
        height: auto;
    }

    .logo {
        color: $accent;
        text-align: center;
        text-style: bold;
        margin: 1 0;
    }

    .welcome-message {
        color: $foreground;
        text-align: center;
        margin: 1 0;
    }

    .prompt {
        color: $accent;
        text-align: center;
        margin: 2 0;
        text-style: bold;
    }

    .hotkey-hint {
        color: $secondary;
        text-align: center;
        margin: 1 0;
    }

    .dragdrop-hint {
        color: $foreground;
        text-align: center;
        margin: 1 0;
        text-style: italic;
    }
    """

    BINDINGS = [
        ("f", "open_file_browser", "Open File Browser"),
    ]

    def compose(self):
        """Compose the welcome screen"""
        
        ascii_logo = """
╔═══════════════════════════════════════╗
║                                       ║
║   ██████╗ ██████╗ ███╗   ██╗██╗   ██╗██╗███████╗██████╗ ████████╗██╗      ██████╗ 
║  ██╔════╝██╔═══██╗████╗  ██║██║   ██║██║██╔════╝██╔══██╗╚══██╔══╝██║     ██╔═══██╗
║  ██║     ██║   ██║██╔██╗ ██║██║   ██║██║█████╗  ██████╔╝   ██║   ██║     ██║   ██║
║  ██║     ██║   ██║██║╚██╗██║╚██╗ ██╔╝██║██╔══╝  ██╔══██╗   ██║   ██║     ██║   ██║
║  ╚██████╗╚██████╔╝██║ ╚████║ ╚████╔╝ ██║███████╗██║  ██║   ██║   ███████╗╚██████╔╝
║   ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝  ╚═══╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚═════╝ 
║                                       ║
║      Media Copilot Converter          ║
║                                       ║
╚═══════════════════════════════════════╝
        """

        yield Container(
            Static(ascii_logo, classes="logo"),
            Static("Welcome to Conviertlo! 🎬", classes="welcome-message"),
            Static(
                "Convert and compress media files using natural language",
                classes="welcome-message"
            ),
            Static("Select files you want to convert...", classes="prompt"),
            Static("Press 'F' to open file browser", classes="hotkey-hint"),
            Static(
                "💡 Tip: You can drag and drop files directly (if supported)",
                classes="dragdrop-hint"
            ),
            id="welcome-container"
        )

    def on_mount(self):
        """Check for required dependencies when screen is mounted"""
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required command-line tools are installed"""
        missing_tools = []
        
        # Check for ffmpeg
        if not shutil.which("ffmpeg"):
            missing_tools.append("ffmpeg")

        # Check for ImageMagick (magick or convert)
        if not (shutil.which("magick") or shutil.which("convert")):
            missing_tools.append("ImageMagick (magick/convert)")
        
        # Check for GitHub Copilot CLI
        if not shutil.which("copilot"):
            missing_tools.append("GitHub Copilot CLI (@github/copilot)")
        
        # Notify user if any tools are missing
        if missing_tools:
            tool_list = ", ".join(missing_tools)
            self.notify(
                f"⚠️  Missing required tools: {tool_list}. "
                "Please install them to use Conviertlo.",
                severity="error",
                timeout=10
            )
            
            # Log installation instructions
            if "ffmpeg" in missing_tools:
                self.log.warning(
                    "ffmpeg not found. Install it using:\n"
                    "  Ubuntu/Debian: sudo apt install ffmpeg\n"
                    "  macOS: brew install ffmpeg\n"
                    "  Windows: winget install ffmpeg"
                )

            if "ImageMagick (magick/convert)" in missing_tools:
                self.log.warning(
                    "ImageMagick not found. Install it using:\n"
                    "  Ubuntu/Debian: sudo apt install imagemagick\n"
                    "  macOS: brew install imagemagick\n"
                    "  Windows: winget install ImageMagick.ImageMagick"
                )
            
            if "GitHub Copilot CLI (@github/copilot)" in missing_tools:
                self.log.warning(
                    "GitHub Copilot CLI not found. Install it using:\n"
                    "  npm install -g @github/copilot@latest"
                )
        else:
            self.log.info("All required dependencies found ✓")

    def action_open_file_browser(self):
        """Handle file browser opening action"""
        def handle_file_selection(selected_files):
            """Callback to handle selected files"""
            if selected_files:
                self.notify(f"Selected {len(selected_files)} file(s)")
                # Transition to instruction screen with selected files
                from conviertlo.screens.instruction_screen import InstructionScreen
                self.app.push_screen(InstructionScreen(
                    selected_files=selected_files,
                    copilot_service=self.app.copilot_service
                ))
            else:
                self.notify("File selection cancelled")
        
        # Push the file browser modal
        self.app.push_screen(FileBrowserScreen(), handle_file_selection)
