"""File browser screen for selecting media files"""
from pathlib import Path
from rich.text import Text
from textual.screen import ModalScreen
from textual.widgets import DirectoryTree, Static, Button, Label
from textual.widgets.tree import TreeNode
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual.reactive import reactive


class MediaDirectoryTree(DirectoryTree):
    """Custom DirectoryTree that filters for media files"""
    
    MEDIA_EXTENSIONS = {
        # Video
        '.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv',
        # Image
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.svg',
        # Audio
        '.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'
    }
    
    def filter_paths(self, paths):
        """Filter to show only directories and media files, excluding hidden files"""
        return [
            path for path in paths
            if not path.name.startswith('.') and (path.is_dir() or path.suffix.lower() in self.MEDIA_EXTENSIONS)
        ]


class FileBrowserScreen(ModalScreen):
    """Modal screen for browsing and selecting media files"""

    confirming = reactive(False)
    
    CSS = """
    FileBrowserScreen {
        align: center middle;
    }

    #browser-container {
        width: 90%;
        height: 85%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    #current-path {
        width: 100%;
        color: $accent;
        margin-bottom: 1;
        padding: 1;
        background: $panel;
        border: solid $foreground;
    }

    #directory-tree {
        width: 100%;
        height: 1fr;
        border: solid $foreground;
        margin-bottom: 1;
    }

    #selection-info {
        width: 100%;
        color: $foreground;
        text-align: center;
        margin-bottom: 1;
    }

    #button-container {
        width: 100%;
        height: auto;
        align: center middle;
    }

    Button {
        margin: 0 1;
    }

    Button.confirm {
        background: $success;
    }

    Button.cancel {
        background: $error;
    }
    """

    BINDINGS = [
        Binding("escape,ctrl+c", "cancel", "Cancel", show=True),
        Binding("alt+enter", "confirm", "Confirm", show=True),
        Binding("j", "move_down", "Move Down", show=False),
        Binding("k", "move_up", "Move Up", show=False),
    ]

    def __init__(self, start_path: str = None):
        """Initialize the file browser
        
        Args:
            start_path: Optional starting directory path (defaults to home)
        """
        super().__init__()
        self.start_path = Path(start_path) if start_path else Path.home()
        self.selected_files: set[Path] = set()

    def compose(self):
        """Compose the file browser UI"""
        yield Container(
            Label("Select Media Files", id="title"),
            Static(f"📁 {self.start_path}", id="current-path"),
            MediaDirectoryTree(
                str(self.start_path),
                id="directory-tree"
            ),
            Static("0 files selected", id="selection-info"),
            Horizontal(
                Button("Cancel", variant="error", classes="cancel"),
                Button("Confirm Selection", variant="success", classes="confirm", id="confirm-button"),
                id="button-container"
            ),
            id="browser-container"
        )

    def on_mount(self):
        """Focus the directory tree on mount"""
        self.query_one(MediaDirectoryTree).focus()

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        """Handle file selection in the directory tree"""
        selected_path = Path(event.path)
        
        # Toggle selection
        if selected_path in self.selected_files:
            self.selected_files.remove(selected_path)
            self._update_node_visual(event.node, False)
        else:
            # Only add if it's a file and has a media extension
            if selected_path.is_file():
                if selected_path.suffix.lower() in MediaDirectoryTree.MEDIA_EXTENSIONS:
                    self.selected_files.add(selected_path)
                    self._update_node_visual(event.node, True)
                else:
                    self.notify(f"File type {selected_path.suffix} is not supported", severity="warning")
        
        # Update selection counter
        self._update_selection_info()

    def _update_node_visual(self, node: TreeNode, selected: bool):
        """Update the visual state of a tree node"""
        if not node:
            return
            
        # Get the base filename (stripping existing prefix if present)
        current_label = str(node.label)
        file_name = current_label[2:] if current_label.startswith("✅ ") else current_label
            
        if selected:
            node.label = Text("✅ ", style="bold green") + Text(file_name, style="bold green")
        else:
            node.label = Text(file_name)

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected):
        """Handle directory navigation"""
        selected_path = Path(event.path)
        current_path_widget = self.query_one("#current-path", Static)
        current_path_widget.update(f"📁 {selected_path}")

    def _update_selection_info(self):
        """Update the selection information display"""
        count = len(self.selected_files)
        info_widget = self.query_one("#selection-info", Static)
        
        if count == 0:
            info_widget.update("0 files selected")
        elif count == 1:
            info_widget.update("1 file selected")
        else:
            info_widget.update(f"{count} files selected")

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses"""
        if "confirm" in event.button.classes:
            self.action_confirm()
        elif "cancel" in event.button.classes:
            self.action_cancel()

    def action_confirm(self):
        """Confirm selection and return to previous screen"""
        if not self.selected_files:
            self.notify("No files selected", severity="warning")
            return

        if self.confirming:
            return

        self.confirming = True

        # Dismiss modal with selected files after UI updates
        self.set_timer(1.5, self._dismiss_with_selection)

    def action_cancel(self):
        """Cancel and return to previous screen"""
        self.dismiss(None)

    def action_move_down(self):
        tree = self.query_one(MediaDirectoryTree)
        tree.action_cursor_down()

    def action_move_up(self):
        tree = self.query_one(MediaDirectoryTree)
        tree.action_cursor_up()

    def watch_confirming(self, confirming: bool) -> None:
        confirm_button = self.query_one("#confirm-button", Button)
        confirm_button.loading = confirming

    def _dismiss_with_selection(self) -> None:
        self.dismiss(list(self.selected_files))
