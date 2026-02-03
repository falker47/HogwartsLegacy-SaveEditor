"""
Configuration constants for Hogwarts Legacy Save Editor.
"""

# Application metadata
APP_NAME = "Hogwarts Legacy Save Editor & Manager"
VERSION = "1.0"

# UI Configuration
APPEARANCE_MODE = "dark"
COLOR_THEME = "dark-blue"
BACKGROUND_COLOR = "#2b2b2b"
INFO_PANEL_COLOR = "#1a1a2e"
SELECTED_COLOR = "#2a4a6a"
SELECTED_BORDER_COLOR = "#4a8aca"

# Button colors
BUTTON_FG_COLOR = "gray25"
BUTTON_HOVER_COLOR = "gray35"
MAIN_BUTTON_FG_COLOR = "#1f6aa5"
MAIN_BUTTON_HOVER_COLOR = "#144870"

# Window configuration
MIN_WIDTH = 600
MIN_HEIGHT = 500
TASKBAR_HEIGHT = 80
MANAGER_WIDTH_RATIO = 0.45

# Expected SHA256 hash of the trusted oo2core_9_win64.dll
EXPECTED_DLL_HASH = "6f5d41a7892ea6b2db420f2458dad2f84a63901c9a93ce9497337b16c195f457"

# DLL download URL
DLL_DOWNLOAD_URL = "https://github.com/new-world-tools/go-oodle/releases/download/v0.2.3-files/oo2core_9_win64.dll"
DLL_NAME = "oo2core_9_win64.dll"

# Required files
HLSAVES_EXE = "hlsaves.exe"
HLSGE_HTML = "HLSGE.html"

# Save file patterns
SAVE_FILE_PATTERN = r"HL-(\d+)-(\d+)\.sav"
