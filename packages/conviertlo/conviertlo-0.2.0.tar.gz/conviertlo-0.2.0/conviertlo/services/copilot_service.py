"""GitHub Copilot SDK service for generating media conversion commands"""
from typing import Callable, Optional, Any
import inspect
import shlex
from pathlib import Path
from copilot import CopilotClient


class CopilotService:
    """Service for interacting with GitHub Copilot SDK"""

    IMAGE_EXTENSIONS = {
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif", ".svg",
        ".heic", ".heif", ".avif", ".ico",
    }
    VIDEO_EXTENSIONS = {
        ".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v",
        ".3gp", ".mpeg", ".mpg", ".ts",
    }
    AUDIO_EXTENSIONS = {
        ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".opus", ".wma",
    }
    
    def __init__(self):
        """Initialize the Copilot service"""
        self.client: Optional[CopilotClient] = None
        self.session = None
        self._event_handlers: list[Callable[[dict], None]] = []
        self._is_started = False
        self._current_session_model: Optional[str] = None  # Track which model the current session uses
    
    async def start(self):
        """Start the Copilot client"""
        if not self._is_started:
            # Default client initialization per SDK docs
            self.client = CopilotClient()
            await self.client.start()
            self._is_started = True
    
    async def stop(self):
        """Stop the Copilot client"""
        if self._is_started:
            if self.session:
                await self.session.destroy()
                self.session = None
            if self.client:
                await self.client.stop()
                self.client = None
            self._is_started = False
    
    async def create_session(self, model: str = "Claude Sonnet 4.5"):
        """Create a new Copilot session
        
        Args:
            model: The model to use (e.g., "gpt-4o", "claude-sonnet-4.5")
        """
        # Auto-start if not already started
        if not self._is_started:
            await self.start()
        
        # Skip if we already have a session with the same model
        if self.session and self._current_session_model == model:
            return self.session
        
        # Destroy existing session if any (with timeout protection)
        if self.session:
            try:
                await self.session.destroy()
            except Exception:
                pass  # Ignore errors during cleanup
            self.session = None
            self._current_session_model = None
        
        # Create new session with model config as dictionary
        self.session = await self.client.create_session({"model": model})
        self._current_session_model = model
        
        # Register event handler
        self.session.on(self._handle_event)
        
        return self.session
    
    async def destroy_session(self):
        """Destroy the current session"""
        if self.session:
            try:
                await self.session.destroy()
            except Exception:
                pass  # Ignore errors during cleanup
            self.session = None
            self._current_session_model = None

    async def cancel(self):
        """Cancel any in-flight Copilot request for the current session"""
        if not self.session:
            return

        abort_fn = getattr(self.session, "abort", None)
        if callable(abort_fn):
            try:
                result = abort_fn()
                if inspect.isawaitable(result):
                    await result
            except Exception:
                pass
    
    def on_event(self, handler: Callable[[dict], None]):
        """Register an event handler
        
        Args:
            handler: Callback function that receives event dictionaries
        """
        if handler not in self._event_handlers:
            self._event_handlers.append(handler)
    
    def off_event(self, handler: Callable[[dict], None]):
        """Unregister an event handler
        
        Args:
            handler: The callback function to remove
        """
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)
    
    def _handle_event(self, event: dict):
        """Internal event handler that broadcasts to all registered handlers"""
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                # Log error but continue processing other handlers
                print(f"Error in event handler: {e}")
    
    async def send_conversion_request(self, instruction: str, files: list[Path], model: str = "Claude Sonnet 4.5"):
        """Send a conversion instruction to Copilot
        
        Args:
            instruction: Natural language instruction from the user
            files: List of file paths to convert
            model: The model to use for this request
        """
        # Ensure we have a session with the correct model (lazy creation)
        await self.create_session(model=model)
        
        if not self.session:
            raise RuntimeError("Failed to create session.")
        
        # Build file metadata string
        file_info = []
        for file_path in files:
            try:
                size_bytes = file_path.stat().st_size
                size_str = self._format_file_size(size_bytes)
                media_type = self._classify_media_type(file_path)
                file_info.append(
                    f"- {file_path.name} ({size_str}, format: {file_path.suffix.upper().replace('.', '')}, type: {media_type})"
                )
            except Exception:
                media_type = self._classify_media_type(file_path)
                file_info.append(
                    f"- {file_path.name} (format: {file_path.suffix.upper().replace('.', '')}, type: {media_type})"
                )
        
        files_str = "\n".join(file_info)
        
        # Construct the prompt
        prompt = f"""You are a professional media command generator. Your job is to return ONLY the final command(s) that should be executed.

    Critical rules:
    - Use FFMPEG (ffmpeg) for video or audio files.
    - Use ImageMagick (magick) for image files.
    - Do NOT include suggestions, alternatives, or optional commands.
    - Do NOT include placeholder text.
    - Do NOT include commands that should NOT be executed.
    - Provide the BEST possible command(s) from the start (optimize for quality, compatibility, and safety).
    - If multiple files require separate commands, output only those exact commands.
    - Never overwrite input files or use in-place editing (do not use mogrify).
    - All output files must be saved into the directory: ~/conviertlo/ using full output paths.
    - When having to run multiple commands, separate them so execution is sequential, Do NOT use command chaining with "&&".
    - If both image and video/audio files are selected, output the appropriate tool per file.
    - Use `magick` (not `convert`) for ImageMagick commands unless absolutely required.

    Selected Files:
    {files_str}

    User Instruction: {instruction}

    Response format (strict):
    1. An "EXECUTE" section containing only the exact command(s) to run, inside a single code block.
    2. Explanation paragraphs explaining each command's purpose (no extra commands).
    3. Warnings/notes paragraph if needed (no extra commands).
    """
        
        print(f"[CopilotService] Sending prompt to Copilot via send_and_wait...")
        try:
            # Send the prompt with config as dictionary
            response = await self.session.send_and_wait({"prompt": prompt})
            print(f"[CopilotService] send_and_wait returned successfully. Response type: {type(response)}")
            
            # If events weren't triggered (likely with send_and_wait), manually notify handlers
            if hasattr(response, 'data') and hasattr(response.data, 'content'):
                content = response.data.content
                print(f"[CopilotService] Response content length: {len(content)}")
                
                # Simulate message event with full content
                # This ensures the UI gets the content even if streaming events didn't fire
                self._handle_event({
                    "type": "assistant.message",
                    "data": {"content": content}
                })
                
                # Simulate completion event to unblock UI
                self._handle_event({
                    "type": "assistant.message_complete"
                })
            
            return response
            
        except Exception as e:
            print(f"[CopilotService] Error in send_and_wait: {e}")
            # Ensure UI gets unblocked even on error
            self._handle_event({
                "type": "error",
                "data": {"message": str(e)}
            })
            raise e

    async def execute_media_command(self, command: str, model: str = "Claude Sonnet 4.5"):
        """Ask Copilot to execute a pre-approved media command

        Args:
            command: The full media command to execute (ffmpeg or magick)
            model: The model to use for this request
        """
        await self.create_session(model=model)

        if not self.session:
            raise RuntimeError("Failed to create session.")

        tool_name = self._infer_command_tool(command)
        tool_label = "shell(ffmpeg)" if tool_name == "ffmpeg" else "shell(magick)"
        tool_desc = "FFMPEG" if tool_name == "ffmpeg" else "ImageMagick"

        prompt = f"""Execute the following {tool_desc} command using the {tool_label} tool.
The user has approved the command. Only run the command and report the result.

Command:
{command}
"""

        try:
            response = await self.session.send_and_wait({"prompt": prompt})

            # If events weren't triggered, manually notify handlers
            if hasattr(response, 'data') and hasattr(response.data, 'content'):
                content = response.data.content
                self._handle_event({
                    "type": "assistant.message",
                    "data": {"content": content}
                })
                self._handle_event({
                    "type": "assistant.message_complete"
                })

            return response

        except Exception as e:
            self._handle_event({
                "type": "error",
                "data": {"message": str(e)}
            })
            raise e

    async def execute_ffmpeg_command(self, command: str, model: str = "Claude Sonnet 4.5"):
        """Backward-compatible wrapper for ffmpeg execution"""
        return await self.execute_media_command(command, model=model)
        
    async def wait_for_response(self):
        """Wait for Copilot to finish processing"""
        if self.session:
            await self.session.wait_for_idle()
    
    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    @classmethod
    def _classify_media_type(cls, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        if suffix in cls.IMAGE_EXTENSIONS:
            return "image"
        if suffix in cls.VIDEO_EXTENSIONS:
            return "video"
        if suffix in cls.AUDIO_EXTENSIONS:
            return "audio"
        return "unknown"

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
