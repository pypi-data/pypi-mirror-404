# Conviertlo

**FFMPEG Copilot Converter**

`conviertlo` is a powerful Terminal User Interface (TUI) tool that lets you convert and compress media files using natural language instructions. Powered by FFMPEG and GitHub Copilot, it translates requests like "compress this video to under 25MB" or "convert these images to PNG" into precise FFMPEG commands.

## Features

*   **Natural Language Commands**: Just type what you want to do (e.g., "Extract audio as MP3", "Resize to 720p").
*   **Intelligent FFMPEG Generation**: Uses GitHub Copilot to generate complex FFMPEG flags so you don't have to memorize them.
*   **Visual File Browser**: Navigate and select media files directly in the terminal.
*   **Command Preview**: Review and execute generated commands with safety checks.
*   **Batch Processing**: Handle multiple files at once.
*   **Real-time Progress**: Monitor conversion status with visual progress bars.

## Prerequisites

1.  **Python 3.10+**
2.  **FFMPEG**: Must be installed and available in your system PATH.
    *   Ubuntu/Debian: `sudo apt install ffmpeg`
    *   macOS: `brew install ffmpeg`
    *   Windows: `winget install ffmpeg`
3.  **GitHub Copilot Access**: This tool requires active GitHub Copilot access.

## Installation

```bash
pip install conviertlo
```

## How to Use

1.  **Start the application:**
    ```bash
    conviertlo
    ```

2.  **Select Files:**
    *   From the Welcome Screen, press `f` or use the file browser to select the media files you want to process.

3.  **Enter Instructions:**
    *   In the Instruction Screen, type your goal in plain English.
    *   *Examples:*
        *   "Convert to MP4 and keep quality high"
        *   "Compress to 5MB for Discord"
        *   "Extract frames every 10 seconds"
        *   "Rotate video 90 degrees clockwise"

4.  **Execute:**
    *   Press `Ctrl+g` to generate the command.
    *   Review the generated FFMPEG command in the preview panel.
    *   Press `Ctrl+e` to execute the conversion.

## Keybindings

### Global / Welcome Screen
| Key | Action |
| --- | --- |
| `f` | Open File Browser |

### File Browser
| Key | Action |
| --- | --- |
| `Alt+Enter` | Confirm Selection |
| `Esc` / `Ctrl+c` | Cancel |
| `j` / `Down` | Move Down |
| `k` / `Up` | Move Up |

### Instruction Screen
| Key | Action | Description |
| --- | --- | --- |
| `Ctrl+g` / `Ctrl+Enter` | Generate Command | Submit instruction to Copilot |
| `Ctrl+e` | Execute | Run the generated FFMPEG command |
| `Ctrl+r` | Refine | Focus input to refine the instruction |
| `Ctrl+a` | Add Files | Open file browser to add more files |
| `D` / `Delete` | Remove Selected | Remove highlighted file from list |
| `Ctrl+d` | Clear All | Remove all selected files |
| `Ctrl+m` | Change Model | Switch AI model |
| `Ctrl+c` | Cancel | Cancel current processing/execution |
| `Esc` | Go Back | Return to previous screen |
| `Ctrl+i` | Focus Input | Focus the instruction text area |
| `Ctrl+l` | Focus Files | Focus the files list |

## License

MIT

---
Built with [Textual](https://textual.textualize.io/) and [GitHub Copilot SDK](https://github.com/github-copilot-resources/github-copilot-sdk).
