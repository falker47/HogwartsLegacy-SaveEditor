"""
Main application module for Hogwarts Legacy Save Editor.
Contains the App class and all UI logic.
"""

import hashlib
import multiprocessing
import os
import shutil
import subprocess
import sys
import threading
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import List, Optional, Tuple

import customtkinter as ctk

# Try drag-drop support (optional)
try:
    from tkinterdnd2 import TkinterDnD
    TKDND_AVAILABLE = True
except ImportError:
    TKDND_AVAILABLE = False

from .config import (
    APP_NAME, APPEARANCE_MODE, BACKGROUND_COLOR, COLOR_THEME,
    DLL_DOWNLOAD_URL, DLL_NAME, EXPECTED_DLL_HASH, HLSAVES_EXE, HLSGE_HTML,
    INFO_PANEL_COLOR, MAIN_BUTTON_FG_COLOR, MAIN_BUTTON_HOVER_COLOR,
    MIN_HEIGHT, MIN_WIDTH, SELECTED_BORDER_COLOR, SELECTED_COLOR, TASKBAR_HEIGHT
)
from .editor import launch_editor_process
from .utils import format_file_size, parse_save_filename


# Choose base class based on drag-drop availability
BaseWindow = TkinterDnD.Tk if TKDND_AVAILABLE else ctk.CTk


