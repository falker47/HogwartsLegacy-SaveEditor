"""
Editor process module for Hogwarts Legacy Save Editor.
Handles the WebView-based save editor in a separate process.
"""

import base64
import subprocess
from pathlib import Path
from typing import Callable, Optional


def get_editor_bridge_js(app_dir: str) -> str:
    """
    Load the editor bridge JavaScript from the assets folder.
    Falls back to inline JS if file not found.
    
    Args:
        app_dir: Application directory to find assets folder.
    """
    try:
        js_path = Path(app_dir) / "assets" / "editor_bridge.js"
        if js_path.exists():
            return js_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Warning: Could not load editor_bridge.js: {e}")
    
    # Fallback inline JS (minimal version)
    return """
    (function() {
        async function tryLoad() {
            if (typeof pywebview === 'undefined') { setTimeout(tryLoad, 500); return; }
            try {
                const b64 = await pywebview.api.get_file_data();
                const fileName = await pywebview.api.get_file_name();
                if (!b64) return;
                const binary = atob(b64);
                const bytes = new Uint8Array(binary.length);
                for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
                const file = new File([bytes], fileName, {type: 'application/octet-stream'});
                const input = document.querySelector('input[type="file"]');
                if (input) {
                    const dt = new DataTransfer();
                    dt.items.add(file);
                    input.files = dt.files;
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                }
            } catch(e) { console.error('Auto-load failed:', e); }
        }
        setTimeout(tryLoad, 1000);
    })();
    """


class EditorApi:
    """
    Python API exposed to JavaScript in the WebView editor.
    Handles file loading, saving, and window management.
    """

    def __init__(
        self,
        file_path: str,
        file_name: str,
        original_save: str,
        hlsaves_path: str,
        app_dir: str,
        status_callback: Optional[Callable[[str, str], None]] = None
    ):
        self.file_path = file_path
        self.file_name = file_name
        self.original_save = original_save
        self.hlsaves_path = hlsaves_path
        self.app_dir = app_dir
        self.status_callback = status_callback
        self._window = None

    def set_window(self, window) -> None:
        """Set the WebView window reference for closing."""
        self._window = window

    def _write_status(self, status: str, message: str = "") -> None:
        """Report status via callback if available."""
        if self.status_callback:
            self.status_callback(status, message)

    def get_file_data(self) -> Optional[str]:
        """
        Read the decompressed save file and return as base64.
        Called from JavaScript to load the file into the editor.
        """
        try:
            with open(self.file_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except (IOError, OSError) as e:
            print(f"Error reading file: {e}")
            return None

    def get_file_name(self) -> str:
        """Return the filename for the editor."""
        return self.file_name

    def save_edited_file(self, b64_data: str) -> dict:
        """
        Save the edited file and recompress to original save location.
        Called from JavaScript when user clicks Download.
        
        Args:
            b64_data: Base64-encoded edited file data.
            
        Returns:
            Dictionary with 'success' boolean and optional 'error' message.
        """
        try:
            edited_path = Path(self.file_path).parent / f"{Path(self.file_name).stem}.edited"

            binary = base64.b64decode(b64_data)
            with open(edited_path, 'wb') as f:
                f.write(binary)

            result = subprocess.run(
                [self.hlsaves_path, "-c", str(edited_path), self.original_save],
                capture_output=True, text=True, cwd=self.app_dir
            )

            if result.returncode != 0:
                self._write_status("error", result.stderr)
                return {"success": False, "error": result.stderr}

            self._write_status("success", "Save updated successfully!")
            return {"success": True}

        except (IOError, OSError, subprocess.SubprocessError) as e:
            self._write_status("error", str(e))
            return {"success": False, "error": str(e)}

    def close_window(self) -> None:
        """Close the editor window."""
        if self._window:
            self._window.destroy()


def launch_editor_process(
    html_path: str,
    file_path: str,
    file_name: str,
    original_save: str,
    hlsaves_path: str,
    app_dir: str,
    status_file: str,
    screen_width: int,
    screen_height: int
) -> None:
    """
    Launch the WebView editor in a separate process.
    
    This function is designed to be called via multiprocessing.Process.
    It handles its own imports to avoid serialization issues.
    
    Args:
        html_path: Path to the HLSGE.html editor file.
        file_path: Path to the decompressed save file.
        file_name: Name of the save file.
        original_save: Path to the original .sav file.
        hlsaves_path: Path to hlsaves.exe.
        app_dir: Application directory for subprocess working directory.
        status_file: Path to status file for IPC.
        screen_width: Screen width for window positioning.
        screen_height: Screen height for window positioning.
    """

    def write_status(status: str, message: str = "") -> None:
        """Write status to file for main process to read."""
        try:
            with open(status_file, 'w') as f:
                f.write(f"{status}|{message}")
        except IOError as e:
            print(f"Failed to write status: {e}")

    try:
        import webview

        # Create API with status callback
        api = EditorApi(
            file_path, file_name, original_save,
            hlsaves_path, app_dir, write_status
        )

        # Position on right side (55% of screen)
        manager_width = int(screen_width * 0.45)
        editor_width = screen_width - manager_width
        editor_height = screen_height - 50  # Leave taskbar space
        editor_x = manager_width
        editor_y = 0

        # Use file:// URI to force direct file loading
        file_uri = Path(html_path).as_uri()

        window = webview.create_window(
            'Hogwarts Legacy Save Editor',
            file_uri,
            width=editor_width, height=editor_height,
            x=editor_x, y=editor_y,
            js_api=api
        )
        api.set_window(window)

        def on_loaded():
            js = get_editor_bridge_js(app_dir)
            window.evaluate_js(js)

        write_status("editing", "Editor opened")
        webview.start(on_loaded)

    except ImportError as e:
        write_status("error", f"WebView not available: {e}")
    except Exception as e:
        write_status("error", str(e))
