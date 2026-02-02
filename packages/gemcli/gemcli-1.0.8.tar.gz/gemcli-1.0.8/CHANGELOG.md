# Changelog

All notable changes to GemCLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-01-22

### Documentation
- Improved installation instructions with clearer option ordering
- Added pipx installation method with automatic PATH setup
- Enhanced troubleshooting section with multiple fix options for 'gem' command not found
- Clarified quick-start guidance prioritizing pip (universal) over pipx (better but requires setup)

## [1.0.1] - 2026-01-22

### Documentation
- Removed emojis from all documentation for professional presentation
- Made README more detailed and enterprise-ready
- Removed repository links from package metadata
- Updated description to emphasize code completions, automation, and image generation

## [1.0.0] - 2026-01-22

### Added
- **Four Operating Modes**: Chat, System Agent, Agent, and Image Generation
- **File Operations**: Read, edit, search, and create files in System Agent and Agent modes
- **System Command Execution**: Control system operations (open apps, adjust brightness/volume, etc.)
- **Git Integration**: Auto-commit, push, and AI-generated commit messages
- **Diff Viewer**: Preview changes before applying with VS Code or terminal
- **Theme Support**: 6 color schemes (Cyan, Pink, Gold, Green, Purple, White)
- **File Path Autocomplete**: Claude-style file path completion in System Agent and Agent modes
- **Workspace Search**: Autonomous file discovery in Agent mode
- **Image Generation**: Create AI-generated images with customizable save locations
- **Browser Cookie Auth**: Automatic session extraction from Chrome, Edge, Firefox
- **Safety Features**: Built-in protections against destructive system commands and file operations

### Commands
- `/help` - Display comprehensive help with mode capabilities
- `/exit` or `/quit` - Exit current mode
- `/clear` - Clear terminal screen
- `/mode` - Switch between operating modes
- `/status` - Show git repository status
- `/commit` - Commit changes with AI-generated message
- `/push` - Push commits to remote repository

### Security
- Client-side only - no server component
- Session tokens never leave local machine
- No file deletion commands allowed
- Safe system command execution only

### Documentation
- Comprehensive README with installation guides
- QUICKSTART.md for rapid onboarding
- SYSTEM_COMMANDS.md for system control features
- GIT_INTEGRATION.md for version control workflows
- PUBLISH.md for package distribution

---

## [1.0.1] - 2026-01-22

### Changed
- Updated package description for clarity and professionalism
- Removed emojis from documentation for enterprise readiness
- Enhanced README with detailed getting started instructions
- Improved first-time setup documentation
- Made all documentation more formal and professional
- Removed repository links from package metadata

### Improved
- More comprehensive installation instructions
- Clearer mode descriptions
- Better workflow examples with detailed explanations

---

## [Unreleased]

### Planned
- Multi-language support
- Custom system command templates
- Plugin system for extensibility
- Cloud sync for settings
- Team collaboration features