class App(BaseWindow):
    """Main application window for Hogwarts Legacy Save Editor."""

    def __init__(self):
        super().__init__()

        self.title(APP_NAME)

        # Position on left side (45% of screen)
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = int(screen_width * 0.45)
        window_height = screen_height - TASKBAR_HEIGHT
        self.geometry(f"{window_width}x{window_height}+0+0")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)

        ctk.set_appearance_mode(APPEARANCE_MODE)
        ctk.set_default_color_theme(COLOR_THEME)
        self.configure(bg=BACKGROUND_COLOR)

        # Paths
        if getattr(sys, 'frozen', False):
            self.app_dir = Path(sys.executable).parent
        else:
            self.app_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent

        self.hlsaves_exe = self.app_dir / HLSAVES_EXE
        self.hlsge_html = self.app_dir / HLSGE_HTML
        self.temp_dir = self.app_dir / "temp"

        # Backup dir will be set after detecting save directory
        self.backup_dir: Optional[Path] = None

        # State
        self.save_directory: Optional[Path] = None
        self.save_files: List[Tuple[Path, datetime]] = []
        self.current_save_file: Optional[Path] = None
        self.current_decomp_file: Optional[Path] = None
        self.selected_button: Optional[ctk.CTkButton] = None
        self.editor_process: Optional[multiprocessing.Process] = None
        self.is_working = False

        # Create temp dir
        self.temp_dir.mkdir(exist_ok=True)

        # Build UI
        self._create_ui()

        # Verify files
        if not self._verify_required_files():
            pass  # Continue to let user read errors

        self._detect_save_directory()

    def _verify_dll_hash(self, dll_path: Path) -> bool:
        """Verify the SHA256 hash of the DLL file."""
        try:
            sha256_hash = hashlib.sha256()
            with open(dll_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256_hash.update(chunk)
            actual_hash = sha256_hash.hexdigest().lower()
            return actual_hash == EXPECTED_DLL_HASH
        except (IOError, OSError) as e:
            print(f"Hash verification error: {e}")
            return False

    def _download_dll_from_web(self) -> bool:
        """Download oo2core_9_win64.dll from modding.wiki and verify its hash."""
        target_path = self.app_dir / DLL_NAME

        try:
            self._log("⬇️ Downloading DLL from modding.wiki...")
            urllib.request.urlretrieve(DLL_DOWNLOAD_URL, target_path)

            if self._verify_dll_hash(target_path):
                self._log("✅ DLL downloaded and verified successfully!")
                messagebox.showinfo("Download Complete",
                    f"Successfully downloaded and verified {DLL_NAME}!")
                return True
            else:
                self._log("⚠️ Downloaded DLL hash verification failed!")
                target_path.unlink(missing_ok=True)
                messagebox.showwarning("Verification Failed",
                    "The downloaded DLL failed hash verification.\n\n"
                    "The file may be corrupted or modified.\n"
                    "Please search for the DLL in your PC instead.")
                return False

        except urllib.error.URLError as e:
            self._log(f"❌ Download failed: {e.reason}")
            messagebox.showwarning("Download Failed",
                f"Could not download from modding.wiki:\n{e.reason}\n\n"
                "Please search for the DLL in your PC instead.")
            return False
        except (IOError, OSError) as e:
            self._log(f"❌ Download error: {e}")
            messagebox.showwarning("Download Error",
                f"Error downloading DLL:\n{e}\n\n"
                "Please search for the DLL in your PC instead.")
            return False

    def _find_and_copy_dll(self) -> bool:
        """Attempt to find and copy oo2core_9_win64.dll from game installations."""
        target_path = self.app_dir / DLL_NAME

        # Check specific hardcoded paths first (fastest)
        fast_paths = [
            Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hogwarts Legacy\Engine\Binaries\ThirdParty\Oodle\Win64\oo2core_9_win64.dll"),
            Path(r"C:\Program Files\Epic Games\Hogwarts Legacy\Engine\Binaries\ThirdParty\Oodle\Win64\oo2core_9_win64.dll"),
        ]

        for path in fast_paths:
            if path.exists():
                try:
                    print(f"Found DLL at (Fast Path): {path}")
                    shutil.copy2(path, target_path)
                    messagebox.showinfo("Auto-Setup",
                        f"Successfully found and copied {DLL_NAME}!\n\n"
                        f"Source: {path}\n(Hogwarts Legacy folder)")
                    return True
                except (IOError, OSError, shutil.Error) as e:
                    print(f"Failed to copy from {path}: {e}")

        # Dynamic search in library roots
        drives = [f"{d}:\\" for d in "CDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
        search_roots = []

        for drive in drives:
            # Steam Paths
            search_roots.append(Path(drive) / "Program Files (x86)" / "Steam" / "steamapps" / "common")
            search_roots.append(Path(drive) / "SteamLibrary" / "steamapps" / "common")
            # Epic Paths
            search_roots.append(Path(drive) / "Program Files" / "Epic Games")
            search_roots.append(Path(drive) / "Epic Games")

        print("🔍 Starting deep search for DLL in game libraries...")
        self._log("🔍 Searching for DLL in game libraries... this may take a moment.")

        for root in search_roots:
            if not root.exists():
                continue

            print(f"Scanning root: {root}")

            try:
                for game_dir in root.iterdir():
                    if not game_dir.is_dir():
                        continue

                    found = list(game_dir.rglob(DLL_NAME))

                    if found:
                        source = found[0]
                        try:
                            print(f"Found DLL at: {source}")
                            shutil.copy2(source, target_path)
                            self._log(f"✅ Found DLL in {game_dir.name}!")
                            messagebox.showinfo("Auto-Setup",
                                f"Successfully found and copied {DLL_NAME}!\n\n"
                                f"Source: {source}\n(Found in {game_dir.name})")
                            return True
                        except (IOError, OSError, shutil.Error) as e:
                            print(f"Failed copy from {source}: {e}")
            except PermissionError as e:
                print(f"Permission denied scanning {root}: {e}")
            except OSError as e:
                print(f"Error scanning {root}: {e}")

        return False

    def _verify_required_files(self) -> bool:
        """Verify all required files are present."""
        # Check HLSAVES & HLSGE
        missing = []
        if not self.hlsaves_exe.exists():
            missing.append((HLSAVES_EXE, "Save tool by Katt"))
        if not self.hlsge_html.exists():
            missing.append((HLSGE_HTML, "Editor by ekaomk"))

        if missing:
            msg = "Missing files:\n\n"
            for f, d in missing:
                msg += f"❌ {f} - {d}\n"
            msg += f"\nPlace in: {self.app_dir}"
            messagebox.showerror("Missing Files", msg)
            return False

        # Blocking DLL check
        while True:
            dll = self.app_dir / DLL_NAME

            if dll.exists():
                return True

            if self._find_and_copy_dll():
                return True

            self._log(f"❌ REQUIRED FILE MISSING: {DLL_NAME}")

            msg = (
                "⛔ MISSING REQUIRED COMPONENT ⛔\n\n"
                f"The file '{DLL_NAME}' was not found.\n"
                "The app CANNOT work without it.\n\n"
                "Click 'Yes' to DOWNLOAD it (with hash verification)\n"
                "Click 'No' to SEARCH your PC for the file\n"
                "Click 'Cancel' to EXIT\n\n"
                f"App Folder: {self.app_dir}\n"
            )

            choice = messagebox.askyesnocancel("Action Required", msg)

            if choice is None:  # Cancel -> Exit
                self.destroy()
                sys.exit(0)
            elif choice:  # Yes -> Download
                if self._download_dll_from_web():
                    return True
            else:  # No -> Search PC
                self._log("🔍 Searching for DLL on your PC...")
                if self._find_and_copy_dll():
                    return True
                else:
                    messagebox.showinfo("Manual Selection",
                        "Could not find the DLL automatically.\n\n"
                        "Please select the 'oo2core_9_win64.dll' file manually.")

                    file_path = filedialog.askopenfilename(
                        title=f"Select {DLL_NAME}",
                        filetypes=[("DLL files", "*.dll"), ("All files", "*.*")]
                    )

                    if file_path and Path(file_path).name.lower() == DLL_NAME.lower():
                        try:
                            shutil.copy2(file_path, dll)
                            self._log(f"✅ DLL copied from: {file_path}")
                            messagebox.showinfo("Success", "DLL file copied successfully!")
                            return True
                        except (IOError, OSError, shutil.Error) as e:
                            self._log(f"❌ Failed to copy DLL: {e}")
                            messagebox.showerror("Error", f"Failed to copy file: {e}")
                    elif file_path:
                        messagebox.showwarning("Wrong File", f"Please select '{DLL_NAME}'")

        return True

    def _create_ui(self) -> None:
        """Create the main UI layout."""
        main_frame = ctk.CTkFrame(self, fg_color=BACKGROUND_COLOR)
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)

        # LEFT PANEL
        left = ctk.CTkFrame(main_frame)
        left.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(left, fg_color="transparent")
        header.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="📁 Save Files",
            font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w")
        self.path_label = ctk.CTkLabel(header, text="Detecting...",
            font=ctk.CTkFont(size=11), text_color="gray")
        self.path_label.grid(row=1, column=0, sticky="w")

        self.save_list_frame = ctk.CTkScrollableFrame(left)
        self.save_list_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.save_list_frame.grid_columnconfigure(0, weight=1)

        # Info panel
        self.info_frame = ctk.CTkFrame(left, fg_color=INFO_PANEL_COLOR, corner_radius=8)
        self.info_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.info_label = ctk.CTkLabel(self.info_frame, text="Select a save file",
            font=ctk.CTkFont(size=11), text_color="gray", justify="left")
        self.info_label.pack(padx=10, pady=8, anchor="w")

        # Buttons
        btns = ctk.CTkFrame(left, fg_color="transparent")
        btns.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew")
        btns.grid_columnconfigure(0, weight=1)
        btns.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btns, text="🔄 Refresh", command=self._refresh_save_list,
            height=28).grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkButton(btns, text="📁 Browse", command=self._browse_save_directory,
            height=28).grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # RIGHT PANEL
        right = ctk.CTkFrame(main_frame)
        right.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="📋 Status Log",
            font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        self.log_textbox = ctk.CTkTextbox(right,
            font=ctk.CTkFont(family="Consolas", size=12), state="disabled")
        self.log_textbox.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")

        # Actions frame
        actions = ctk.CTkFrame(right, fg_color="transparent")
        actions.grid(row=2, column=0, padx=15, pady=10, sticky="ew")
        actions.grid_columnconfigure(0, weight=1)

        # Main action button
        self.extract_button = ctk.CTkButton(
            actions, text="🔓 Edit Save File", command=self._extract_and_edit,
            height=50, font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=MAIN_BUTTON_FG_COLOR, hover_color=MAIN_BUTTON_HOVER_COLOR
        )
        self.extract_button.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        # Progress indicator (hidden by default)
        self.progress_frame = ctk.CTkFrame(actions, fg_color=INFO_PANEL_COLOR, corner_radius=8)
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, mode="indeterminate", height=8)
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Working...",
            font=ctk.CTkFont(size=12), text_color="#a0a0a0")

        # Info text
        info_text = ctk.CTkLabel(
            actions,
            text="Select a save → Click 'Edit Save File' → Edit in browser → Click Download → Done!",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=400
        )
        info_text.grid(row=2, column=0, pady=(10, 0))

        # Bottom buttons
        bottom = ctk.CTkFrame(right, fg_color="transparent")
        bottom.grid(row=3, column=0, padx=15, pady=(10, 15), sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(bottom, text="📂 Backups", command=self._open_backup_folder,
            height=32).grid(row=0, column=0, padx=(0, 10), sticky="ew")
        ctk.CTkButton(bottom, text="❓ Help", command=self._show_help,
            height=32, width=70, fg_color="gray30", hover_color="gray40").grid(
            row=0, column=1, padx=(0, 5))
        ctk.CTkButton(bottom, text="Credits", command=self._show_credits,
            height=32, width=70, fg_color="gray30", hover_color="gray40").grid(
            row=0, column=2)

        self._log("🧙 Welcome to Hogwarts Legacy Save Manager!")
        self._log("Select a save file and click 'Edit Save File' to begin.")
        self._log("")

    def _show_progress(self, message: str) -> None:
        """Show progress indicator."""
        self.is_working = True
        self.extract_button.configure(state="disabled", text="⏳ Working...")
        self.progress_label.configure(text=message)
        self.progress_frame.grid(row=1, column=0, pady=5, sticky="ew")
        self.progress_label.pack(padx=10, pady=(8, 2))
        self.progress_bar.pack(padx=10, pady=(2, 8), fill="x")
        self.progress_bar.start()
        self.update()

    def _hide_progress(self) -> None:
        """Hide progress indicator."""
        self.is_working = False
        self.progress_bar.stop()
        self.progress_frame.grid_forget()
        self.extract_button.configure(state="normal", text="🔓 Edit Save File")
        self.update()

    def _log(self, msg: str) -> None:
        """Log a message to the status log."""
        if not hasattr(self, "log_textbox"):
            print(f"[LOG] {msg}")
            return

        ts = datetime.now().strftime("%H:%M:%S")
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"[{ts}] {msg}\n" if msg else "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        self.update()

    def _detect_save_directory(self) -> None:
        """Auto-detect the Hogwarts Legacy save directory."""
        base = Path(os.environ.get("LOCALAPPDATA", "")) / "Hogwarts Legacy" / "Saved" / "SaveGames"
        if not base.exists():
            self._log("⚠️ Save dir not found. Use Browse.")
            self.path_label.configure(text="Not found")
            return

        folders = [d for d in base.iterdir() if d.is_dir() and d.name.isdigit()]
        if not folders:
            self._log("⚠️ No user folders.")
            self.path_label.configure(text="No folders")
            return

        folders.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        self.save_directory = folders[0]

        # Create backup dir inside save directory
        self.backup_dir = self.save_directory / "Backups"
        self.backup_dir.mkdir(exist_ok=True)

        self.path_label.configure(text=f".../{folders[0].name}")
        self._log("✅ Found save folder!")
        self._refresh_save_list()

    def _browse_save_directory(self) -> None:
        """Browse for save directory manually."""
        initial = Path(os.environ.get("LOCALAPPDATA", "")) / "Hogwarts Legacy"
        if not initial.exists():
            initial = Path.home()

        d = filedialog.askdirectory(title="Select Save Directory", initialdir=initial)
        if d:
            self.save_directory = Path(d)
            self.backup_dir = self.save_directory / "Backups"
            self.backup_dir.mkdir(exist_ok=True)
            self.path_label.configure(text=f".../{self.save_directory.name}")
            self._log("📁 Directory set.")
            self._refresh_save_list()

    def _refresh_save_list(self) -> None:
        """Refresh the list of save files."""
        for w in self.save_list_frame.winfo_children():
            w.destroy()

        self.save_files = []
        self.current_save_file = None
        self.selected_button = None
        self._update_file_info(None)

        if not self.save_directory or not self.save_directory.exists():
            ctk.CTkLabel(self.save_list_frame, text="No directory",
                text_color="gray").pack(pady=20)
            return

        saves = [f for f in self.save_directory.glob("*.sav") if f.is_file()]
        if not saves:
            ctk.CTkLabel(self.save_list_frame, text="No saves found",
                text_color="gray").pack(pady=20)
            return

        saves.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        for sav in saves:
            stat = sav.stat()
            mod = datetime.fromtimestamp(stat.st_mtime)
            self.save_files.append((sav, mod))

            info = parse_save_filename(sav.name)
            size = format_file_size(stat.st_size)

            btn = ctk.CTkButton(
                self.save_list_frame,
                text=f"🎮 {info['display']}\n   {mod.strftime('%Y-%m-%d %H:%M')}  •  {size}",
                anchor="w", height=55, font=ctk.CTkFont(size=12),
                fg_color="gray25", hover_color="gray35",
                command=lambda f=sav: None
            )
            btn.configure(command=lambda f=sav, b=btn: self._select_save_file(f, b))
            btn.pack(fill="x", pady=2)

        self._log(f"🔄 Found {len(saves)} save(s).")

    def _select_save_file(self, save_file: Path, button: Optional[ctk.CTkButton] = None) -> None:
        """Select a save file."""
        if self.selected_button:
            self.selected_button.configure(fg_color="gray25", border_width=0)

        self.current_save_file = save_file
        self.selected_button = button

        if button:
            button.configure(fg_color=SELECTED_COLOR, border_width=2,
                border_color=SELECTED_BORDER_COLOR)

        self._update_file_info(save_file)
        self._log(f"📌 Selected: {save_file.name}")

    def _update_file_info(self, save_file: Optional[Path]) -> None:
        """Update the file info display."""
        if not save_file:
            self.info_label.configure(text="Select a save file", text_color="gray")
            return

        stat = save_file.stat()
        info = parse_save_filename(save_file.name)
        mod = datetime.fromtimestamp(stat.st_mtime)

        text = (
            f"📄 {save_file.name}\n"
            f"🎮 {info['display']}\n"
            f"📅 {mod.strftime('%Y-%m-%d %H:%M')}\n"
            f"💾 {format_file_size(stat.st_size)}"
        )
        self.info_label.configure(text=text, text_color="#a0a0a0")

    def _extract_and_edit(self) -> None:
        """Extract and edit the selected save file."""
        if self.is_working:
            return

        if not self.current_save_file:
            messagebox.showwarning("No File", "Please select a save file first!")
            return

        if not self.hlsaves_exe.exists():
            messagebox.showerror("Error", f"{HLSAVES_EXE} not found!")
            return

        def do_work():
            try:
                self._show_progress("Creating backup...")
                self._log("📦 Creating backup...")

                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup = self.backup_dir / f"{self.current_save_file.stem}_{ts}.sav.bak"
                shutil.copy2(self.current_save_file, backup)
                self._log("✅ Backup created")

                self._show_progress("Preparing save file...")

                # Copy to temp
                temp_sav = self.temp_dir / self.current_save_file.name
                shutil.copy2(self.current_save_file, temp_sav)

                self._show_progress("Decompressing...")
                self._log("🔓 Decompressing...")

                decomp = self.temp_dir / f"{self.current_save_file.stem}.decomp"
                self.current_decomp_file = decomp

                result = subprocess.run(
                    [str(self.hlsaves_exe), "-d", str(temp_sav), str(decomp)],
                    capture_output=True, text=True, cwd=str(self.app_dir)
                )

                if result.returncode != 0:
                    self._hide_progress()
                    self._log(f"❌ Error: {result.stderr}")
                    messagebox.showerror("Error", f"Decompression failed:\n{result.stderr}")
                    return

                if not decomp.exists():
                    self._hide_progress()
                    self._log("❌ File not created")
                    messagebox.showerror("Error", "Decompression failed.")
                    return

                self._log(f"✅ Decompressed: {decomp.name}")
                self._show_progress("Launching editor...")

                # Launch editor
                try:
                    import webview  # noqa: F401 - Check availability

                    self._log("🌐 Launching editor...")
                    self._hide_progress()

                    # Create status file for communication
                    status_file = self.temp_dir / "editor_status.txt"
                    if status_file.exists():
                        status_file.unlink()

                    # Get screen dimensions
                    screen_width = self.winfo_screenwidth()
                    screen_height = self.winfo_screenheight()

                    self.editor_process = multiprocessing.Process(
                        target=launch_editor_process,
                        args=(
                            str(self.hlsge_html), str(decomp), decomp.name,
                            str(self.current_save_file), str(self.hlsaves_exe),
                            str(self.app_dir), str(status_file),
                            screen_width, screen_height
                        )
                    )
                    self.editor_process.start()

                    self._log("✅ Editor opened!")
                    self._log("")
                    self._log("📝 Edit your save and click 'Download'.")

                    # Monitor status file in background
                    def monitor_status():
                        import time
                        last_status = None
                        while self.editor_process and self.editor_process.is_alive():
                            try:
                                if status_file.exists():
                                    with open(status_file, 'r') as f:
                                        content = f.read().strip()

                                    if content and content != last_status:
                                        last_status = content
                                        parts = content.split('|', 1)
                                        status = parts[0]
                                        message = parts[1] if len(parts) > 1 else ""

                                        if status == "success":
                                            self._log("")
                                            self._log("=" * 45)
                                            self._log("🎉 SAVE UPDATED SUCCESSFULLY!")
                                            self._log("=" * 45)
                                            self._log("✅ Your save is ready to play!")
                                            self._log("")
                                            self._refresh_save_list()
                                        elif status == "error":
                                            self._log(f"❌ Error: {message}")
                            except (IOError, OSError):
                                pass

                            time.sleep(0.5)

                        # Clean up
                        if status_file.exists():
                            try:
                                status_file.unlink()
                            except OSError:
                                pass

                        self._log("📝 Editor closed.")

                    monitor_thread = threading.Thread(target=monitor_status, daemon=True)
                    monitor_thread.start()

                except ImportError:
                    self._hide_progress()
                    self._log("🌐 Opening browser editor...")
                    import webbrowser
                    webbrowser.open(self.hlsge_html.as_uri())
                    os.startfile(self.temp_dir)
                    self._log(f"📂 Drag '{decomp.name}' into browser")

            except Exception as e:
                self._hide_progress()
                self._log(f"❌ Error: {e}")
                messagebox.showerror("Error", str(e))

        # Start in thread
        thread = threading.Thread(target=do_work, daemon=True)
        thread.start()

    def _open_backup_folder(self) -> None:
        """Open the backup folder."""
        if self.backup_dir and self.backup_dir.exists():
            os.startfile(self.backup_dir)
            self._log("📂 Opened backups")
        else:
            messagebox.showinfo("No Backups",
                "No backup folder found yet.\nSelect a save directory first.")

    def _show_help(self) -> None:
        """Show help dialog."""
        messagebox.showinfo("Help", """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   HOGWARTS LEGACY SAVE MANAGER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 HOW TO USE:

1️⃣  Select a save from the list
2️⃣  Click 'Edit Save File'
3️⃣  The editor opens automatically
4️⃣  Make your changes
5️⃣  Click 'Download' in the editor
     ✅ Save is updated automatically!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 REQUIRED FILES (same folder as app):
   • hlsaves.exe - Compression tool
   • HLSGE.html - Save editor
   • oo2core_9_win64.dll - From game

💾 BACKUPS:
   Saved in your game's save folder:
   [SaveGames]/[UserID]/Backups/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

    def _show_credits(self) -> None:
        """Show credits dialog."""
        messagebox.showinfo("Credits", """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   HOGWARTS LEGACY SAVE MANAGER
            Version 1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧙 Developed by: falker47

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💫 SPECIAL THANKS:

• hlsaves.exe
  by Katt (MIT License)
  Save compression/decompression tool

• HLSGE (Save Editor HTML)
  by ekaomk
  Web-based save editor

• CustomTkinter
  Modern UI framework

• pywebview
  Integrated browser window

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
