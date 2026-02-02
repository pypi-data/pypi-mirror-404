# GEM CLI 💎

Beautiful terminal interface for Gemini AI with intelligent Git integration and AI-powered coding assistance.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

## ✨ Features

- **🤖 Multiple Modes**
  - **Ask Mode**: Chat with Gemini AI
  - **System Agent Mode**: AI coding assistant that can read, modify, and create files
  - **Image Generation**: Create stunning images from text prompts

- **🔧 Git Integration**
  - AI-generated commit messages
  - Smart branch management
  - Automated commit & push workflows
  - `/status`, `/commit`, `/push` commands

- **📁 File Management**
  - Read files with `/path/to/file.py` syntax
  - VS Code diff preview for changes
  - Accept/reject modifications
  - Multi-file operations

- **🎨 Beautiful UI**
  - Gradient ASCII art banner
  - Customizable color themes
  - Rich markdown rendering
  - Diamond (◆) indicators

- **🔒 100% Private**
  - Client-side only (no server)
  - Your data stays on your machine
  - Secure cookie authentication

## 📦 Installation

### Option 1: Install from Source (Recommended)

```bash
# Clone the repository
git clone https://github.com/Aniketh78/Gemini-Terminal-Tool-GEM-CLI.git
cd gem-cli

# Install globally
pip install .
```

### Option 2: Install in Development Mode

```bash
# Clone the repository
git clone https://github.com/Aniketh78/Gemini-Terminal-Tool-GEM-CLI.git
cd gem-cli

# Install in editable mode
pip install -e .
```

### Option 3: Install from PyPI (when published)

```bash
pip install gem-cli
```

### Option 4: Direct from GitHub

```bash
pip install git+https://github.com/Aniketh78/Gemini-Terminal-Tool-GEM-CLI.git
```

## 🚀 Quick Start

After installation, simply run:

```bash
gem
```

Or use the alternative command:

```bash
gemcli
```

### First-Time Setup

1. Run `gem` to start the CLI
2. Enter your Gemini cookies:
   - `__Secure-1PSID`
   - `__Secure-1PSIDTS`
3. Choose your mode (Ask / System Agent / Image Generation)
4. Start chatting!

## 📖 Usage

### Basic Commands

All modes support:
- `/exit` - Exit the application
- `/clear` - Clear the screen
- `/mode` - Switch between modes

### System Agent Mode Commands

Git integration:
- `/status` - Show git status and current branch
- `/commit` - AI-generated commit with confirmation
- `/push` - Push commits to remote

File operations:
- `/path/to/file.py` - Read and include file in context
- AI can suggest modifications in JSON format
- Accept/reject changes with VS Code diff preview

### Git Workflow

Configure your preferences from the main menu:
- **Commit Mode**: "Ask on exit" or "After every change"
- **Auto Push**: Automatically push after commits
- **Branch Selection**: Choose/create branches in System Agent mode

### Example Workflows

**Coding Assistant:**
```
You: /gemini_cli.py add a new feature to handle user authentication
```
*AI reads the file, suggests changes, opens VS Code diff, you accept*

**Git Integration:**
```
You: /commit
```
*AI analyzes changes, generates smart commit message, you confirm*

**Image Generation:**
```
You: Create a beautiful sunset over mountains with vibrant colors
```
*AI generates image, saves to configured directory*

## ⚙️ Configuration

### Git Settings
Access from main menu → **Git Settings**:
- Commit timing (immediate or on exit)
- Auto-push after commit
- Branch selection prompts

### Theme Customization
Access from main menu → **Customize Theme**:
- White, Cyan, Pink, Gold, Green, Purple, Hot Pink

### Image Settings
In Image Mode → **Save Settings**:
- Configure save directory
- Auto-complete for directory paths

## 🔑 Getting Gemini Cookies

1. Open [Google Gemini](https://gemini.google.com) in your browser
2. Log in to your account
3. Open Developer Tools (F12)
4. Go to Application/Storage → Cookies
5. Find and copy:
   - `__Secure-1PSID`
   - `__Secure-1PSIDTS`

Cookies are saved locally in `.gemini_cookies.json`

## 🛠️ Development

### Requirements

- Python 3.8+
- Git (for git integration features)
- VS Code (recommended for diff previews)

### Install for Development

```bash
git clone https://github.com/Aniketh78/Gemini-Terminal-Tool-GEM-CLI.git
cd gem-cli
pip install -e ".[dev]"
```

### Project Structure

```
gem-cli/
├── gemini_cli.py          # Main application
├── pyproject.toml         # Package configuration
├── requirements.txt       # Dependencies
├── README.md             # This file
├── LICENSE               # MIT License
├── GIT_INTEGRATION.md    # Git features documentation
└── .gitignore           # Git ignore rules
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [gemini-webapi](https://github.com/HanaokaYuzu/Gemini-API) by HanaokaYuzu
- UI powered by [Rich](https://github.com/Textualize/rich)
- Interactive prompts by [Questionary](https://github.com/tmbo/questionary)

## 📞 Support

- 🐛 Report bugs: [GitHub Issues](https://github.com/Aniketh78/Gemini-Terminal-Tool-GEM-CLI/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/Aniketh78/Gemini-Terminal-Tool-GEM-CLI/discussions)

## 🗺️ Roadmap

- [ ] PyPI package publication
- [ ] More Git operations (stash, rebase, etc.)
- [ ] Plugin system for extensions
- [ ] Multi-language support
- [ ] Docker containerization

---

Made with ❤️ by 89P13
