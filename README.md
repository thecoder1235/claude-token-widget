# Claude Token Widget

A lightweight Windows desktop widget that shows your remaining Claude context window tokens in real time — no API calls, no internet connection required.

> 🇹🇷 Türkçe kurulum için → [README.tr.md](README.tr.md)

![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## How It Works

```
Claude Code finishes a response
        │
        ▼
  token_hook.py runs automatically
  (triggered by Claude Code's Stop hook)
        │  writes to JSON
        ▼
  ~/.claude/token_stats.json
        │  read every 2.5 seconds
        ▼
  claude_token_widget.py
  (always-on-bottom desktop widget)
```

The two scripts never talk to each other directly — they share a JSON file. No API calls, no tokens spent.

---

## Features

- **Always on desktop layer** — stays behind all windows, above the wallpaper
- **Auto-fades** when a window covers it, reappears when uncovered
- **Circular arc gauge** showing usage percentage
- **Rounded corners** (Windows 11 native DWM / Windows 10 region fallback)
- **Draggable** — position is saved between sessions
- **Starts with Windows** — registers itself to startup registry on first run
- **No taskbar entry**, doesn't steal focus

---

## Requirements

- Windows 10 or 11
- Python 3.8+
- [Claude Code](https://claude.ai/code) CLI installed and configured

No third-party Python packages required — only standard library.

---

## Installation

### 1. Clone or download

```bash
git clone https://github.com/YOUR_USERNAME/claude-token-widget.git
```

Or download the ZIP and extract it anywhere.

### 2. Set up the Claude Code hook

Open (or create) `~/.claude/settings.json` and add the following — replace the path with wherever you extracted the files:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/path/to/token_hook.py\""
          }
        ]
      }
    ]
  }
}
```

If you already have other hooks, just add the `Stop` block alongside them.

### 3. Restart Claude Code

Close and reopen Claude Code so the hook takes effect.

### 4. Run the widget

```bash
pythonw "C:/path/to/claude_token_widget.py"
```

Use `pythonw` (not `python`) to run without a console window.

For testing or troubleshooting:

```bash
python "C:/path/to/claude_token_widget.py"
```

The widget will register itself to Windows startup automatically on first run.

---

## Files

| File | Purpose |
|------|---------|
| `claude_token_widget.py` | The desktop widget — run this manually once |
| `token_hook.py` | Claude Code hook — runs automatically, don't touch |

---

## Uninstall

1. Close the widget (click ✕)
2. Remove the hook entry from `~/.claude/settings.json`
3. Remove the startup entry: open **Registry Editor** → `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run` → delete `ClaudeTokenWidget`
4. Delete the project folder

---

## License

MIT — see [LICENSE](LICENSE)
