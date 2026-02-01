"""Input/Instruction screen for natural language conversion instructions"""
from pathlib import Path
import re
import shlex
from textual.screen import Screen
from textual.widgets import Button, Label, ListView, ListItem, Select, ProgressBar, Markdown
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.binding import Binding
from textual import work
from textual.color import Gradient
from textual.worker import Worker
from conviertlo.widgets import VimTextArea
from conviertlo.services import CopilotService

MEDIA_COMMAND_PREFIXES = ("ffmpeg", "magick", "convert")


class FileListItem(ListItem):
    """Custom list item for displaying file information"""
    
    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path
        self._file_size = self._get_file_size()
        self._file_format = file_path.suffix.upper().replace('.', '')
        
    def compose(self):
        """Compose the file list item"""
        yield Horizontal(
            Label(f"📄 {self.file_path.name}", classes="file-name"),
            Label(f"{self._file_size}", classes="file-size"),
            Label(f"{self._file_format}", classes="file-format"),
            Button("×", variant="error", classes="remove-file-btn"),
            classes="file-item-content"
        )
    
    def _get_file_size(self) -> str:
        """Get human-readable file size"""
        try:
            size_bytes = self.file_path.stat().st_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} TB"
        except Exception:
            return "Unknown"


class InstructionScreen(Screen):
    """Screen for displaying selected files and accepting conversion instructions"""
    
    CSS = """
    InstructionScreen {
        background: $background;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
        layout: grid;
        grid-size: 2 2;
        grid-rows: 1fr 1fr;
        grid-columns: 1fr 1fr;
        padding: 1 2;
    }
    
    /* Panel 1 - Selected Files (Top-Left) */
    #selected-files-panel {
        background: $surface;
        border: solid $primary;
        padding: 1 2;
        column-span: 1;
        row-span: 1;
    }
    
    .panel-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
        text-align: center;
    }
    
    #files-list {
        height: 1fr;
        border: solid $foreground;
        margin-bottom: 1;
    }
    
    .file-item-content {
        width: 100%;
        height: auto;
        align: left middle;
    }
    
    .file-name {
        width: 1fr;
        color: $foreground;
    }
    
    .file-size {
        width: auto;
        color: $accent;
        margin: 0 1;
    }
    
    .file-format {
        width: auto;
        color: $secondary;
        margin: 0 1;
    }
    
    .remove-file-btn {
        width: auto;
        min-width: 3;
        margin: 0 1;
    }
    
    #file-actions {
        width: 100%;
        height: auto;
        align: center middle;
    }
    
    #file-actions Button {
        margin: 0 1;
    }
    
    /* Panel 2 - Instruction Input (Bottom-Left) */
    #instruction-panel {
        background: $surface;
        border: solid $primary;
        padding: 1 2;
        column-span: 1;
        row-span: 1;
    }
    
    #instruction-input {
        height: 1fr;
        border: solid $foreground;
        margin-bottom: 1;
    }
    
    #model-select {
        width: 100%;
        margin-bottom: 1;
    }
    
    #submit-btn {
        width: 100%;
    }
    
    .placeholder-text {
        color: $foreground;
        text-align: center;
        text-style: italic;
        margin: 2 0;
    }
    
    /* Panel 3 - Command Preview (Right - Full Height) */
    #preview-panel {
        background: $surface;
        border: solid $primary;
        padding: 1 2;
        column-span: 1;
        row-span: 2;
    }
    
    #command-preview-scroll {
        height: 1fr;
        border: solid $foreground;
        margin-bottom: 1;
    }
    
    #command-preview {
        width: 100%;
        padding: 1;
    }
    
    #preview-actions {
        width: 100%;
        height: auto;
        align: center middle;
    }
    
    #preview-actions Button {
        margin: 0 1;
    }

    #ffmpeg-progress-container {
        width: 100%;
        height: auto;
        align: left middle;
        margin-bottom: 1;
    }

    #ffmpeg-progress-label {
        width: auto;
        color: $accent;
        margin-right: 1;
    }

    #ffmpeg-progress {
        width: 1fr;
        height: 1;
        color: $accent;
        background: $surface;
    }

    .ffmpeg-progress-hidden {
        display: none;
    }
    
    .loading-text {
        color: $accent;
        text-align: center;
        text-style: italic;
    }
    """
    
    BINDINGS = [
        Binding("escape", "go_back", "Go Back", show=True),
        Binding("ctrl+a", "add_files", "Add More Files", show=True),
        Binding("ctrl+d", "clear_all", "Clear All", show=True),
        Binding("D,delete", "remove_selected", "Remove Selected", show=True),
        Binding("ctrl+g", "submit_instruction", "Generate Command", show=True),
        Binding("ctrl+m", "change_model", "Change Model", show=True),
        Binding("ctrl+e", "execute", "Execute", show=True),
        Binding("ctrl+c", "cancel", "Cancel", show=True),
        Binding("ctrl+r", "refine", "Refine", show=True),
        Binding("j", "move_down", "Move Down", show=False),
        Binding("k", "move_up", "Move Up", show=False),
        Binding("ctrl+i", "focus_instruction", "Focus Instruction Input", show=True),
        Binding("ctrl+l", "focus_files", "Focus Files List", show=True),
        Binding("ctrl+enter", "submit_instruction", "Submit Instruction", show=True),
    ]
    
    def __init__(self, selected_files: list[Path], copilot_service: CopilotService = None):
        """Initialize the instruction screen
        
        Args:
            selected_files: List of file paths selected by the user
            copilot_service: Optional CopilotService instance (will create if not provided)
        """
        super().__init__()
        self.selected_files = selected_files
        self.copilot_service = copilot_service or CopilotService()
        self.current_model = "Claude Sonnet 4.5"
        self.current_response = ""
        self.is_processing = False
        self.pending_commands: list[str] = []
        self._executing_batch = False
        self.output_directory = Path("~/conviertlo").expanduser()
        self._ffmpeg_command_index = 0
        self._ffmpeg_command_total = 0
        self._request_worker: Worker | None = None
        self._execution_worker: Worker | None = None
        self._cancel_requested = False
    
    def compose(self):
        gradient = Gradient.from_colors(
            "#881177",
            "#aa3355",
            "#cc6666",
            "#ee9944",
            "#eedd00",
            "#99dd55",
            "#44dd88",
            "#22ccbb",
            "#00bbcc",
            "#0099cc",
            "#3366bb",
            "#663399",
        )
        """Compose the instruction screen UI"""
        yield Container(
            # Panel 1 - Selected Files (Top-Left)
            Vertical(
                Label("Selected Files", classes="panel-title"),
                ListView(
                    *[FileListItem(file_path) for file_path in self.selected_files],
                    id="files-list"
                ),
                Horizontal(
                    Button("Add More Files", variant="primary", id="add-files-btn"),
                    Button("Clear All", variant="warning", id="clear-all-btn"),
                    id="file-actions"
                ),
                id="selected-files-panel"
            ),
            
            # Panel 2 - Command Preview (Right - Full Height)
            Vertical(
                Label("Command Preview", classes="panel-title"),
                VerticalScroll(
                    Markdown("", id="command-preview"),
                    id="command-preview-scroll"
                ),
                Horizontal(
                    Label("Conversion Progress", id="ffmpeg-progress-label"),
                    ProgressBar(total=100, id="ffmpeg-progress", gradient=gradient),
                    id="ffmpeg-progress-container",
                    classes="ffmpeg-progress-hidden",
                ),
                Horizontal(
                    Button("Execute", variant="success", id="execute-btn", disabled=True),
                    Button("Refine", variant="primary", id="refine-btn", disabled=True),
                    Button("Cancel", variant="error", id="cancel-btn", disabled=True),
                    Button("Clear", variant="warning", id="clear-preview-btn", disabled=True),
                    id="preview-actions"
                ),
                id="preview-panel"
            ),

            # Panel 3 - Instruction Input (Bottom-Left)
            Vertical(
                Label("Instruction Input", classes="panel-title"),
                Select(
                    [
                        ("Claude Sonnet 4.5", "Claude Sonnet 4.5"),
                        ("Claude Haiku 4.5", "Claude Haiku 4.5"),
                        ("Claude Opus 4.5", "Claude Opus 4.5"),
                        ("Claude Sonnet 4", "Claude Sonnet 4"),
                        ("GPT-5.2-Codex", "GPT-5.2-Codex"),
                        ("GPT-5.1-Codex-Max", "GPT-5.1-Codex-Max"),
                        ("GPT-5.1-Codex", "GPT-5.1-Codex"),
                        ("GPT-5.2", "GPT-5.2"),
                        ("GPT-5.1", "GPT-5.1"),
                        ("GPT-5", "GPT-5"),
                        ("GPT-5.1-Codex-Mini", "GPT-5.1-Codex-Mini"),
                        ("GPT-5 mini", "GPT-5 mini"),
                        ("GPT-4.1", "GPT-4.1"),
                        ("Gemini 3 Pro (Preview)", "Gemini 3 Pro (Preview)"),
                    ],
                    value=self.current_model,
                    id="model-select",
                    allow_blank=False,
                ),
                VimTextArea(
                    id="instruction-input",
                    placeholder="What do you want to do? (e.g., 'compress to under 10MB', 'convert to MP4 720p')\n\nPress Ctrl+g to submit"
                ),
                Button("Generate Command", variant="success", id="submit-btn"),
                id="instruction-panel"
            ),
            
            id="main-container"
        )
    
    async def on_mount(self):
        """Initialize Copilot service when screen is mounted"""
        try:
            # Just start the client - session will be created lazily when needed
            await self.copilot_service.start()
            self.copilot_service.on_event(self._handle_copilot_event)
            self.notify("Ready to generate commands", severity="information")
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.notify(f"Failed to initialize Copilot: {e}", severity="error")
            # Log full traceback for debugging
            self.log.error(f"Copilot initialization failed:\n{error_details}")
    
    async def on_unmount(self):
        """Clean up Copilot service when screen is unmounted"""
        try:
            self.copilot_service.off_event(self._handle_copilot_event)
            await self.copilot_service.destroy_session()
        except Exception as e:
            self.notify(f"Error during cleanup: {e}", severity="warning")
    
    def _handle_copilot_event(self, event: dict):
        """Handle events from Copilot SDK"""
        event_type = event.get("type")

        if self._cancel_requested and event_type in {
            "assistant.message",
            "assistant.message_complete",
            "tool.execution_start",
            "tool.execution_complete",
        }:
            return
        
        if event_type == "assistant.message":
            # Append message content to current response
            content = event.get("data", {}).get("content", "")
            self.current_response += content
            self._update_preview(self.current_response)
            
        elif event_type == "assistant.message_complete":
            # Enable action buttons when response is complete
            if self._executing_batch:
                return

            self.is_processing = False
            self.pending_commands = self._extract_media_commands(self.current_response)
            self._update_execute_label(len(self.pending_commands))
            self._enable_preview_actions()
            self._enable_input_controls()
            self._disable_cancel_action()
            
        elif event_type == "tool.execution_start":
            tool_name = event.get("data", {}).get("toolName", "")
            self.notify(f"Running tool: {tool_name}", severity="information")

        elif event_type == "tool.execution_complete":
            tool_name = event.get("data", {}).get("toolName", "")
            if tool_name:
                self.notify(f"Completed tool: {tool_name}", severity="information")
            
        elif event_type == "error":
            error_msg = event.get("data", {}).get("message", "Unknown error")
            self.notify(f"Copilot error: {error_msg}", severity="error")
            self.is_processing = False
            self._update_preview(f"[bold red]Error:[/bold red] {error_msg}")
            self._enable_input_controls()
            self._disable_cancel_action()
    
    def _update_preview(self, content: str):
        """Update the command preview panel with new content"""
        preview = self.query_one("#command-preview", Markdown)
        preview.update(content)

    def _disable_input_controls(self):
        """Disable instruction input controls while processing"""
        self.query_one("#instruction-input", VimTextArea).disabled = True
        self.query_one("#model-select", Select).disabled = True
        self.query_one("#submit-btn", Button).disabled = True

    def _enable_input_controls(self):
        """Enable instruction input controls when idle"""
        self.query_one("#instruction-input", VimTextArea).disabled = False
        self.query_one("#model-select", Select).disabled = False
        self.query_one("#submit-btn", Button).disabled = False
    
    def _enable_preview_actions(self):
        """Enable the preview action buttons"""
        self.query_one("#execute-btn", Button).disabled = False
        self.query_one("#refine-btn", Button).disabled = False
        self.query_one("#clear-preview-btn", Button).disabled = False
        self.query_one("#cancel-btn", Button).disabled = True
    
    def _disable_preview_actions(self):
        """Disable the preview action buttons"""
        self.query_one("#execute-btn", Button).disabled = True
        self.query_one("#refine-btn", Button).disabled = True
        self.query_one("#clear-preview-btn", Button).disabled = True
        self.query_one("#cancel-btn", Button).disabled = True

    def _enable_cancel_action(self):
        self.query_one("#cancel-btn", Button).disabled = False

    def _disable_cancel_action(self):
        self.query_one("#cancel-btn", Button).disabled = True
    
    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses"""
        if event.button.id == "add-files-btn":
            self.action_add_files()
        elif event.button.id == "clear-all-btn":
            self.action_clear_all()
        elif event.button.id == "submit-btn":
            self.action_submit_instruction()
        elif event.button.id == "execute-btn":
            self._handle_execute()
        elif event.button.id == "refine-btn":
            self._handle_refine()
        elif event.button.id == "cancel-btn":
            self.action_cancel()
        elif event.button.id == "clear-preview-btn":
            self._handle_clear_preview()
        elif "remove-file-btn" in event.button.classes:
            # Find the parent ListItem and remove the file
            list_item = event.button.ancestors[0]
            if isinstance(list_item, FileListItem):
                self._remove_file(list_item.file_path)
    
    def on_select_changed(self, event: Select.Changed):
        """Handle model selection changes"""
        if event.select.id == "model-select":
            self.current_model = event.value
            self.notify(f"Model set to {event.value}", severity="information")
    
    def action_go_back(self):
        """Go back to the previous screen"""
        self.app.pop_screen()
    
    def action_submit_instruction(self):
        """Submit the instruction to Copilot"""
        if self.is_processing:
            self.notify("Already processing a request...", severity="warning")
            return
        
        # Get the instruction text
        instruction_input = self.query_one("#instruction-input", VimTextArea)
        instruction = instruction_input.text.strip()
        
        if not instruction:
            self.notify("Please enter an instruction", severity="warning")
            return
        
        if not self.selected_files:
            self.notify("No files selected", severity="warning")
            return
        
        # Start processing
        self.is_processing = True
        self.current_response = ""
        self._cancel_requested = False
        self._disable_input_controls()
        self._disable_preview_actions()
        self._enable_cancel_action()
        self._update_preview("Generating command...")
        
        # Send request in background
        self._request_worker = self._send_copilot_request(instruction)

    def action_change_model(self):
        """Focus the model select to change model"""
        model_select = self.query_one("#model-select", Select)
        model_select.focus()

    def action_execute(self):
        """Trigger execute action from keybinding"""
        self._handle_execute()

    def action_refine(self):
        """Trigger refine action from keybinding"""
        self._handle_refine()

    def action_cancel(self):
        """Cancel any active Copilot command execution"""
        if not self.is_processing:
            self.notify("No active process to cancel", severity="warning")
            return

        self._cancel_requested = True
        self.notify("Cancellation requested", severity="warning")
        self._update_preview("Cancellation requested...")

        if self._request_worker:
            self._request_worker.cancel()
            self._request_worker = None
        if self._execution_worker:
            self._execution_worker.cancel()
            self._execution_worker = None

        self._cancel_copilot()
        self._executing_batch = False
        self.is_processing = False
        self._enable_input_controls()
        self._enable_preview_actions()
        self._disable_cancel_action()
        self._finish_ffmpeg_progress()
    
    @work(exclusive=True)
    async def _send_copilot_request(self, instruction: str):
        """Send request to Copilot in background worker"""
        try:
            await self.copilot_service.send_conversion_request(
                instruction, 
                self.selected_files,
                model=self.current_model
            )
        except Exception as e:
            self.notify(f"Error communicating with Copilot: {e}", severity="error")
            self._update_preview(f"[bold red]Error:[/bold red] {str(e)}")
            self.is_processing = False
            self._enable_input_controls()
            self._disable_cancel_action()
        finally:
            self._request_worker = None
    
    def _handle_execute(self):
        """Handle execute button press"""
        if self.is_processing:
            self.notify("Already processing a request...", severity="warning")
            return

        if not self.current_response.strip():
            self.notify("No command to execute", severity="warning")
            return

        commands = self.pending_commands or self._extract_media_commands(self.current_response)
        if not commands:
            self.notify("No command found in the preview", severity="warning")
            return

        prepared_commands = self._prepare_commands_for_execution(commands)
        if not prepared_commands:
            self.notify("Unable to resolve input file paths", severity="warning")
            return

        self.is_processing = True
        self.current_response = ""
        self._executing_batch = True
        self._cancel_requested = False
        self._disable_input_controls()
        self._disable_preview_actions()
        self._enable_cancel_action()
        self._update_preview("[italic]Executing commands...[/italic]")
        self._start_ffmpeg_progress(len(prepared_commands))

        self._execution_worker = self._send_execution_request(prepared_commands)

    @work(exclusive=True)
    async def _send_execution_request(self, commands: list[str]):
        """Send execution request to Copilot in background worker"""
        try:
            self._ensure_output_directory()
            for index, command in enumerate(commands, start=1):
                if self._cancel_requested:
                    break
                self._reset_ffmpeg_progress(index, len(commands))
                self._update_preview(
                    f"[italic]Executing command {index} of {len(commands)}...[/italic]\n\n{command}"
                )
                await self.copilot_service.execute_media_command(
                    command,
                    model=self.current_model
                )
                self._complete_ffmpeg_progress(index, len(commands))
        except Exception as e:
            self.notify(f"Error executing command: {e}", severity="error")
            self._update_preview(f"[bold red]Error:[/bold red] {str(e)}")
            self.is_processing = False
            self._enable_input_controls()
            self._finish_ffmpeg_progress(error=str(e))
        finally:
            self._executing_batch = False
            self.is_processing = False
            self.pending_commands = []
            self._update_execute_label(0)
            self._enable_input_controls()
            self._enable_preview_actions()
            self._disable_cancel_action()
            self._finish_ffmpeg_progress()
            self._execution_worker = None

    def _extract_media_command(self, content: str) -> str | None:
        """Extract the first media command from Copilot response content"""
        commands = self._extract_media_commands(content)
        return commands[0] if commands else None

    def _extract_media_commands(self, content: str) -> list[str]:
        """Extract all ffmpeg/magick commands from Copilot response content"""
        commands: list[str] = []
        seen: set[str] = set()

        def add_command(command: str):
            command = command.strip()
            if not command or command in seen:
                return
            seen.add(command)
            commands.append(command)

        code_blocks = re.findall(r"```(?:bash|sh|shell|text)?\n(.*?)```", content, re.DOTALL | re.IGNORECASE)
        for block in code_blocks:
            for command in self._extract_commands_from_block_all(block, MEDIA_COMMAND_PREFIXES):
                add_command(command)

        for line in content.splitlines():
            match = re.search(r"^\s*(ffmpeg|magick|convert)\b.*", line, re.IGNORECASE)
            if match:
                add_command(match.group(0))

        return commands

    def _prepare_command_for_execution(self, command: str) -> str | None:
        """Replace input file names with absolute paths for execution"""
        if not self.selected_files:
            return None

        updated_command = command
        for file_path in self.selected_files:
            name = file_path.name
            abs_path = str(file_path.resolve())
            quoted_abs = shlex.quote(abs_path)

            replacements = {
                name: quoted_abs,
                f"./{name}": quoted_abs,
            }

            for original, replacement in replacements.items():
                updated_command = re.sub(
                    rf"(?<![\w./-]){re.escape(original)}(?![\w./-])",
                    replacement,
                    updated_command,
                )

        tool_name = self._infer_command_tool(updated_command)
        return self._rewrite_output_paths(updated_command, tool_name)

    def _prepare_commands_for_execution(self, commands: list[str]) -> list[str]:
        """Prepare a list of commands for execution with absolute paths"""
        prepared: list[str] = []
        for command in commands:
            updated = self._prepare_command_for_execution(command)
            if updated:
                prepared.append(updated)
        return prepared

    def _ensure_output_directory(self) -> None:
        """Ensure the output directory exists"""
        try:
            self.output_directory.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            self.notify(f"Unable to create output directory: {exc}", severity="error")

    def _rewrite_output_paths(self, command: str, tool_name: str) -> str:
        """Rewrite output file paths to the configured output directory"""
        try:
            tokens = shlex.split(command)
        except ValueError:
            return command

        if not tokens:
            return command

        input_paths = {str(path.resolve()) for path in self.selected_files}
        input_names = {path.name for path in self.selected_files}
        media_exts = {
            ".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v", ".3gp", ".mpeg", ".mpg",
            ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif", ".svg", ".heic", ".heif", ".avif", ".ico",
            ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".opus", ".wma",
        }

        rewritten = []
        skip_next = False
        for idx, token in enumerate(tokens):
            if skip_next:
                rewritten.append(token)
                skip_next = False
                continue

            if tool_name == "ffmpeg" and token == "-i":
                rewritten.append(token)
                skip_next = True
                continue

            if token.startswith("-"):
                rewritten.append(token)
                continue

            token_path = Path(token)
            token_suffix = token_path.suffix.lower()

            is_input = token in input_paths or token_path.name in input_names
            is_media_file = token_suffix in media_exts

            if is_media_file and not is_input:
                output_name = token_path.name if token_path.name else f"output{token_suffix}"
                output_path = self.output_directory / output_name
                rewritten.append(str(output_path))
            else:
                rewritten.append(token)

        return shlex.join(rewritten)

    @staticmethod
    def _extract_commands_from_block_all(block: str, prefixes: tuple[str, ...]) -> list[str]:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        commands: list[str] = []
        idx = 0
        while idx < len(lines):
            line = lines[idx]
            line_lower = line.lower()
            if any(line_lower.startswith(prefix) for prefix in prefixes):
                parts = [line]
                idx += 1
                while idx < len(lines):
                    next_line = lines[idx]
                    if next_line.startswith("#"):
                        idx += 1
                        continue
                    if parts[-1].endswith("\\"):
                        parts[-1] = parts[-1][:-1].rstrip()
                        parts.append(next_line)
                        idx += 1
                        continue
                    break
                commands.append(" ".join(parts).strip())
                continue
            idx += 1

        return commands

    @staticmethod
    def _infer_command_tool(command: str) -> str:
        try:
            tokens = shlex.split(command)
        except ValueError:
            return "ffmpeg"

        if not tokens:
            return "ffmpeg"

        first = tokens[0].lower()
        if first in {"magick", "convert"}:
            return "magick"
        return "ffmpeg"

    def _update_execute_label(self, count: int):
        """Update the execute button label with available command count"""
        label = "Execute" if count <= 1 else f"Execute ({count})"
        self.query_one("#execute-btn", Button).label = label

    def _start_ffmpeg_progress(self, total_commands: int) -> None:
        self._ffmpeg_command_total = total_commands
        self._ffmpeg_command_index = 0
        container = self.query_one("#ffmpeg-progress-container")
        container.remove_class("ffmpeg-progress-hidden")
        self._set_ffmpeg_progress(0, f"0/{total_commands}")

    def _reset_ffmpeg_progress(self, command_index: int, total_commands: int) -> None:
        self._ffmpeg_command_index = command_index
        self._ffmpeg_command_total = total_commands
        self._set_ffmpeg_progress(command_index - 1, f"{command_index - 1}/{total_commands}")

    def _complete_ffmpeg_progress(self, command_index: int, total_commands: int) -> None:
        if command_index >= total_commands:
            self._set_ffmpeg_progress(total_commands, f"{total_commands}/{total_commands}")
        else:
            self._set_ffmpeg_progress(command_index, f"{command_index}/{total_commands}")

    def _finish_ffmpeg_progress(self, error: str | None = None) -> None:
        if error:
            self._set_ffmpeg_progress(0, "Error")
        container = self.query_one("#ffmpeg-progress-container")
        container.add_class("ffmpeg-progress-hidden")

    def _set_ffmpeg_progress(self, progress_value: float, label: str) -> None:
        progress_bar = self.query_one("#ffmpeg-progress", ProgressBar)
        if self._ffmpeg_command_total > 0:
            progress_bar.total = self._ffmpeg_command_total
        progress_bar.update(progress=int(max(0, min(self._ffmpeg_command_total, progress_value))))
        label_widget = self.query_one("#ffmpeg-progress-label", Label)
        label_widget.update(f"Conversion Progress · {label}")
    
    def _handle_refine(self):
        """Handle refine button press - allows user to modify instruction"""
        # Focus back on instruction input for refinement
        instruction_input = self.query_one("#instruction-input", VimTextArea)
        instruction_input.focus()
        self.notify("Modify your instruction and submit again", severity="information")
    
    def _handle_clear_preview(self):
        """Handle clear preview button press"""
        self.current_response = ""
        self.pending_commands = []
        self._update_execute_label(0)
        self._update_preview("")
        self._disable_preview_actions()
        self._disable_cancel_action()
        self.notify("Preview cleared", severity="information")

    @work(exclusive=True)
    async def _cancel_copilot(self):
        """Cancel any in-flight Copilot session requests"""
        try:
            await self.copilot_service.cancel()
        except Exception as exc:
            self.notify(f"Cancel request failed: {exc}", severity="warning")
    
    def action_add_files(self):
        """Open file browser to add more files"""
        from conviertlo.screens.file_browser_screen import FileBrowserScreen
        
        def handle_file_selection(new_files):
            """Callback to handle newly selected files"""
            if new_files:
                # Add new files that aren't already selected
                added_count = 0
                for file_path in new_files:
                    if file_path not in self.selected_files:
                        self.selected_files.append(file_path)
                        added_count += 1
                
                if added_count > 0:
                    self.notify(f"Added {added_count} file(s)")
                    self._refresh_file_list()
                else:
                    self.notify("All selected files were already in the list", severity="warning")
        
        self.app.push_screen(FileBrowserScreen(), handle_file_selection)
    
    def action_clear_all(self):
        """Clear all selected files"""
        if self.selected_files:
            count = len(self.selected_files)
            self.selected_files.clear()
            self.notify(f"Removed {count} file(s)")
            self._refresh_file_list()
    
    def action_remove_selected(self):
        """Remove the currently highlighted file from the list"""
        files_list = self.query_one("#files-list", ListView)
        if files_list.highlighted_child:
            item = files_list.highlighted_child
            if isinstance(item, FileListItem):
                self._remove_file(item.file_path)
    
    def _remove_file(self, file_path: Path):
        """Remove a specific file from the selection"""
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)
            self.notify(f"Removed {file_path.name}")
            self._refresh_file_list()
    
    def _refresh_file_list(self):
        """Refresh the file list display"""
        if not self.selected_files:
            # If no files left, go back to welcome screen
            self.notify("No files selected. Returning to welcome screen.")
            self.app.pop_screen()
            return
        
        # Update the ListView with new items
        files_list = self.query_one("#files-list", ListView)
        files_list.clear()
        for file_path in self.selected_files:
            files_list.append(FileListItem(file_path))

    def action_move_down(self):
        file_list = self.query_one("#files-list", ListView)
        file_list.action_cursor_down()

    def action_move_up(self):
        file_list = self.query_one("#files-list", ListView)
        file_list.action_cursor_up()
    
    def action_focus_instruction(self):
        """Focus the instruction input textarea"""
        instruction_input = self.query_one("#instruction-input", VimTextArea)
        instruction_input.focus()

    def action_focus_files(self):
        """Focus the selected files list"""
        files_list = self.query_one("#files-list", ListView)
        files_list.focus()
