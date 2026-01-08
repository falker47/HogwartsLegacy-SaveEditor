# 🧙 Hogwarts Legacy Save Editor & Manager

A modern, user-friendly GUI application for editing and managing Hogwarts Legacy save files.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

## ✨ Features

- 📁 **Auto-detect** save files location
- 🔓 **One-click** save extraction and editing
- 🌐 **Integrated editor** - opens directly in the app
- 💾 **Auto-save** - changes applied automatically when you click Download
- 📦 **Automatic backups** - never lose your progress
- 🎮 **Side-by-side windows** - manager on left, editor on right

## 📋 Requirements

### Required Files (place in same folder as app)

| File | Description | Source |
|------|-------------|--------|
| `hlsaves.exe` | Save compression tool | [Nexus Mods #1983](https://www.nexusmods.com/hogwartslegacy/mods/1983) (included) |
| `HLSGE.html` | Save editor | [Nexus Mods #77](https://www.nexusmods.com/hogwartslegacy/mods/77) (included) |
| `oo2core_9_win64.dll` | Oodle decompression | Copy from your game folder* |

### 🔍 How to find `oo2core_9_win64.dll` 

This file is required for decompression but **cannot be distributed** with the app. You must copy it from your game installation folder.

**Common locations:**
- **Steam:** `C:\Program Files (x86)\Steam\steamapps\common\Hogwarts Legacy\Engine\Binaries\ThirdParty\Oodle\Win64\`
- **Epic Games:** `C:\Program Files\Epic Games\Hogwarts Legacy\Engine\Binaries\ThirdParty\Oodle\Win64\`

**Instructions:**
1. Navigate to the folder above
2. Copy `oo2core_9_win64.dll`
3. Paste it into the same folder as `HL_Save_Manager.exe`

### Python Dependencies (for running from source)

```
customtkinter>=5.0.0
tkinterdnd2>=0.3.0
pywebview>=4.0.0
```

## 🚀 Installation

### Option 1: Download Release (Recommended)
1. Download the latest release from [Releases](../../releases)
2. Extract to a folder
3. Add the required files listed above
4. Run `HogwartsLegacy-SaveEditor.exe`

### Option 2: Run from Source
```bash
# Clone the repository
git clone https://github.com/falker47/HogwartsLegacy-SaveEditor.git
cd HogwartsLegacy-SaveEditor

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

### Option 3: Build Executable
```bash
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build
build.bat
```

## 📖 Usage

1. **Launch** the application
2. **Select** a save file from the list
3. **Click** "Edit Save File"
4. **Edit** your save in the integrated editor
5. **Click** "Download" in the editor
6. ✅ **Done!** Your save is updated automatically

## 📁 File Structure

```
HogwartsLegacy-SaveEditor/
├── HogwartsLegacy-SaveEditor.exe  # Main application
├── hlsaves.exe                    # Compression tool (required)
├── HLSGE.html                     # Save editor (required)
├── oo2core_9_win64.dll            # From game (required)
└── Backups/                       # Created automatically
```

## 🎮 Where Are My Saves?

Hogwarts Legacy saves are located at:
```
%LOCALAPPDATA%\Hogwarts Legacy\Saved\SaveGames\[USER_ID]\
```

Backups are saved in:
```
[Save Location]\Backups\
```

## 🙏 Credits

### Developer
- **falker47** - Application development

### Special Thanks
- **Katt** - [hlsaves.exe](https://www.nexusmods.com/hogwartslegacy/mods/99) (MIT License)
- **ekaomk** - [HLSGE Save Editor](https://www.nexusmods.com/hogwartslegacy/mods/77)
- **CustomTkinter** - Modern Python UI framework
- **pywebview** - Integrated browser window

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is provided as-is. Always backup your saves before editing. The developer is not responsible for any lost or corrupted save data.

---

Made with ❤️ for the Hogwarts Legacy community
