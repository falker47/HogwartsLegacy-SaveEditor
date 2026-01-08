# Project: Hogwarts Legacy Save Manager (GUI Wrapper)

## Role
Act as a Senior Python Developer and UI/UX Designer.

## Goal
Create a modern, user-friendly GUI application to manage, backup, and edit *Hogwarts Legacy* save files. This tool acts as a wrapper around an existing CLI tool (`hlsaves.exe`) and a web-based editor (`HLSGE.html`).

## Context & Constraints
1.  **Portability:** The application runs from a portable folder. It expects `hlsaves.exe`, `oo2core_9_win64.dll`, and `HLSGE.html` to be in the same directory (or a `/bin` subdirectory) as the Python script.
2.  **Safety:** Before any modification, the tool MUST create a backup of the save file.
3.  **Environment:** Windows 10/11.
4.  **Tech Stack:** Python 3.x, `customtkinter` (for a modern UI), `shutil`, `subprocess`.

## Functional Requirements

### 1. Automatic Path Detection
- Automatically detect the Hogwarts Legacy save directory: `%LOCALAPPDATA%\Hogwarts Legacy\Saved\SaveGames\`.
- Identify the user ID folder (the numeric folder inside `SaveGames`). If multiple exist, pick the most recently modified or ask the user.
- Allow the user to manually select the path if auto-detection fails.

### 2. Save File Listing
- Display a list of `.sav` files found in the save directory.
- **Sort:** Descending by modification date (newest on top).
- **Display info:** Filename (e.g., `HL-00-00.sav`) and formatted timestamp.

### 3. Workflow - Step A: Extract & Edit
- **User Action:** Selects a save file from the list and clicks "Edit / Decrypt".
- **System Action:**
    1.  Create a timestamped backup in a local `./Backups/` folder.
    2.  Copy the target `.sav` to a temporary workspace.
    3.  Run the decompression command: `hlsaves.exe -d [input.sav] [output.decomp]`.
    4.  Check for errors (ensure output file exists).
    5.  Open `HLSGE.html` in the default web browser using the `webbrowser` module.
    6.  **UI Feedback:** Show a status message: "File decrypted. Drag the .decomp file into the browser editor." & "Waiting for edited file..."

### 4. Workflow - Step B: Inject & Restore
- **User Action:** Once the user has downloaded the edited file (usually named with `.edited` extension or similar) from the web editor.
- **UI Feature:** A "Select Edited File" button (or Drag & Drop zone if possible, otherwise a simple file dialog).
- **System Action:**
    1.  Take the user-selected edited database file.
    2.  Run the compression command: `hlsaves.exe -c [input.edited] [original_name.sav]`.
    3.  Overwrite the file in the actual Game Save Directory.
    4.  **UI Feedback:** Show a success message "Save file successfully updated!"

### 5. Credits & About Section
- Add a "Credits" button or a dedicated tab.
- **Content to Display:**
    - **App Wrapper:** Created by [Your Name/User].
    - **Save Tool Logic (hlsaves.exe):** Created by **Katt** (MIT License).
    - **Save Game Editor (HLSGE.html):** Created by **ekaomk** (Community Project).
    - **License Button:** If a `LICENSE` file exists in the folder, add a button to open/read it.

## UI Design (CustomTkinter)
- **Theme:** Dark Blue / System default.
- **Layout:**
    - **Left Panel:** Listbox of Save Files.
    - **Right Panel:**
        - Status/Log area (Text box).
        - Button: "Extract & Open Editor" (Primary Color).
        - Separator.
        - Button: "Inject Edited File" (Secondary Color).
        - Bottom Area: Button "Open Backup Folder" and small "Credits" button.

## Code Structure
- **File:** `main.py`
- Use a Class-based structure (`class App(ctk.CTk)`).
- Implement robust error handling (try/except blocks for file operations and subprocess calls).
- Add comments explaining the logic.

## Deliverables
1.  Complete `main.py` code.
2.  A `requirements.txt` file.
3.  Instructions on how to structure the folder (where to place the `.exe` and `.dll`).