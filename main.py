"""
Hogwarts Legacy Save Manager
A modern GUI application to manage, backup, and edit Hogwarts Legacy save files.
"""

import os
import sys
import re
import base64
import shutil
import subprocess
import multiprocessing
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

import customtkinter as ctk
from tkinter import filedialog, messagebox

# Try drag-drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    TKDND_AVAILABLE = True
except ImportError:
    TKDND_AVAILABLE = False


def format_file_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def parse_save_filename(filename: str) -> dict:
    info = {"slot": "Unknown", "type": "Save", "display": filename}
    match = re.match(r"HL-(\d+)-(\d+)\.sav", filename)
    if match:
        slot_num = int(match.group(1))
        save_type = int(match.group(2))
        info["type"] = "Manual Save" if save_type == 0 else f"Auto #{save_type}"
        info["slot"] = f"Slot {slot_num}"
        info["display"] = f"{info['slot']} - {info['type']}"
    return info


def launch_editor_process(html_path: str, file_path: str, file_name: str, 
                          original_save: str, hlsaves_path: str, app_dir: str,
                          status_file: str, screen_width: int, screen_height: int):
    """Function to run in separate process - launches WebView editor with auto-save."""
    
    def write_status(status: str, message: str = ""):
        """Write status to file for main process to read."""
        with open(status_file, 'w') as f:
            f.write(f"{status}|{message}")
    
    try:
        import webview
        
        window_ref = [None]
        
        class Api:
            def __init__(self, fp, fn, orig_save, hlsaves, appdir):
                self.file_path = fp
                self.file_name = fn
                self.original_save = orig_save
                self.hlsaves_path = hlsaves
                self.app_dir = appdir
            
            def get_file_data(self):
                try:
                    with open(self.file_path, 'rb') as f:
                        return base64.b64encode(f.read()).decode('utf-8')
                except:
                    return None
            
            def get_file_name(self):
                return self.file_name
            
            def save_edited_file(self, b64_data: str):
                """Called from JS when user clicks Download."""
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
                        write_status("error", result.stderr)
                        return {"success": False, "error": result.stderr}
                    
                    write_status("success", "Save updated successfully!")
                    return {"success": True}
                    
                except Exception as e:
                    write_status("error", str(e))
                    return {"success": False, "error": str(e)}
            
            def close_window(self):
                """Close the editor window."""
                if window_ref[0]:
                    window_ref[0].destroy()
        
        api = Api(file_path, file_name, original_save, hlsaves_path, app_dir)
        
        # Position on right half of screen
        editor_width = screen_width // 2
        editor_height = screen_height - 80  # Leave taskbar space
        editor_x = screen_width // 2
        editor_y = 0
        
        window_ref[0] = webview.create_window(
            'Hogwarts Legacy Save Editor',
            html_path,
            width=editor_width, height=editor_height,
            x=editor_x, y=editor_y,
            js_api=api
        )
        
        def on_loaded():
            js = """
            (function() {
                // Auto-load file
                async function tryLoad() {
                    if (typeof pywebview === 'undefined') {
                        setTimeout(tryLoad, 500);
                        return;
                    }
                    try {
                        const b64 = await pywebview.api.get_file_data();
                        const fileName = await pywebview.api.get_file_name();
                        if (!b64) return;
                        
                        const binary = atob(b64);
                        const bytes = new Uint8Array(binary.length);
                        for (let i = 0; i < binary.length; i++) {
                            bytes[i] = binary.charCodeAt(i);
                        }
                        
                        const file = new File([bytes], fileName, {type: 'application/octet-stream'});
                        const input = document.querySelector('input[type="file"]');
                        if (input) {
                            const dt = new DataTransfer();
                            dt.items.add(file);
                            input.files = dt.files;
                            input.dispatchEvent(new Event('change', {bubbles: true}));
                        }
                    } catch(e) {
                        console.error('Auto-load failed:', e);
                    }
                }
                setTimeout(tryLoad, 1000);
                
                // Intercept download clicks
                function interceptDownloads() {
                    document.addEventListener('click', async function(e) {
                        const target = e.target;
                        if (target.tagName === 'A' && target.hasAttribute('download')) {
                            e.preventDefault();
                            e.stopPropagation();
                            
                            // Show saving indicator
                            const overlay = document.createElement('div');
                            overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.9);display:flex;align-items:center;justify-content:center;z-index:99999;';
                            overlay.innerHTML = '<div style="text-align:center;color:white;font-size:28px;">💾 Saving...<br><small style="font-size:16px;">Please wait</small></div>';
                            document.body.appendChild(overlay);
                            
                            const href = target.href;
                            if (href && href.startsWith('blob:')) {
                                try {
                                    const response = await fetch(href);
                                    const blob = await response.blob();
                                    const reader = new FileReader();
                                    
                                    reader.onload = async function() {
                                        const b64 = reader.result.split(',')[1];
                                        const result = await pywebview.api.save_edited_file(b64);
                                        
                                        if (result.success) {
                                            overlay.innerHTML = '<div style="text-align:center;color:#4CAF50;font-size:28px;">✅ Save Updated!<br><small style="font-size:16px;">Closing...</small></div>';
                                            setTimeout(async () => {
                                                await pywebview.api.close_window();
                                            }, 1500);
                                        } else {
                                            overlay.innerHTML = '<div style="text-align:center;color:#f44336;font-size:28px;">❌ Error<br><small style="font-size:14px;">' + result.error + '</small></div>';
                                            setTimeout(() => overlay.remove(), 3000);
                                        }
                                    };
                                    reader.readAsDataURL(blob);
                                } catch(err) {
                                    overlay.innerHTML = '<div style="text-align:center;color:#f44336;font-size:28px;">❌ Error<br><small style="font-size:14px;">' + err.message + '</small></div>';
                                    setTimeout(() => overlay.remove(), 3000);
                                }
                            }
                            return false;
                        }
                    }, true);
                }
                setTimeout(interceptDownloads, 2000);
            })();
            """
            window_ref[0].evaluate_js(js)
        
        write_status("editing", "Editor opened")
        webview.start(on_loaded)
        
    except Exception as e:
        write_status("error", str(e))


