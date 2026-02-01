"""Vim-enabled TextArea widget with modal editing"""
from enum import Enum
from textual.reactive import reactive
from textual.widgets import TextArea
from textual.events import Key


class MODES(str, Enum):
    """Vim editing modes"""
    NORMAL = 'normal'
    INSERT = 'insert'


class VimTextArea(TextArea):
    """TextArea with Vim-like modal editing"""
    
    mode = reactive(MODES.NORMAL)
    
    def watch_mode(self, new_mode: MODES) -> None:
        """Toggle read-only based on mode"""
        match new_mode:
            case MODES.NORMAL:
                self.read_only = True
            case MODES.INSERT:
                self.read_only = False
    
    def _on_key(self, event: Key) -> None:
        """Handle key events for vim motions"""
        if self.mode == MODES.NORMAL:
            self._handle_normal_mode(event)
        elif self.mode == MODES.INSERT:
            self._handle_insert_mode(event)
    
    def _handle_normal_mode(self, event: Key) -> None:
        """Handle key presses in normal mode"""
        # Enter insert mode
        if event.character in ['i', 'I', 'a', 'A']:
            self._enter_insert_mode(event.character)
            event.prevent_default()
        # Navigate with hjkl
        elif event.character in ['h', 'j', 'k', 'l', 'w', 'b']:
            self._navigate(event.character)
            event.prevent_default()
        # Delete operations
        elif event.character in ['d', 'x']:
            self._delete_operation(event.character)
            event.prevent_default()
    
    def _handle_insert_mode(self, event: Key) -> None:
        """Handle key presses in insert mode"""
        if event.key in ["escape", "ctrl+c"]:
            self.mode = MODES.NORMAL
            event.prevent_default()
    
    def _enter_insert_mode(self, character: str) -> None:
        """Enter insert mode with different starting positions"""
        self.mode = MODES.INSERT
        
        match character:
            case 'i':
                # Insert at cursor
                pass
            case 'I':
                # Insert at beginning of line
                self.move_cursor((self.cursor_location[0], 0))
            case 'a':
                # Append after cursor
                self.move_cursor_relative(columns=1)
            case 'A':
                # Append at end of line
                line = self.cursor_location[0]
                line_length = len(self.text.split('\n')[line]) if line < len(self.text.split('\n')) else 0
                self.move_cursor((line, line_length))
    
    def _navigate(self, character: str) -> None:
        """Navigate the cursor using vim motions"""
        match character:
            case 'h':
                # Move left
                self.action_cursor_left()
            case 'j':
                # Move down
                self.action_cursor_down()
            case 'k':
                # Move up
                self.action_cursor_up()
            case 'l':
                # Move right
                self.action_cursor_right()
            case 'w':
                # Move to next word
                self.action_cursor_word_right()
            case 'b':
                # Move to previous word
                self.action_cursor_word_left()
    
    def _delete_operation(self, character: str) -> None:
        """Handle delete operations"""
        match character:
            case 'x':
                # Delete character under cursor
                if self.selection.start != self.selection.end:
                    self.delete(*self.selection)
                else:
                    cursor = self.cursor_location
                    # Delete one character at cursor position
                    end_pos = (cursor[0], cursor[1] + 1)
                    self.delete(cursor, end_pos)
            case 'd':
                # dd deletes line (would need to track second 'd')
                # For now, just delete selected text if any
                if self.selection.start != self.selection.end:
                    self.delete(*self.selection)
