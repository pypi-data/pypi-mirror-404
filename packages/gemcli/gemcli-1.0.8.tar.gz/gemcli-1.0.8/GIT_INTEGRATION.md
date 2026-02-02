# Git Integration Guide

## Overview
The Gemini CLI now includes full Git integration with AI-powered commit message generation.

## Features

### 1. Git Commands
Available in Ask and System Agent modes:

- **`/status`** - Show current branch and changes
- **`/commit`** - AI-generated commit message with confirmation
- **`/push`** - Push commits to remote repository

### 2. Auto-Commit Workflow
After modifying files in System Agent mode:
1. Files are written to disk
2. CLI detects you're in a git repository
3. Prompts: "Would you like to commit these changes?"
4. If yes, AI generates a smart commit message based on the diff
5. You review and confirm the commit message
6. Changes are committed

### 3. AI Commit Messages
The AI analyzes:
- Git diff of all changes
- File paths modified
- Context from the conversation

It generates:
- Conventional commit format (feat:, fix:, refactor:, etc.)
- Clear, concise descriptions
- Multi-file summaries when needed

## Usage Examples

### Check Status
```
You: /status
```
Output:
```
◆ Git Status
Branch: main

 M gemini_cli.py
 M README.md
```

### Commit Changes
```
You: /commit
```
Output:
```
◆ Generating commit message...

◆ Suggested commit message:
feat: add git integration with AI-powered commit messages

Commit with this message?
◆ Yes, commit
◆ No, cancel
```

### Push to Remote
```
You: /push
```
Output:
```
◆ Pushing to remote...
✓ Pushed successfully
```

### Auto-Commit After File Modifications
In System Agent mode, after files are modified:
```
✓ Modified: gemini_cli.py
✓ Created: GIT_INTEGRATION.md

◆ Would you like to commit these changes?

◆ Yes, generate commit message
◆ No, skip
```

## Technical Details

### Functions Added
- `get_git_status()` - Checks repository status, branch, and changes
- `generate_commit_message(chat, modified_files)` - AI-generated commit messages
- `git_commit(message, files)` - Commits changes with message
- `git_push()` - Pushes to remote repository

### Integration Points
- Commands added to chat loop after `/clear` handler
- Auto-commit prompt added after file write operations
- Uses existing chat session for commit message generation
- Subprocess with CREATE_NO_WINDOW flag for silent execution on Windows

## Benefits
1. **Smart Commit Messages** - AI understands context and generates meaningful messages
2. **Seamless Workflow** - No need to switch to terminal
3. **Review & Confirm** - Always see commit message before committing
4. **Conventional Commits** - Follows standard commit message conventions
5. **File Tracking** - Automatically stages modified files

## Requirements
- Git installed and accessible from command line
- Repository must be initialized (`git init`)
- Remote configured for push operations