# Choose base class
if TKDND_AVAILABLE:
    BaseWindow = TkinterDnD.Tk
else:
    BaseWindow = ctk.CTk


class App(BaseWindow):
    def __init__(self):
        super().__init__()
        
        self.title("Hogwarts Legacy Save Manager")
        
        # Position on left half of screen
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = screen_width // 2
        window_height = screen_height - 80  # Leave taskbar space
        self.geometry(f"{window_width}x{window_height}+0+0")
        self.minsize(600, 500)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(bg="#2b2b2b")
        
        # Paths
        if getattr(sys, 'frozen', False):
            self.app_dir = Path(sys.executable).parent
        else:
            self.app_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        
        self.hlsaves_exe = self.app_dir / "hlsaves.exe"
        self.hlsge_html = self.app_dir / "HLSGE.html"
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
        
        # Verify files
        if not self._verify_required_files():
            return
        
        # Build UI
        self._create_ui()
        self._detect_save_directory()
    
    def _verify_required_files(self) -> bool:
        missing = []
        if not self.hlsaves_exe.exists():
            missing.append(("hlsaves.exe", "Save tool by Katt"))
        if not self.hlsge_html.exists():
            missing.append(("HLSGE.html", "Editor by ekaomk"))
        
        dll = self.app_dir / "oo2core_9_win64.dll"
        if not dll.exists():
            missing.append(("oo2core_9_win64.dll", "From game files"))
        
        if missing:
            msg = "Missing files:\n\n"
            for f, d in missing:
                msg += f"❌ {f} - {d}\n"
            msg += f"\nPlace in: {self.app_dir}"
            messagebox.showerror("Missing Files", msg)
            return False
        return True
    
    def _create_ui(self) -> None:
        main_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # LEFT PANEL
        left = ctk.CTkFrame(main_frame)
        left.grid(row=0, column=0, padx=(10,5), pady=10, sticky="nsew")
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(left, fg_color="transparent")
        header.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header, text="📁 Save Files", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w")
        self.path_label = ctk.CTkLabel(header, text="Detecting...", font=ctk.CTkFont(size=11), text_color="gray")
        self.path_label.grid(row=1, column=0, sticky="w")
        
        self.save_list_frame = ctk.CTkScrollableFrame(left)
        self.save_list_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.save_list_frame.grid_columnconfigure(0, weight=1)
        
        # Info panel
        self.info_frame = ctk.CTkFrame(left, fg_color="#1a1a2e", corner_radius=8)
        self.info_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.info_label = ctk.CTkLabel(self.info_frame, text="Select a save file", font=ctk.CTkFont(size=11), text_color="gray", justify="left")
        self.info_label.pack(padx=10, pady=8, anchor="w")
        
        # Buttons
        btns = ctk.CTkFrame(left, fg_color="transparent")
        btns.grid(row=3, column=0, padx=10, pady=(5,10), sticky="ew")
        btns.grid_columnconfigure(0, weight=1)
        btns.grid_columnconfigure(1, weight=1)
        
        ctk.CTkButton(btns, text="🔄 Refresh", command=self._refresh_save_list, height=28).grid(row=0, column=0, padx=(0,5), sticky="ew")
        ctk.CTkButton(btns, text="📁 Browse", command=self._browse_save_directory, height=28).grid(row=0, column=1, padx=(5,0), sticky="ew")
        
        # RIGHT PANEL
        right = ctk.CTkFrame(main_frame)
        right.grid(row=0, column=1, padx=(5,10), pady=10, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(right, text="📋 Status Log", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=15, pady=(15,5), sticky="w")
        
        self.log_textbox = ctk.CTkTextbox(right, font=ctk.CTkFont(family="Consolas", size=12), state="disabled")
        self.log_textbox.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")
        
        # Actions frame
        actions = ctk.CTkFrame(right, fg_color="transparent")
        actions.grid(row=2, column=0, padx=15, pady=10, sticky="ew")
        actions.grid_columnconfigure(0, weight=1)
        
        # Main action button
        self.extract_button = ctk.CTkButton(
            actions, text="🔓 Edit Save File", command=self._extract_and_edit,
            height=50, font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#1f6aa5", hover_color="#144870"
        )
        self.extract_button.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        
        # Progress indicator (hidden by default)
        self.progress_frame = ctk.CTkFrame(actions, fg_color="#1a1a2e", corner_radius=8)
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, mode="indeterminate", height=8)
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Working...", font=ctk.CTkFont(size=12), text_color="#a0a0a0")
        
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
        bottom.grid(row=3, column=0, padx=15, pady=(10,15), sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)
        
        ctk.CTkButton(bottom, text="📂 Backups", command=self._open_backup_folder, height=32).grid(row=0, column=0, padx=(0,10), sticky="ew")
        ctk.CTkButton(bottom, text="❓ Help", command=self._show_help, height=32, width=70, fg_color="gray30", hover_color="gray40").grid(row=0, column=1, padx=(0,5))
        ctk.CTkButton(bottom, text="Credits", command=self._show_credits, height=32, width=70, fg_color="gray30", hover_color="gray40").grid(row=0, column=2)
        
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
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"[{ts}] {msg}\n" if msg else "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        self.update()
    
    def _detect_save_directory(self) -> None:
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
        for w in self.save_list_frame.winfo_children():
            w.destroy()
        
        self.save_files = []
        self.current_save_file = None
        self.selected_button = None
        self._update_file_info(None)
        
        if not self.save_directory or not self.save_directory.exists():
            ctk.CTkLabel(self.save_list_frame, text="No directory", text_color="gray").pack(pady=20)
            return
        
        saves = [f for f in self.save_directory.glob("*.sav") if f.is_file()]
        if not saves:
            ctk.CTkLabel(self.save_list_frame, text="No saves found", text_color="gray").pack(pady=20)
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
    
    def _select_save_file(self, save_file: Path, button: ctk.CTkButton = None) -> None:
        if self.selected_button:
            self.selected_button.configure(fg_color="gray25", border_width=0)
        
        self.current_save_file = save_file
        self.selected_button = button
        
        if button:
            button.configure(fg_color="#2a4a6a", border_width=2, border_color="#4a8aca")
        
        self._update_file_info(save_file)
        self._log(f"📌 Selected: {save_file.name}")
    
    def _update_file_info(self, save_file: Optional[Path]) -> None:
        if not save_file:
            self.info_label.configure(text="Select a save file", text_color="gray")
            return
        
        stat = save_file.stat()
        info = parse_save_filename(save_file.name)
        mod = datetime.fromtimestamp(stat.st_mtime)
        
        text = f"📄 {save_file.name}\n🎮 {info['display']}\n📅 {mod.strftime('%Y-%m-%d %H:%M')}\n💾 {format_file_size(stat.st_size)}"
        self.info_label.configure(text=text, text_color="#a0a0a0")
    
    def _extract_and_edit(self) -> None:
        if self.is_working:
            return
        
        if not self.current_save_file:
            messagebox.showwarning("No File", "Please select a save file first!")
            return
        
        if not self.hlsaves_exe.exists():
            messagebox.showerror("Error", "hlsaves.exe not found!")
            return
        
        # Run in thread to keep UI responsive
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
                    import webview
                    
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
                        args=(str(self.hlsge_html), str(decomp), decomp.name,
                              str(self.current_save_file), str(self.hlsaves_exe), 
                              str(self.app_dir), str(status_file),
                              screen_width, screen_height)
                    )
                    self.editor_process.start()
                    
                    self._log("✅ Editor opened!")
                    self._log("")
                    self._log("📝 Edit your save and click 'Download'.")
                    
                    # Monitor status file in background
                    def monitor_status():
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
                            except:
                                pass
                            
                            import time
                            time.sleep(0.5)
                        
                        # Clean up
                        if status_file.exists():
                            try:
                                status_file.unlink()
                            except:
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
        if self.backup_dir and self.backup_dir.exists():
            os.startfile(self.backup_dir)
            self._log("📂 Opened backups")
        else:
            messagebox.showinfo("No Backups", "No backup folder found yet.\nSelect a save directory first.")
    
    def _show_help(self) -> None:
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
        messagebox.showinfo("Credits", """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   HOGWARTS LEGACY SAVE MANAGER
            Version 1.5
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


def main():
    multiprocessing.freeze_support()
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    main()
