from textual.app import App
from textual.widgets import Header, Footer
from conviertlo.resources.themes import CONVIERTLO_DARK
from conviertlo.screens.welcome_screen import WelcomeScreen
from conviertlo.services import CopilotService

class ConviertloApp(App):
    """A TUI app for media conversion using FFMPEG/ImageMagick and Copilot"""

    BINDINGS = [
        ("q", "quit", "Quit")
    ]
    
    def __init__(self, *args, **kwargs):
        """Initialize the app with shared Copilot service"""
        super().__init__(*args, **kwargs)
        self.copilot_service = CopilotService()
    
    def on_mount(self):
        """Initialize app and register theme"""
        self.register_theme(CONVIERTLO_DARK)
        self.theme = "conviertlo-dark"
        self.push_screen(WelcomeScreen())
    
    def compose(self):
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
    
    async def on_unmount(self):
        """Clean up resources when app closes"""
        try:
            await self.copilot_service.stop()
        except Exception:
            pass
    

if __name__ == "__main__":
    app = ConviertloApp()
    app.run()
