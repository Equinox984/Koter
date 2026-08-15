# Koter 📝
> Offline Markdown note-taking CLI for developers.

This Python program helps developers organize their thoughts and notes through a minimalistic terminal interface. Create, edit, search, and manage your Markdown notes with vim-style keybindings and zero dependencies.

## 🛠️ Technologies
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

## 🧠 How does it work?

The program offers two main interfaces accessible through the CLI:

### 📋 Command Line Interface
- **Create Notes:** `koter new "Title"` opens your editor
- **List Notes:** `koter list` shows all notes sorted by date
- **Search:** `koter search "query"` finds text across all notes
- **Tags & Pin:** Organize notes with tags and pinned items
- **Trash System:** Move notes to trash and restore them
- **Version History:** Track changes with automatic snapshots

### ⌨️ Interactive TUI Mode
Run `koter` without arguments to enter the interactive mode:
- **j/k:** Navigate up/down
- **gg/G:** Jump to start/end
- **Enter:** Edit selected note in $EDITOR
- **p:** Pin/unpin note
- **d:** Move to trash
- **/:** Search
- **:**: Command line (vim-style)
- **q:** Quit

## 🚀 Installation and Use

**Requirement:** Have **Python 3.11+** installed on your system.

Clone the repository and install:

1. **Clone the repository:**
```bash
   git clone https://github.com/yourusername/koter
   cd koter/
```

2. **Install the package:**
```bash
   pip install -e .
```

3. **Use the CLI:**
```bash
   koter                    # Enter interactive mode
   koter new "My Note"      # Create a new note
   koter list               # List all notes
   koter search "keyword"   # Search notes
   koter --help             # Show all commands
```

## ✨ Features

- ✅ Zero external dependencies (stdlib only)
- ✅ Obsidian-compatible YAML frontmatter
- ✅ Vim-style interactive TUI mode
- ✅ Automatic version snapshots
- ✅ Tag-based organization
- ✅ Pin important notes
- ✅ Trash system with restore
- ✅ Case-insensitive search
- ✅ Configurable via TOML config file
- ✅ Theme support (mono default)

## 📁 File Structure

Notes are stored in `~/Koter/` by default (configurable):
- Each note is a `.md` file with YAML frontmatter
- `.trash/` directory holds deleted notes
- `.koter/history/` stores version snapshots

## 📝 Project Status

**Completed:**
- ✅ Core CLI with argparse
- ✅ Note creation and editing
- ✅ List and search functionality
- ✅ Tag management
- ✅ Pin/unpin system
- ✅ Trash and restore
- ✅ Version history with snapshots
- ✅ Interactive TUI mode
- ✅ Configuration via TOML
- ✅ Theme system

**Upcoming:**
- 🔄 Custom themes via TOML files
- 🔄 Enhanced search with context
- 🔄 Export/import functionality

---

**Developed with ❤️**
