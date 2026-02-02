#!/usr/bin/env python3
"""
GemCLI - Beautiful terminal interface for Gemini AI
Made by 89P13
"""

import asyncio
import sys
import os
import json
import glob
import re
import difflib
import subprocess
import tempfile
from typing import Optional, Tuple, List
from pathlib import Path

# Suppress ALL logging before importing anything
import logging
import warnings
warnings.filterwarnings('ignore')

# Disable all logging including loguru
logging.disable(logging.CRITICAL)
os.environ['LOGURU_LEVEL'] = 'CRITICAL'
os.environ['LOGURU_DIAGNOSE'] = 'False'

# Redirect stderr to suppress loguru output
import io
sys.stderr = io.StringIO()

# Third-party imports
try:
    from gemini_webapi import GeminiClient
    from rich.console import Console
    from rich.markdown import Markdown
    from rich import box
    from rich.theme import Theme
    import questionary
    from questionary import Style
    import base64
    import webbrowser
except ImportError as e:
    print(f"Missing required library: {e}")
    print("\nPlease install: pip install gemini-webapi rich questionary")
    sys.exit(1)

# Theme configuration
theme_config = {
    'primary_color': '#FFFFFF',  # White (default)
    'secondary_color': '#FF6B9D',  # Vibrant pink
    'accent_color': '#FFFFFF',  # White (default)
    'text_color': 'white',
    'border_color': '#3a3a3a',
    'success_color': '#00FF88',
    'warning_color': '#FFB700'
}

# Initialize Rich console with custom theme for markdown
rich_theme = Theme({
    "markdown.link": theme_config['accent_color'],
    "markdown.link_url": theme_config['accent_color'],
    "markdown.code": theme_config['accent_color'],
    "markdown.code_block": theme_config['text_color'],
})
console = Console(theme=rich_theme)

# =============================================================================
# UI Components
# =============================================================================

# Store last code blocks for copy functionality
last_code_blocks = []

# Git workflow preferences
git_preferences = {
    'enabled': True,  # Enable git integration
    'commit_mode': 'on_exit',  # 'immediate' or 'on_exit'
    'auto_push': True,
    'ask_branch': True  # Ask to create/select branch when entering semi-agent mode
}

# Diff viewer preferences
diff_preferences = {
    'enabled': True,  # Enable diff viewing
    'editor': 'vscode'  # 'vscode', 'default', or 'none'
}


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """Display beautiful banner."""
    clear_screen()
    
    # Banner with gradient effect from white to black (top to bottom)
    banner_lines = [
        "   ██████╗ ███████╗███╗   ███╗  ██████╗██╗     ██╗",
        "  ██╔════╝ ██╔════╝████╗ ████║ ██╔════╝██║     ██║",
        "  ██║  ███╗█████╗  ██╔████╔██║ ██║     ██║     ██║",
        "  ██║   ██║██╔══╝  ██║╚██╔╝██║ ██║     ██║     ██║",
        "  ╚██████╔╝███████╗██║ ╚═╝ ██║ ╚██████╗███████╗██║",
        "   ╚═════╝ ╚══════╝╚═╝     ╚═╝  ╚═════╝╚══════╝╚═╝"
    ]
    
    # Gradient colors - vibrant golden to orange/pink (top to bottom)
    gradient_colors = ['#FFD700', '#FFC700', '#FFB700', '#FF8C00', '#FF6B35', '#FF6B9D']
    
    console.print()
    for i, line in enumerate(banner_lines):
        console.print(line, style=f"bold {gradient_colors[i]}", justify="left")
    
    # Clickable GitHub credit
    console.print(f"\n[link=https://github.com/Aniketh78/Gemini-Terminal-Tool-GEM-CLI][bold {theme_config['accent_color']}]Made by 89P13[/][/link]\n", justify="center")


def get_file_completions(text: str, current_word: str) -> List[str]:
    """Get file path completions based on current input - restricted to workspace only."""
    try:
        # Get workspace root (current working directory)
        workspace_root = Path.cwd()
        
        # Remove the / prefix if present
        path_word = current_word.lstrip('/')
        
        # If word starts with / or contains path separators, try to complete
        if current_word.startswith('/') or '/' in current_word or '\\' in current_word:
            # Extract the directory and partial filename
            path_str = path_word.replace('\\', '/')
            
            # Convert relative path to absolute within workspace
            search_base = workspace_root
            if path_str.startswith('./'):
                path_str = path_str[2:]
            
            if not path_str or path_str.endswith('/'):
                # User typed / alone or a directory path ending with /, show contents
                search_dir = search_base / path_str.rstrip('/') if path_str else search_base
                pattern = '*'
            else:
                # Extract directory and filename pattern
                last_slash = path_str.rfind('/')
                if last_slash != -1:
                    dir_part = path_str[:last_slash]
                    file_part = path_str[last_slash + 1:]
                    search_dir = search_base / dir_part
                    pattern = file_part + '*' if file_part else '*'
                else:
                    search_dir = search_base
                    pattern = path_str + '*' if path_str else '*'
            
            # Get matches within workspace only
            matches = []
            try:
                if search_dir.exists() and search_dir.is_dir():
                    for item in search_dir.glob(pattern):
                        # Only include items within workspace
                        try:
                            relative = item.relative_to(workspace_root)
                            rel_str = str(relative).replace('\\', '/')
                            if item.is_dir():
                                matches.append('/' + rel_str + '/')
                            else:
                                matches.append('/' + rel_str)
                        except ValueError:
                            # Skip items outside workspace
                            continue
            except:
                pass
            
            # Filter out common ignore patterns
            matches = [m for m in matches if not any(
                ignore in m for ignore in ['__pycache__', '.git', 'venv', 'node_modules', '.pyc']
            )]
            
            return sorted(matches)[:20]  # Limit to 20 suggestions
        else:
            return []
    except:
        return []


def get_directory_completions(text: str, current_word: str) -> List[str]:
    """Get directory path completions (directories only) - restricted to workspace only."""
    try:
        # Get workspace root (current working directory)
        workspace_root = Path.cwd()
        
        # Handle both absolute and relative paths
        if current_word.startswith('/'):
            # Workspace-relative path
            path_word = current_word.lstrip('/')
            search_base = workspace_root
        else:
            # Could be absolute Windows path or relative
            if Path(current_word).is_absolute():
                # Absolute path
                search_base = Path(current_word).parent
                path_word = Path(current_word).name
            else:
                # Relative to workspace
                path_word = current_word
                search_base = workspace_root
        
        path_str = path_word.replace('\\', '/')
        
        if not path_str or path_str.endswith('/'):
            # Show directories in current level
            search_dir = search_base / path_str.rstrip('/') if path_str else search_base
            pattern = '*'
        else:
            # Extract directory and partial name
            last_slash = path_str.rfind('/')
            if last_slash != -1:
                dir_part = path_str[:last_slash]
                name_part = path_str[last_slash + 1:]
                search_dir = search_base / dir_part
                pattern = name_part + '*' if name_part else '*'
            else:
                search_dir = search_base
                pattern = path_str + '*' if path_str else '*'
        
        # Get directory matches only
        matches = []
        try:
            if search_dir.exists() and search_dir.is_dir():
                for item in search_dir.glob(pattern):
                    if item.is_dir():
                        # Use absolute paths for directory picker
                        matches.append(str(item) + os.sep)
        except:
            pass
        
        # Filter out common ignore patterns
        matches = [m for m in matches if not any(
            ignore in m for ignore in ['__pycache__', '.git', 'venv', 'node_modules']
        )]
        
        return sorted(matches)[:20]
    except:
        return []
    """Get file path completions based on current input - restricted to workspace only."""
    try:
        # Get workspace root (CliTool directory)
        workspace_root = Path(__file__).parent.absolute()
        
        # Remove the / prefix if present
        path_word = current_word.lstrip('/')
        
        # If word starts with / or contains path separators, try to complete
        if current_word.startswith('/') or '/' in current_word or '\\' in current_word:
            # Extract the directory and partial filename
            path_str = path_word.replace('\\', '/')
            
            # Convert relative path to absolute within workspace
            search_base = workspace_root
            if path_str.startswith('./'):
                path_str = path_str[2:]
            
            if not path_str or path_str.endswith('/'):
                # User typed / alone or a directory path ending with /, show contents
                search_dir = search_base / path_str.rstrip('/') if path_str else search_base
                pattern = '*'
            else:
                # Extract directory and filename pattern
                last_slash = path_str.rfind('/')
                if last_slash != -1:
                    dir_part = path_str[:last_slash]
                    file_part = path_str[last_slash + 1:]
                    search_dir = search_base / dir_part
                    pattern = file_part + '*' if file_part else '*'
                else:
                    search_dir = search_base
                    pattern = path_str + '*' if path_str else '*'
            
            # Get matches within workspace only
            matches = []
            try:
                if search_dir.exists() and search_dir.is_dir():
                    for item in search_dir.glob(pattern):
                        # Only include items within workspace
                        try:
                            relative = item.relative_to(workspace_root)
                            rel_str = str(relative).replace('\\', '/')
                            if item.is_dir():
                                matches.append('/' + rel_str + '/')
                            else:
                                matches.append('/' + rel_str)
                        except ValueError:
                            # Skip items outside workspace
                            continue
            except:
                pass
            
            # Filter out common ignore patterns
            matches = [m for m in matches if not any(
                ignore in m for ignore in ['__pycache__', '.git', 'venv', 'node_modules', '.pyc']
            )]
            
            return sorted(matches)[:20]  # Limit to 20 suggestions
        else:
            return []
    except:
        return []


async def get_text_input_async(prompt: str) -> str:
    """Get text input with real-time file path highlighting using /."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.styles import Style as PTStyle
    from prompt_toolkit.formatted_text import HTML, FormattedText
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.lexers import Lexer
    from prompt_toolkit.document import Document
    import re as regex
    
    class FilePathLexer(Lexer):
        """Lexer that highlights file paths starting with / in accent color."""
        def lex_document(self, document):
            def get_line(lineno):
                line = document.lines[lineno]
                result = []
                
                # Find all file path patterns /something
                pattern = regex.compile(r'(/[^\s]+)')
                last_end = 0
                
                for match in pattern.finditer(line):
                    # Add text before the match in default style
                    if match.start() > last_end:
                        result.append(('', line[last_end:match.start()]))
                    
                    # Add the file path in accent color with background
                    file_path = match.group(1)
                    result.append((f'class:filepath', file_path))
                    last_end = match.end()
                
                # Add remaining text
                if last_end < len(line):
                    result.append(('', line[last_end:]))
                
                return result
            
            return get_line
    
    class PathCompleter(Completer):
        def get_completions(self, document, complete_event):
            text = document.text
            text_before_cursor = document.text_before_cursor
            
            # Find the last / symbol and get the word starting from it
            slash_pos = text_before_cursor.rfind('/')
            if slash_pos != -1:
                word = text_before_cursor[slash_pos:]
                completions = get_file_completions(text, word)
                for completion in completions:
                    # Display just the filename/folder with styled display
                    display_name = completion.lstrip('/').split('/')[-1] or completion
                    if completion.endswith('/'):
                        display_name = '📁 ' + display_name
                    else:
                        display_name = '📄 ' + display_name
                    
                    # White text in dropdown
                    yield Completion(
                        completion,
                        start_position=-len(word),
                        display=FormattedText([('#ffffff bold', display_name)])
                    )
    
    style = PTStyle.from_dict({
        'prompt': f'{theme_config["primary_color"]} bold',
        '': f'{theme_config["text_color"]}',
        'completion-menu': 'bg:#1a1a2e #ffffff',
        'completion-menu.completion': 'bg:#16213e #ffffff',
        'completion-menu.completion.current': f'bg:{theme_config["accent_color"]} #000000 bold',
        'scrollbar.background': 'bg:#444444',
        'scrollbar.button': f'bg:{theme_config["accent_color"]}',
        'filepath': f'fg:{theme_config["accent_color"]} bold bg:#2a2a3a',
    })
    
    # Create key bindings
    kb = KeyBindings()
    
    @kb.add('tab')
    def select_completion(event):
        """Use Tab to accept the current highlighted completion."""
        buff = event.app.current_buffer
        if buff.complete_state:
            buff.complete_state = None
        else:
            buff.start_completion(select_first=True)
    
    @kb.add('down')
    def next_completion(event):
        """Navigate down in completion menu."""
        buff = event.app.current_buffer
        if buff.complete_state:
            buff.complete_next()
    
    @kb.add('up')
    def prev_completion(event):
        """Navigate up in completion menu."""
        buff = event.app.current_buffer
        if buff.complete_state:
            buff.complete_previous()
    
    @kb.add('enter')
    def handle_enter(event):
        """Enter: submit the input."""
        buff = event.app.current_buffer
        if buff.complete_state:
            buff.complete_state = None
        buff.validate_and_handle()
    
    # Claude-style prompt with diamond and vibrant colors
    console.print()
    console.print(f"[bold {theme_config['primary_color']}]◆ {prompt}[/]")
    
    session = PromptSession(
        completer=PathCompleter(),
        lexer=FilePathLexer(),
        complete_while_typing=True,
        style=style,
        key_bindings=kb,
        message=HTML(f'<style fg="{theme_config["accent_color"]}" bg="">❯ </style>'),
    )
    
    result = await session.prompt_async()
    
    return result.strip()


async def get_directory_input_async(prompt: str) -> str:
    """Get directory path input with autocomplete for directories only."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.styles import Style as PTStyle
    from prompt_toolkit.formatted_text import HTML, FormattedText
    from prompt_toolkit.key_binding import KeyBindings
    
    class DirectoryCompleter(Completer):
        def get_completions(self, document, complete_event):
            text = document.text
            completions = get_directory_completions(text, text)
            for completion in completions:
                # Display directory name with folder icon
                display_name = Path(completion).name or completion
                display_name = '📁 ' + display_name
                
                yield Completion(
                    completion,
                    start_position=-len(text),
                    display=FormattedText([('#ffffff bold', display_name)])
                )
    
    style = PTStyle.from_dict({
        'prompt': f'{theme_config["primary_color"]} bold',
        '': f'{theme_config["text_color"]}',
        'completion-menu': 'bg:#1a1a2e #ffffff',
        'completion-menu.completion': 'bg:#16213e #ffffff',
        'completion-menu.completion.current': f'bg:{theme_config["accent_color"]} #000000 bold',
        'scrollbar.background': 'bg:#444444',
        'scrollbar.button': f'bg:{theme_config["accent_color"]}',
    })
    
    # Create key bindings
    kb = KeyBindings()
    
    @kb.add('tab')
    def select_completion(event):
        buff = event.app.current_buffer
        if buff.complete_state:
            buff.complete_state = None
        else:
            buff.start_completion(select_first=True)
    
    @kb.add('down')
    def next_completion(event):
        buff = event.app.current_buffer
        if buff.complete_state:
            buff.complete_next()
    
    @kb.add('up')
    def prev_completion(event):
        buff = event.app.current_buffer
        if buff.complete_state:
            buff.complete_previous()
    
    @kb.add('enter')
    def handle_enter(event):
        buff = event.app.current_buffer
        if buff.complete_state:
            buff.complete_state = None
        buff.validate_and_handle()
    
    console.print()
    console.print(f"[bold {theme_config['primary_color']}]◆ {prompt}[/]")
    
    session = PromptSession(
        completer=DirectoryCompleter(),
        complete_while_typing=True,
        style=style,
        key_bindings=kb,
        message=HTML(f'<style fg="{theme_config["accent_color"]}" bg="">❯ </style>'),
    )
    
    result = await session.prompt_async()
    
    return result.strip()
    """Get text input with real-time file path highlighting using /."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.styles import Style as PTStyle
    from prompt_toolkit.formatted_text import HTML, FormattedText
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.lexers import Lexer
    from prompt_toolkit.document import Document
    import re as regex
    
    class FilePathLexer(Lexer):
        """Lexer that highlights file paths starting with / in accent color."""
        def lex_document(self, document):
            def get_line(lineno):
                line = document.lines[lineno]
                result = []
                
                # Find all file path patterns /something
                pattern = regex.compile(r'(/[^\s]+)')
                last_end = 0
                
                for match in pattern.finditer(line):
                    # Add text before the match in default style
                    if match.start() > last_end:
                        result.append(('', line[last_end:match.start()]))
                    
                    # Add the file path in accent color with background
                    file_path = match.group(1)
                    result.append((f'class:filepath', file_path))
                    last_end = match.end()
                
                # Add remaining text
                if last_end < len(line):
                    result.append(('', line[last_end:]))
                
                return result
            
            return get_line
    
    class PathCompleter(Completer):
        def get_completions(self, document, complete_event):
            text = document.text
            text_before_cursor = document.text_before_cursor
            
            # Find the last / symbol and get the word starting from it
            slash_pos = text_before_cursor.rfind('/')
            if slash_pos != -1:
                word = text_before_cursor[slash_pos:]
                completions = get_file_completions(text, word)
                for completion in completions:
                    # Display just the filename/folder with styled display
                    display_name = completion.lstrip('/').split('/')[-1] or completion
                    if completion.endswith('/'):
                        display_name = '📁 ' + display_name
                    else:
                        display_name = '📄 ' + display_name
                    
                    # White text in dropdown
                    yield Completion(
                        completion,
                        start_position=-len(word),
                        display=FormattedText([('#ffffff bold', display_name)])
                    )
    
    style = PTStyle.from_dict({
        'prompt': f'{theme_config["primary_color"]} bold',
        '': f'{theme_config["text_color"]}',
        'completion-menu': 'bg:#1a1a2e #ffffff',
        'completion-menu.completion': 'bg:#16213e #ffffff',
        'completion-menu.completion.current': f'bg:{theme_config["accent_color"]} #000000 bold',
        'scrollbar.background': 'bg:#444444',
        'scrollbar.button': f'bg:{theme_config["accent_color"]}',
        'filepath': f'fg:{theme_config["accent_color"]} bold bg:#2a2a3a',
    })
    
    # Create key bindings
    kb = KeyBindings()
    
    @kb.add('tab')
    def select_completion(event):
        """Use Tab to accept the current highlighted completion."""
        buff = event.app.current_buffer
        if buff.complete_state:
            buff.complete_state = None
        else:
            buff.start_completion(select_first=True)
    
    @kb.add('down')
    def next_completion(event):
        """Navigate down in completion menu."""
        buff = event.app.current_buffer
        if buff.complete_state:
            buff.complete_next()
    
    @kb.add('up')
    def prev_completion(event):
        """Navigate up in completion menu."""
        buff = event.app.current_buffer
        if buff.complete_state:
            buff.complete_previous()
    
    @kb.add('enter')
    def handle_enter(event):
        """Enter: submit the input."""
        buff = event.app.current_buffer
        if buff.complete_state:
            buff.complete_state = None
        buff.validate_and_handle()
    
    # Claude-style prompt with diamond and vibrant colors
    console.print()
    console.print(f"[bold {theme_config['primary_color']}]◆ {prompt}[/]")
    
    session = PromptSession(
        completer=PathCompleter(),
        lexer=FilePathLexer(),
        complete_while_typing=True,
        style=style,
        key_bindings=kb,
        message=HTML(f'<style fg="{theme_config["accent_color"]}" bg="">❯ </style>'),
    )
    
    result = await session.prompt_async()
    
    return result.strip()



def get_text_input(prompt: str, placeholder: str = "") -> str:
    """Get text input with creative styling."""
    console.print()
    console.print(f"[bold {theme_config['primary_color']}]◆ {prompt}[/]")
    if placeholder:
        console.print(f"  [dim italic]{placeholder}[/]")
    console.print(f"[{theme_config['accent_color']}]❯[/] ", end="")
    text = input().strip()
    console.print()
    return text


def typewriter_print(text: str, delay: float = 0.01):
    """Print text with typewriter effect character by character."""
    import sys
    import time
    
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        # Faster for spaces and newlines, slower for other characters
        if char in ' \n':
            time.sleep(delay * 0.5)
        else:
            time.sleep(delay)
    print()  # Final newline


async def typewriter_response(response_text: str):
    """Display response with typewriter effect, handling markdown properly."""
    import time
    import sys
    
    # For markdown content, we'll type it out line by line with rich formatting
    lines = response_text.split('\n')
    
    for line in lines:
        # Print each line with a slight delay between characters
        if line.strip():
            # Use console for rich formatting, but add small delay between lines
            console.print(Markdown(line))
            await asyncio.sleep(0.03)  # Small delay between lines
        else:
            console.print()
            await asyncio.sleep(0.01)


def render_response_with_code_blocks(response_text: str):
    """Render response with styled code blocks that have copy functionality."""
    import re
    import pyperclip
    
    global last_code_blocks
    last_code_blocks = []
    
    # Pattern to match code blocks with optional language
    code_pattern = r'```(\w*)\n(.*?)```'
    
    # Split text by code blocks
    parts = re.split(r'(```\w*\n.*?```)', response_text, flags=re.DOTALL)
    
    code_index = 0
    for part in parts:
        code_match = re.match(r'```(\w*)\n(.*?)```', part, re.DOTALL)
        if code_match:
            language = code_match.group(1) or 'code'
            code_content = code_match.group(2).rstrip()
            code_index += 1
            
            # Store code for copy functionality
            last_code_blocks.append(code_content)
            
            # Print styled code block header
            console.print()
            console.print(f"[{theme_config['border_color']}]┌─[/] [{theme_config['accent_color']} bold]{language}[/] [{theme_config['border_color']}]{'─' * 60}[/] [dim][ /copy {code_index} ][/]")
            console.print(f"[{theme_config['border_color']}]│[/]")
            
            # Print code with syntax highlighting
            for line in code_content.split('\n'):
                console.print(f"[{theme_config['border_color']}]│[/]  [{theme_config['text_color']}]{line}[/]")
            
            console.print(f"[{theme_config['border_color']}]│[/]")
            console.print(f"[{theme_config['border_color']}]└{'─' * 70}[/]")
            console.print()
        else:
            # Render regular markdown
            if part.strip():
                console.print(Markdown(part))


def copy_code_block(index: int) -> bool:
    """Copy a code block to clipboard by index."""
    try:
        import pyperclip
        if 1 <= index <= len(last_code_blocks):
            pyperclip.copy(last_code_blocks[index - 1])
            return True
    except:
        pass
    return False


def display_file_diff(file_path: str, old_content: str, new_content: str, is_new: bool = False):
    """Display a diff between old and new file content with red/green indicators."""
    console.print()
    console.print(f"[bold {theme_config['accent_color']}]━━━ {file_path} {'(NEW FILE)' if is_new else ''} ━━━[/]")
    console.print()
    
    if is_new:
        # For new files, show all lines as additions
        lines = new_content.splitlines(keepends=False)
        for line in lines:
            console.print(f"[bold green]+ {line}[/]")
    else:
        # Generate diff for existing files
        old_lines = old_content.splitlines(keepends=False)
        new_lines = new_content.splitlines(keepends=False)
        
        diff = difflib.unified_diff(
            old_lines, 
            new_lines, 
            lineterm='',
            fromfile=f'a/{file_path}',
            tofile=f'b/{file_path}'
        )
        
        # Skip the file headers (first 2 lines: --- and +++)
        diff_lines = list(diff)
        for line in diff_lines[2:]:
            if line.startswith('@@'):
                # Hunk header
                console.print(f"[bold cyan]{line}[/]")
            elif line.startswith('+'):
                # Added line
                console.print(f"[bold green]{line}[/]")
            elif line.startswith('-'):
                # Removed line
                console.print(f"[bold red]{line}[/]")
            else:
                # Context line
                console.print(f"[dim]{line}[/]")
    
    console.print()
    console.print(f"[bold {theme_config['accent_color']}]━━━ End of {file_path} ━━━[/]")
    console.print()


def open_vscode_diff(original_path: Path, new_content: str, file_label: str, is_new: bool = False):
    """Open diff viewer to show changes visually based on user preferences."""
    try:
        # Check if diff viewer is enabled
        if not diff_preferences['enabled']:
            return None
        
        # Create a temporary file with the new content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tmp', delete=False, encoding='utf-8') as tmp:
            tmp.write(new_content)
            tmp_path = tmp.name
        
        # Choose editor based on preferences
        if diff_preferences['editor'] == 'none':
            # Just return tmp path without opening any editor
            return tmp_path
        elif diff_preferences['editor'] == 'default':
            # Use system default editor
            try:
                if os.name == 'nt':
                    os.startfile(tmp_path)
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', tmp_path])
                else:
                    subprocess.Popen(['xdg-open', tmp_path])
                return tmp_path
            except Exception:
                return tmp_path
        else:  # vscode
            # Try multiple ways to launch VS Code on Windows
            vscode_commands = [
                'code',
                'code.cmd',
                os.path.expandvars(r'%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd'),
                os.path.expandvars(r'%PROGRAMFILES%\Microsoft VS Code\bin\code.cmd'),
            ]
            
            launched = False
            for cmd in vscode_commands:
                try:
                    if is_new:
                        # For new files, just open the temp file in preview mode
                        subprocess.Popen([cmd, '--reuse-window', tmp_path], 
                                       stdout=subprocess.DEVNULL, 
                                       stderr=subprocess.DEVNULL,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    else:
                        # For existing files, open VS Code diff editor
                        # Format: code --diff <original> <modified>
                        subprocess.Popen([cmd, '--diff', str(original_path), tmp_path],
                                       stdout=subprocess.DEVNULL, 
                                       stderr=subprocess.DEVNULL,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    launched = True
                    break
                except (FileNotFoundError, OSError):
                    continue
            
            if not launched:
                raise FileNotFoundError("VS Code not found. Make sure VS Code is installed and 'code' command is in PATH.")
        
        return tmp_path
    except Exception as e:
        console.print(f"[{theme_config['warning_color']}]⚠ Could not open diff viewer: {e}[/]")
        return None


# =============================================================================
# Cookie Management
# =============================================================================

def save_cookies(psid: str, psidts: Optional[str] = None):
    """Save cookies to local file."""
    cookies_file = Path('.gemini_cookies.json')
    cookies_data = {
        'psid': psid,
        'psidts': psidts
    }
    try:
        cookies_file.write_text(json.dumps(cookies_data, indent=2))
    except Exception as e:
        console.print(f"[yellow]⚠ Could not save cookies: {e}[/]")


def load_cookies() -> Tuple[Optional[str], Optional[str]]:
    """Load cookies from local file."""
    cookies_file = Path('.gemini_cookies.json')
    if cookies_file.exists():
        try:
            cookies_data = json.loads(cookies_file.read_text())
            return cookies_data.get('psid'), cookies_data.get('psidts')
        except Exception as e:
            console.print(f"[yellow]⚠ Could not load cookies: {e}[/]")
    return None, None


def get_cookies() -> Tuple[Optional[str], Optional[str]]:
    """Get authentication cookies from user."""
    
    console.print(f"\n[bold {theme_config['primary_color']}]◆ Cookie Setup ◆[/]")
    console.rule(style=theme_config['border_color'])
    
    console.print(f"\n[{theme_config['text_color']}]◆ To get your authentication cookies:[/]\n")
    console.print(f" [{theme_config['accent_color']}]1.[/] Open [{theme_config['secondary_color']}]https://gemini.google.com[/] in your browser")
    console.print(f" [{theme_config['accent_color']}]2.[/] Press [{theme_config['secondary_color']}]F12[/] to open Developer Tools")
    console.print(f" [{theme_config['accent_color']}]3.[/] Go to: [{theme_config['secondary_color']}]Application[/] → [{theme_config['secondary_color']}]Cookies[/] → [{theme_config['secondary_color']}]https://gemini.google.com[/]")
    console.print(f" [{theme_config['accent_color']}]4.[/] Copy the cookie values below:\n")
    
    console.rule(style=theme_config['border_color'])
    
    try:
        # Get __Secure-1PSID
        psid = get_text_input("◆ __Secure-1PSID (required)", "Paste cookie value here")
        
        if not psid:
            console.print(f"\n[red]✗ No value entered[/]")
            return None, None
        
        # Get __Secure-1PSIDTS
        psidts = get_text_input("◆ __Secure-1PSIDTS (optional)", "Press Enter to skip") or None
        
        console.print(f"\n[bold {theme_config['success_color']}]✓ Cookies received successfully[/]\n")
        
        return psid, psidts
        
    except (KeyboardInterrupt, EOFError):
        console.print(f"\n\n[{theme_config['warning_color']}]⚠ Cancelled[/]")
        return None, None


# =============================================================================
# Gemini Client
# =============================================================================

async def initialize_client(psid: str, psidts: Optional[str] = None) -> Optional[GeminiClient]:
    """Initialize Gemini client."""
    try:
        with console.status(f"[bold {theme_config['primary_color']}]◆ Gemini is connecting...[/]", spinner="dots"):
            client = GeminiClient(secure_1psid=psid, secure_1psidts=psidts)
            await client.init(timeout=45)
        
        console.print(f"[bold {theme_config['success_color']}]✓ Connected to Gemini[/]\n")
        return client
        
    except Exception as e:
        console.print(f"[bold red]✗ Failed to connect[/]")
        console.print(f"[red]Error: {e}[/]")
        return None


# =============================================================================
# Workspace Search (for Agent mode)
# =============================================================================

def search_workspace(query: str, file_pattern: str = "**/*", max_results: int = 20) -> List[dict]:
    """Search workspace for files matching query. Returns metadata only (paths, not content).
    Searches recursively through ALL subdirectories regardless of depth."""
    workspace_root = Path.cwd()
    results = []
    
    try:
        # Use rglob for recursive search through all subdirectories
        # rglob('**/*') will search through ALL nested subdirectories
        if file_pattern == "**/*" or not file_pattern:
            # Search all files recursively
            search_pattern = "**/*"
        elif not file_pattern.startswith("**/"):
            # Ensure pattern is recursive
            search_pattern = f"**/{file_pattern}"
        else:
            search_pattern = file_pattern
        
        # Search through all files recursively (no depth limit)
        if search_pattern.startswith("**/"):
            pattern = search_pattern[3:]  # Remove **/ prefix
        else:
            pattern = search_pattern if search_pattern != "**/*" else "*"
        
        # Use rglob with proper pattern - rglob already searches recursively
        for file_path in workspace_root.rglob(pattern):
            # Skip directories
            if not file_path.is_file():
                continue
            
            # Skip large files and common ignore patterns
            if any(ignore in str(file_path) for ignore in ['__pycache__', '.git', 'venv', 'node_modules', '.pyc']):
                continue
            
            try:
                if file_path.stat().st_size > 500_000:  # Skip files > 500KB
                    continue
                
                # Check if query matches FILENAME first (case-insensitive)
                patterns = query.split('|')  # Support multiple patterns
                filename = file_path.name
                filename_match = any(re.search(pattern, filename, re.IGNORECASE) for pattern in patterns)
                
                # If filename matches, add immediately
                if filename_match:
                    relative_path = file_path.relative_to(workspace_root)
                    content = file_path.read_text(errors='ignore')
                    results.append({
                        'path': str(relative_path).replace('\\', '/'),
                        'size': f"{file_path.stat().st_size / 1024:.1f}kb",
                        'lines': content.count('\n') + 1
                    })
                    continue  # Skip content search if filename already matched
                
                # Otherwise check file content
                content = file_path.read_text(errors='ignore')
                if any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns):
                    relative_path = file_path.relative_to(workspace_root)
                    results.append({
                        'path': str(relative_path).replace('\\', '/'),
                        'size': f"{file_path.stat().st_size / 1024:.1f}kb",
                        'lines': content.count('\n') + 1
                    })
            except Exception:
                continue
        
        # Sort by size (smaller files first - easier to digest)
        results.sort(key=lambda x: float(x['size'].replace('kb', '')))
        return results[:max_results]
    except Exception:
        return []


def read_workspace_files(file_paths: List[str], max_size_per_file: int = 15000) -> dict:
    """Read specific files from workspace. Returns dict of {path: content}."""
    workspace_root = Path.cwd()
    file_contents = {}
    
    for path_str in file_paths:
        try:
            # Normalize path
            path_str = path_str.lstrip('/')
            file_path = workspace_root / path_str
            
            if file_path.exists() and file_path.is_file():
                content = file_path.read_text(errors='ignore')
                # Limit content size to avoid token overflow
                if len(content) > max_size_per_file:
                    content = content[:max_size_per_file] + f"\n\n... [truncated, file is {len(content)} chars total]"
                file_contents[path_str] = content
            else:
                file_contents[path_str] = f"Error: File not found or not accessible"
        except Exception as e:
            file_contents[path_str] = f"Error reading file: {e}"
    
    return file_contents


# =============================================================================
# System Command Execution (for Agent/System Agent mode)
# =============================================================================

def execute_system_command(command: str) -> Tuple[bool, str]:
    """
    Execute system commands like opening applications, adjusting settings, etc.
    Returns (success: bool, output: str)
    """
    try:
        if os.name == 'nt':  # Windows
            # Use PowerShell for Windows commands
            result = subprocess.run(
                ['powershell', '-Command', command],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:  # Unix/Linux/Mac
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
        
        output = result.stdout if result.stdout else result.stderr
        success = result.returncode == 0
        
        return success, output.strip() if output else "Command executed"
    except Exception as e:
        return False, f"Error executing command: {str(e)}"


# =============================================================================
# Git Integration
# =============================================================================

def get_git_status() -> dict:
    """Get current git status."""
    try:
        workspace_root = Path.cwd()
        
        # Check if git repo
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        if result.returncode != 0:
            return {'is_repo': False}
        
        # Get status
        status_result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        # Get current branch
        branch_result = subprocess.run(
            ['git', 'branch', '--show-current'],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        return {
            'is_repo': True,
            'status': status_result.stdout,
            'branch': branch_result.stdout.strip(),
            'has_changes': bool(status_result.stdout.strip())
        }
    except Exception as e:
        return {'is_repo': False, 'error': str(e)}


async def generate_commit_message(chat, modified_files: List[str]) -> str:
    """Generate a commit message based on modified files."""
    try:
        # Get diff for context
        workspace_root = Path.cwd()
        diff_result = subprocess.run(
            ['git', 'diff', '--staged'] if modified_files else ['git', 'diff'],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        # Get diff text safely
        diff_text = diff_result.stdout[:3000] if diff_result.stdout else "No diff available"
        
        # Build file list string
        files_str = ', '.join(modified_files) if modified_files else "all changes"
        
        prompt = f"""Generate a concise git commit message for these changes.
Files modified: {files_str}

Diff:
{diff_text}

Return ONLY the commit message (one line summary, then optional detailed description). No explanations."""
        
        response = await chat.send_message(prompt)
        return response.text.strip() if response and response.text else "Update files"
    except Exception as e:
        # Safe fallback message
        if modified_files:
            return f"Update {', '.join(modified_files)}"
        else:
            return "Update files"


def git_commit(message: str, files: List[str] = None) -> tuple:
    """Commit changes with message."""
    try:
        workspace_root = Path.cwd()
        
        # Add files
        if files:
            for file in files:
                subprocess.run(
                    ['git', 'add', file],
                    cwd=workspace_root,
                    check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
        else:
            subprocess.run(
                ['git', 'add', '-A'],
                cwd=workspace_root,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
        
        # Commit
        result = subprocess.run(
            ['git', 'commit', '-m', message],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        return True, result.stdout
    except Exception as e:
        return False, str(e)


def git_push() -> tuple:
    """Push commits to remote."""
    try:
        workspace_root = Path.cwd()
        
        result = subprocess.run(
            ['git', 'push'],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)


# =============================================================================
# Image Settings Management
# =============================================================================

# Global image settings
image_settings = {
    'save_path': Path('gemini_images')  # Default path
}


async def configure_image_settings():
    """Configure image save settings."""
    clear_screen()
    print_banner()
    
    console.print(f"\n[bold {theme_config['primary_color']}]◆ Image Save Settings ◆[/]")
    console.rule(style=theme_config['border_color'])
    
    console.print()
    console.print(f"[{theme_config['text_color']}]Current save path:[/] [{theme_config['accent_color']}]{image_settings['save_path']}[/]")
    console.print(f"[dim]Type to see directory suggestions. Press Enter to keep current.[/]")
    console.print()
    
    # Get new path from user with directory autocomplete
    new_path = await get_directory_input_async("Enter save directory path")
    
    if new_path:
        # Remove trailing separator if present
        new_path = new_path.rstrip(os.sep)
        image_settings['save_path'] = Path(new_path)
        console.print(f"\n[bold {theme_config['success_color']}]✓ Save path updated to: {image_settings['save_path']}[/]\n")
    else:
        console.print(f"\n[{theme_config['text_color']}]Keeping current path[/]\n")
    
    await asyncio.sleep(1)


# =============================================================================
# Git Settings Management
# =============================================================================

async def configure_git_settings():
    """Configure Git workflow preferences."""
    clear_screen()
    print_banner()
    
    console.print(f"\n[bold {theme_config['primary_color']}]◆ Git Workflow Settings ◆[/]")
    console.rule(style=theme_config['border_color'])
    
    custom_style = Style([
        ('pointer', f'fg:{theme_config["accent_color"]} bold'),
        ('highlighted', f'fg:{theme_config["primary_color"]} bold'),
        ('question', f'fg:{theme_config["secondary_color"]} bold'),
    ])
    
    console.print()
    console.print(f"[bold {theme_config['secondary_color']}]Commit Mode:[/]")
    console.print(f"[dim]When should changes be committed?[/]\n")
    
    commit_mode_choice = await questionary.select(
        "",
        choices=[
            '◆ Ask on exit (recommended)',
            '◆ After every change'
        ],
        pointer="❯",
        style=custom_style,
        qmark="",
        show_selected=False,
        use_shortcuts=False,
        default='◆ Ask on exit (recommended)' if git_preferences['commit_mode'] == 'on_exit' else '◆ After every change'
    ).ask_async()
    
    if commit_mode_choice == '◆ Ask on exit (recommended)':
        git_preferences['commit_mode'] = 'on_exit'
    else:
        git_preferences['commit_mode'] = 'immediate'
    
    console.print()
    console.print(f"[bold {theme_config['secondary_color']}]Auto Push:[/]")
    console.print(f"[dim]Automatically push after committing?[/]\n")
    
    auto_push_choice = await questionary.select(
        "",
        choices=['◆ Yes', '◆ No'],
        pointer="❯",
        style=custom_style,
        qmark="",
        show_selected=False,
        use_shortcuts=False,
        default='◆ Yes' if git_preferences['auto_push'] else '◆ No'
    ).ask_async()
    
    git_preferences['auto_push'] = (auto_push_choice == '◆ Yes')
    
    console.print()
    console.print(f"[bold {theme_config['secondary_color']}]Branch Selection:[/]")
    console.print(f"[dim]Ask to create/select branch in System Agent mode?[/]\n")
    
    branch_choice = await questionary.select(
        "",
        choices=['◆ Yes', '◆ No'],
        pointer="❯",
        style=custom_style,
        qmark="",
        show_selected=False,
        use_shortcuts=False,
        default='◆ Yes' if git_preferences['ask_branch'] else '◆ No'
    ).ask_async()
    
    git_preferences['ask_branch'] = (branch_choice == '◆ Yes')
    
    console.print()
    console.print(f"[bold {theme_config['success_color']}]✓ Git settings saved[/]")
    console.print()
    console.print(f"[dim]Commit mode: {git_preferences['commit_mode']}[/]")
    console.print(f"[dim]Auto push: {'Yes' if git_preferences['auto_push'] else 'No'}[/]")
    console.print(f"[dim]Ask branch: {'Yes' if git_preferences['ask_branch'] else 'No'}[/]\n")
    
    await asyncio.sleep(2)


# =============================================================================
# Settings Menu
# =============================================================================

async def settings_menu():
    """Main settings menu."""
    while True:
        clear_screen()
        print_banner()
        
        console.print(f"\n[bold {theme_config['primary_color']}]◆ Settings ◆[/]")
        console.rule(style=theme_config['border_color'])
        
        custom_style = Style([
            ('pointer', f'fg:{theme_config["accent_color"]} bold'),
            ('highlighted', f'fg:{theme_config["primary_color"]} bold'),
            ('question', f'fg:{theme_config["secondary_color"]} bold'),
            ('instruction', 'fg:#555555'),
        ])
        
        console.print()
        choice = await questionary.select(
            "Choose a setting to configure:",
            choices=["◆ GitHub Integration", "◆ View Diff Settings", "◆ Back to Main Menu"],
            pointer="❯",
            style=custom_style,
            qmark="",
            instruction="(Use arrow keys)",
            show_selected=False,
            use_shortcuts=False
        ).ask_async()
        
        if choice == "◆ Back to Main Menu":
            return
        elif choice == "◆ GitHub Integration":
            await configure_github_integration()
        elif choice == "◆ View Diff Settings":
            await configure_diff_settings()


async def configure_github_integration():
    """Configure GitHub integration settings."""
    clear_screen()
    print_banner()
    
    console.print(f"\n[bold {theme_config['primary_color']}]◆ GitHub Integration ◆[/]")
    console.rule(style=theme_config['border_color'])
    
    custom_style = Style([
        ('pointer', f'fg:{theme_config["accent_color"]} bold'),
        ('highlighted', f'fg:{theme_config["primary_color"]} bold'),
        ('question', f'fg:{theme_config["secondary_color"]} bold'),
    ])
    
    console.print()
    console.print(f"[bold {theme_config['secondary_color']}]Enable Git Integration:[/]")
    console.print(f"[dim]Enable automatic git operations (commits, pushes)?[/]\n")
    
    enable_choice = await questionary.select(
        "",
        choices=['◆ Yes', '◆ No'],
        pointer="❯",
        style=custom_style,
        qmark="",
        show_selected=False,
        use_shortcuts=False,
        default='◆ Yes' if git_preferences['enabled'] else '◆ No'
    ).ask_async()
    
    git_preferences['enabled'] = (enable_choice == '◆ Yes')
    
    if git_preferences['enabled']:
        # Ask for commit mode
        console.print()
        console.print(f"[bold {theme_config['secondary_color']}]Commit Mode:[/]")
        console.print(f"[dim]When should changes be committed?[/]\n")
        
        commit_mode_choice = await questionary.select(
            "",
            choices=[
                '◆ Ask on exit (recommended)',
                '◆ After every change'
            ],
            pointer="❯",
            style=custom_style,
            qmark="",
            show_selected=False,
            use_shortcuts=False,
            default='◆ Ask on exit (recommended)' if git_preferences['commit_mode'] == 'on_exit' else '◆ After every change'
        ).ask_async()
        
        if commit_mode_choice == '◆ Ask on exit (recommended)':
            git_preferences['commit_mode'] = 'on_exit'
        else:
            git_preferences['commit_mode'] = 'immediate'
        
        # Ask for auto push
        console.print()
        console.print(f"[bold {theme_config['secondary_color']}]Auto Push:[/]")
        console.print(f"[dim]Automatically push after committing?[/]\n")
        
        auto_push_choice = await questionary.select(
            "",
            choices=['◆ Yes', '◆ No'],
            pointer="❯",
            style=custom_style,
            qmark="",
            show_selected=False,
            use_shortcuts=False,
            default='◆ Yes' if git_preferences['auto_push'] else '◆ No'
        ).ask_async()
        
        git_preferences['auto_push'] = (auto_push_choice == '◆ Yes')
        
        # Ask for branch selection
        console.print()
        console.print(f"[bold {theme_config['secondary_color']}]Branch Selection:[/]")
        console.print(f"[dim]Ask to create/select branch in System Agent mode?[/]\n")
        
        branch_choice = await questionary.select(
            "",
            choices=['◆ Yes', '◆ No'],
            pointer="❯",
            style=custom_style,
            qmark="",
            show_selected=False,
            use_shortcuts=False,
            default='◆ Yes' if git_preferences['ask_branch'] else '◆ No'
        ).ask_async()
        
        git_preferences['ask_branch'] = (branch_choice == '◆ Yes')
    
    console.print()
    console.print(f"[bold {theme_config['success_color']}]✓ GitHub integration settings saved[/]")
    console.print()
    console.print(f"[dim]Git integration: {'Enabled' if git_preferences['enabled'] else 'Disabled'}[/]")
    if git_preferences['enabled']:
        console.print(f"[dim]Commit mode: {git_preferences['commit_mode']}[/]")
        console.print(f"[dim]Auto push: {'Yes' if git_preferences['auto_push'] else 'No'}[/]")
        console.print(f"[dim]Ask branch: {'Yes' if git_preferences['ask_branch'] else 'No'}[/]")
    console.print()
    
    await asyncio.sleep(2)


async def configure_diff_settings():
    """Configure diff viewing settings."""
    clear_screen()
    print_banner()
    
    console.print(f"\n[bold {theme_config['primary_color']}]◆ View Diff Settings ◆[/]")
    console.rule(style=theme_config['border_color'])
    
    custom_style = Style([
        ('pointer', f'fg:{theme_config["accent_color"]} bold'),
        ('highlighted', f'fg:{theme_config["primary_color"]} bold'),
        ('question', f'fg:{theme_config["secondary_color"]} bold'),
    ])
    
    console.print()
    console.print(f"[bold {theme_config['secondary_color']}]Enable Diff Viewer:[/]")
    console.print(f"[{theme_config['text_color']}]Show file changes in a diff viewer before applying?[/]\n")
    
    enable_choice = await questionary.select(
        "",
        choices=['◆ Yes', '◆ No'],
        pointer="❯",
        style=custom_style,
        qmark="",
        show_selected=False,
        use_shortcuts=False,
        default='◆ Yes' if diff_preferences['enabled'] else '◆ No'
    ).ask_async()
    
    diff_preferences['enabled'] = (enable_choice == '◆ Yes')
    
    if diff_preferences['enabled']:
        console.print()
        console.print(f"[bold {theme_config['secondary_color']}]Diff Editor:[/]")
        console.print(f"[{theme_config['text_color']}]Choose your preferred diff viewer:[/]\n")
        
        editor_choice = await questionary.select(
            "",
            choices=['◆ VS Code', '◆ System Default', '◆ None (terminal only)'],
            pointer="❯",
            style=custom_style,
            qmark="",
            show_selected=False,
            use_shortcuts=False,
            default='◆ VS Code' if diff_preferences['editor'] == 'vscode' else ('◆ System Default' if diff_preferences['editor'] == 'default' else '◆ None (terminal only)')
        ).ask_async()
        
        if editor_choice == '◆ VS Code':
            diff_preferences['editor'] = 'vscode'
        elif editor_choice == '◆ System Default':
            diff_preferences['editor'] = 'default'
        else:
            diff_preferences['editor'] = 'none'
    
    console.print()
    console.print(f"[bold {theme_config['success_color']}]✓ Diff viewer settings saved[/]")
    console.print()
    console.print(f"[dim]Diff viewer: {'Enabled' if diff_preferences['enabled'] else 'Disabled'}[/]")
    if diff_preferences['enabled']:
        console.print(f"[dim]Editor: {diff_preferences['editor']}[/]")
    console.print()
    
    await asyncio.sleep(2)


async def handle_exit_git_commit(chat):
    """Handle git commit when exiting semi-agent mode."""
    git_info = get_git_status()
    if git_info['is_repo'] and git_info['has_changes']:
        console.print()
        console.print(f"[bold {theme_config['warning_color']}]⚠ You have uncommitted changes[/]\n")
        
        custom_style = Style([
            ('pointer', f'fg:{theme_config["accent_color"]} bold'),
            ('highlighted', f'fg:{theme_config["primary_color"]} bold'),
        ])
        
        # Build choices based on auto_push preference
        choices = []
        if git_preferences['auto_push']:
            choices.extend(['◆ Yes, commit and push', '◆ Yes, commit only'])
        else:
            choices.append('◆ Yes, commit')
        choices.append('◆ No, exit without committing')
        
        commit_choice = await questionary.select(
            "Would you like to commit before exiting?",
            choices=choices,
            pointer="❯",
            style=custom_style,
            qmark="",
            show_selected=False,
            use_shortcuts=False
        ).ask_async()
        
        if commit_choice and 'Yes' in commit_choice:
            console.print()
            console.print(f"[bold {theme_config['primary_color']}]◆ Generating commit message...[/]")
            commit_msg = await generate_commit_message(chat, [])
            
            if commit_msg:
                console.print()
                console.print(f"[bold {theme_config['secondary_color']}]◆ Suggested commit message:[/]")
                console.print(f"[{theme_config['accent_color']}]{commit_msg}[/]")
                console.print()
                
                confirm = await questionary.select(
                    "Commit with this message?",
                    choices=['◆ Yes, commit', '◆ No, cancel'],
                    pointer="❯",
                    style=custom_style,
                    qmark="",
                    show_selected=False,
                    use_shortcuts=False
                ).ask_async()
                
                if confirm == '◆ Yes, commit':
                    success, output = git_commit(commit_msg)
                    if success:
                        console.print(f"\n[bold {theme_config['success_color']}]✓ Committed successfully[/]")
                        console.print(f"[dim]{output}[/]")
                        
                        # Push if user selected commit and push
                        if 'push' in commit_choice.lower():
                            console.print(f"[bold {theme_config['primary_color']}]◆ Pushing to remote...[/]")
                            push_success, push_output = git_push()
                            if push_success:
                                console.print(f"[bold {theme_config['success_color']}]✓ Pushed successfully[/]")
                            else:
                                console.print(f"[bold red]✗ Push failed:[/] {push_output}")
                        console.print()
                    else:
                        console.print(f"\n[bold red]✗ Commit failed:[/] {output}\n")


def get_git_branches():
    """Get list of git branches."""
    try:
        # Get local branches only
        result = subprocess.run(
            ['git', 'branch'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        if result.returncode == 0:
            branches = []
            current_branch = None
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith('*'):
                    # Current branch
                    current_branch = line[2:].strip()
                    branches.append(current_branch)
                elif line:
                    # Other local branches
                    branches.append(line)
            return branches, current_branch
        return [], None
    except Exception:
        return [], None


async def handle_branch_selection():
    """Handle branch creation or selection for System Agent mode."""
    git_info = get_git_status()
    
    if not git_info['is_repo']:
        return None
    
    if not git_preferences['ask_branch']:
        return None
    
    branches, current_branch = get_git_branches()
    
    if not branches:
        return None
    
    console.print()
    console.print(f"[bold {theme_config['primary_color']}]◆ Git Branch Management ◆[/]")
    console.print(f"[{theme_config['text_color']}]Current branch:[/] [{theme_config['accent_color']}]{current_branch}[/]\n")
    
    custom_style = Style([
        ('pointer', f'fg:{theme_config["accent_color"]} bold'),
        ('highlighted', f'fg:{theme_config["primary_color"]} bold'),
    ])
    
    choice = await questionary.select(
        "Would you like to work on a different branch?",
        choices=[
            '◆ Stay on current branch',
            '◆ Create new branch',
            '◆ Switch to existing branch'
        ],
        pointer="❯",
        style=custom_style,
        qmark="",
        show_selected=False,
        use_shortcuts=False
    ).ask_async()
    
    if choice == '◆ Create new branch':
        console.print()
        branch_name = await questionary.text(
            "Enter new branch name:",
            style=custom_style,
            qmark=""
        ).ask_async()
        
        if branch_name:
            result = subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                console.print(f"\n[bold {theme_config['success_color']}]✓ Created and switched to branch: {branch_name}[/]\n")
                return branch_name
            else:
                console.print(f"\n[bold red]✗ Failed to create branch: {result.stderr}[/]\n")
                return None
    
    elif choice == '◆ Switch to existing branch':
        console.print()
        branch_choices = [f'◆ {b}' for b in branches if b != current_branch]
        
        if not branch_choices:
            console.print(f"[{theme_config['warning_color']}]No other branches available[/]\n")
            return None
        
        selected = await questionary.select(
            "Select branch:",
            choices=branch_choices,
            pointer="❯",
            style=custom_style,
            qmark="",
            show_selected=False,
            use_shortcuts=False
        ).ask_async()
        
        if selected:
            branch_name = selected.replace('◆ ', '')
            result = subprocess.run(
                ['git', 'checkout', branch_name],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                console.print(f"\n[bold {theme_config['success_color']}]✓ Switched to branch: {branch_name}[/]\n")
                return branch_name
            else:
                console.print(f"\n[bold red]✗ Failed to switch branch: {result.stderr}[/]\n")
                return None
    
    return None


# =============================================================================
# Chat Interface
# =============================================================================

async def send_message(chat, message: str) -> tuple:
    """Send message to Gemini chat session. Returns (text, images_list)."""
    try:
        response = await chat.send_message(message)
        
        text = response.text if response and response.text else ""
        images = []
        
        # Check for images in response
        if response and hasattr(response, 'images') and response.images:
            images = response.images
        
        # If no text but has images, show placeholder
        if not text and images:
            text = "_Image generated successfully_"
        elif not text and not images:
            text = "[No response]"
        
        return text, images
    except asyncio.TimeoutError:
        return "[red][Timeout - Please try again][/]", []
    except Exception as e:
        return f"[red][Error: {str(e)}][/]", []


# =============================================================================
# AutoBot Mode - Fully Autonomous Agent
# =============================================================================

async def execute_autobot_command(command: str, cwd: str = None) -> Tuple[bool, str]:
    """
    Execute a command for AutoBot mode with output capture.
    Returns (success: bool, output: str)
    Automatically answers 'y' to prompts for non-interactive execution.
    """
    try:
        working_dir = cwd if cwd else os.getcwd()
        
        if os.name == 'nt':  # Windows
            # Wrap command to auto-accept prompts by piping 'y'
            # Also set environment to be non-interactive
            env = os.environ.copy()
            env['CI'] = 'true'  # Many tools check this for non-interactive mode
            env['npm_config_yes'] = 'true'  # npm auto-yes
            
            result = subprocess.run(
                ['powershell', '-Command', command],
                capture_output=True,
                text=True,
                timeout=180,  # Increased timeout for build commands
                cwd=working_dir,
                creationflags=subprocess.CREATE_NO_WINDOW,
                input='y\ny\ny\n',  # Auto-answer yes to prompts
                env=env
            )
        else:  # Unix/Linux/Mac
            env = os.environ.copy()
            env['CI'] = 'true'
            env['npm_config_yes'] = 'true'
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=180,
                cwd=working_dir,
                input='y\ny\ny\n',
                env=env
            )
        
        # Combine stdout and stderr for complete output
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr if output else result.stderr
        
        success = result.returncode == 0
        return success, output.strip() if output else "Command executed successfully"
    except subprocess.TimeoutExpired:
        return False, "Command timed out after 180 seconds. The command may still be running."
    except Exception as e:
        return False, f"Error executing command: {str(e)}"


async def autobot_loop(client: GeminiClient):
    """AutoBot Mode - Fully autonomous agent that executes tasks from a single prompt."""
    
    clear_screen()
    print_banner()
    
    console.print(f"[bold {theme_config['primary_color']}]◆ AutoBot Mode ◆[/]")
    console.rule(style=theme_config['border_color'])
    console.print()
    console.print(f"[{theme_config['text_color']}]AutoBot is a fully autonomous agent that can:[/]")
    console.print(f" [{theme_config['accent_color']}]•[/] Execute terminal commands")
    console.print(f" [{theme_config['accent_color']}]•[/] Create and modify files")
    console.print(f" [{theme_config['accent_color']}]•[/] Search the web for information")
    console.print(f" [{theme_config['accent_color']}]•[/] Install packages and dependencies")
    console.print(f" [{theme_config['accent_color']}]•[/] Complete complex multi-step tasks autonomously")
    console.print()
    console.print(f"[{theme_config['warning_color']}]⚠ Warning: AutoBot will execute commands on your system![/]")
    console.print(f"[dim]Give it a task and it will work autonomously until completion.[/]")
    console.print(f"[dim]Type /exit or /mode to leave AutoBot mode.[/]")
    console.print()
    console.rule(style=theme_config['border_color'])
    console.print()
    
    # Start a chat session that persists across multiple tasks
    chat = client.start_chat()
    
    # Detect OS
    os_name = "Windows" if os.name == 'nt' else ("macOS" if sys.platform == 'darwin' else "Linux")
    workspace_dir = os.getcwd()
    
    # Track if this is the first task (for system prompt)
    first_task = True
    
    # Main session loop - keeps AutoBot running for multiple tasks
    while True:
        # Get the task from user
        if first_task:
            console.print(f"[bold {theme_config['secondary_color']}]◆ Enter your task:[/]")
            console.print(f"[dim]Example: Build a React app using Vite for travel planning[/]")
        else:
            console.print(f"[bold {theme_config['secondary_color']}]◆ Enter your next task or follow-up:[/]")
            console.print(f"[dim]Example: Add a dark mode toggle to the app[/]")
        console.print()
        
        try:
            task = await get_text_input_async("Task" if first_task else "Follow-up")
        except (EOFError, KeyboardInterrupt):
            console.print(f"\n\n[bold {theme_config['primary_color']}]◆ AutoBot session ended ◆[/]\n")
            return
        
        if not task:
            continue
        
        # Handle exit commands
        if task.lower() in ('/exit', '/quit', '/q', '/mode'):
            console.print(f"\n[bold {theme_config['primary_color']}]◆ AutoBot session ended ◆[/]\n")
            return
        
        # Handle clear screen
        if task.lower() == '/clear':
            clear_screen()
            print_banner()
            console.print(f"[bold {theme_config['primary_color']}]◆ AutoBot Mode ◆[/]")
            console.rule(style=theme_config['border_color'])
            console.print()
            continue
        
        # Update workspace directory (in case it changed)
        workspace_dir = os.getcwd()
        
        # Create the system prompt (only for first task, follow-ups use context)
        if first_task:
            autobot_system_prompt = f"""[AUTOBOT MODE - AUTONOMOUS AGENT SYSTEM]

You are AutoBot, a fully autonomous AI agent running on {os_name}. You have COMPLETE control to execute commands, create files, and perform any actions needed to complete the user's task.

WORKSPACE: {workspace_dir}

🔧 YOUR CAPABILITIES:
1. Execute terminal commands (cmd - any shell command)
2. Create/modify files (create_file - with path and content)
3. Search for information (search - web search query)
4. Read files (read_file - path to file)
5. Change working directory (cd - path)

📋 RESPONSE FORMAT (MANDATORY - RESPOND ONLY IN THIS JSON FORMAT):
```json
{{
    "thought": "Your reasoning about the current step",
    "action": "cmd|create_file|read_file|search|cd|done",
    "command": "The command to execute (for cmd action)",
    "path": "File path (for create_file/read_file)",
    "content": "File content (for create_file)",
    "query": "Search query (for search action)",
    "reply": "Message to show the user about what you're doing",
    "end": false
}}
```

🔴 CRITICAL RULES:
1. ALWAYS respond with ONLY a JSON code block - no other text
2. Execute ONE action at a time, wait for the result, then proceed
3. When the task is COMPLETE, set "end": true and include a final summary in "reply"
4. For multi-step tasks (like building apps), proceed step by step:
   - First install dependencies
   - Wait for output
   - Then create files
   - Wait for output
   - Continue until done
5. NEVER include markdown or text outside the JSON block
6. Use {os_name}-specific commands only!

📦 COMMON PATTERNS:
⚠️ CRITICAL: Use non-interactive commands! Always use -y or --yes flags!

For Vite React apps on {os_name}:
1. First create the project directory if needed: mkdir project-name
2. Then: npx -y create-vite@latest project-name --template react
3. cd into the directory
4. npm install
5. Modify files as needed
6. npm run dev (to start - but DON'T run this as it blocks!)

IMPORTANT COMMAND RULES:
- Use 'npx -y' instead of 'npm create' (auto-accepts package install)
- Never run blocking commands like 'npm run dev' or 'npm start' - tell user to run manually
- For npm: use 'npm install --yes' or just 'npm install' (it's non-interactive)
- Always check if directory exists before creating

For file creation: Use create_file action with full path and content.

🎯 USER'S TASK: {task}

Start by analyzing the task and taking the first action. Respond with JSON only!"""
            prompt_to_send = autobot_system_prompt
        else:
            # Follow-up task - just send the new task (context is preserved in chat)
            prompt_to_send = f"""[NEW TASK FROM USER]

The user wants you to do the following (this is a follow-up to your previous work):

🎯 NEW TASK: {task}

CURRENT WORKSPACE: {workspace_dir}

Remember:
- You have full context from previous tasks in this session
- Respond with JSON only
- Set "end": true when this new task is complete

Start working on this task. Respond with JSON only!"""
        
        console.print()
        console.print(f"[bold {theme_config['accent_color']}]◆ AutoBot is starting...[/]")
        console.print(f"[dim]Task: {task}[/]")
        console.print()
        
        # Send initial prompt
        with console.status(f"[bold {theme_config['primary_color']}]◆ AutoBot is thinking...[/]", spinner="dots"):
            response_text, _ = await send_message(chat, prompt_to_send)
        
        # Task execution loop
        iteration = 0
        max_iterations = 50  # Safety limit per task
        
        while iteration < max_iterations:
            iteration += 1
            
            # Parse JSON response
            json_pattern = r'```json\s*\n(.*?)\n```'
            json_match = re.search(json_pattern, response_text, re.DOTALL | re.IGNORECASE)
            
            if not json_match:
                # Try to find raw JSON
                try:
                    # Remove any markdown artifacts
                    clean_text = response_text.strip()
                    if clean_text.startswith('```'):
                        clean_text = re.sub(r'^```\w*\s*\n?', '', clean_text)
                        clean_text = re.sub(r'\n?```$', '', clean_text)
                    response_json = json.loads(clean_text)
                except:
                    console.print(f"[{theme_config['warning_color']}]⚠ Could not parse JSON response. Retrying...[/]")
                    console.print(f"[dim]Response: {response_text[:200]}...[/]")
                    
                    # Ask Gemini to format properly
                    retry_prompt = "Your response was not valid JSON. Please respond with ONLY a JSON code block in the format I specified. No other text!"
                    with console.status(f"[bold {theme_config['primary_color']}]◆ AutoBot is thinking...[/]", spinner="dots"):
                        response_text, _ = await send_message(chat, retry_prompt)
                    continue
            else:
                try:
                    json_str = json_match.group(1).strip()
                    response_json = json.loads(json_str)
                except json.JSONDecodeError as e:
                    console.print(f"[{theme_config['warning_color']}]⚠ JSON parse error: {e}[/]")
                    retry_prompt = "Your JSON was malformed. Please respond with valid JSON only!"
                    with console.status(f"[bold {theme_config['primary_color']}]◆ AutoBot is thinking...[/]", spinner="dots"):
                        response_text, _ = await send_message(chat, retry_prompt)
                    continue
            
            # Extract fields
            thought = response_json.get('thought', '')
            action = response_json.get('action', '')
            reply = response_json.get('reply', '')
            end = response_json.get('end', False)
            
            # Display thought and reply
            if thought:
                console.print(f"[dim italic]💭 {thought}[/]")
            if reply:
                console.print(f"[bold {theme_config['secondary_color']}]◆ AutoBot:[/] {reply}")
            console.print()
            
            # Check if task is complete
            if end:
                console.print(f"[bold {theme_config['success_color']}]✓ AutoBot has completed the task![/]")
                console.print()
                break
            
            # Execute the action
            action_result = ""
            action_success = True
            
            if action == "cmd":
                command = response_json.get('command', '')
                if command:
                    console.print(f"[{theme_config['accent_color']}]⚡ Executing:[/] [dim]{command}[/]")
                    
                    success, output = await execute_autobot_command(command)
                    action_success = success
                    action_result = output
                    
                    if success:
                        console.print(f"[{theme_config['success_color']}]✓ Command executed successfully[/]")
                    else:
                        console.print(f"[{theme_config['warning_color']}]⚠ Command returned an error[/]")
                    
                    # Show truncated output if too long
                    if len(output) > 500:
                        console.print(f"[dim]{output[:500]}... (truncated)[/]")
                    else:
                        console.print(f"[dim]{output}[/]")
            
            elif action == "create_file":
                file_path = response_json.get('path', '')
                file_content = response_json.get('content', '')
                
                if file_path and file_content is not None:
                    console.print(f"[{theme_config['accent_color']}]📝 Creating file:[/] [dim]{file_path}[/]")
                    
                    try:
                        # Handle relative and absolute paths
                        if not os.path.isabs(file_path):
                            file_path = os.path.join(workspace_dir, file_path)
                        
                        # Create parent directories
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        
                        # Write file
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(file_content)
                        
                        action_result = f"File created successfully at {file_path}"
                        console.print(f"[{theme_config['success_color']}]✓ File created[/]")
                    except Exception as e:
                        action_success = False
                        action_result = f"Error creating file: {str(e)}"
                        console.print(f"[{theme_config['warning_color']}]⚠ Failed to create file: {e}[/]")
            
            elif action == "read_file":
                file_path = response_json.get('path', '')
                
                if file_path:
                    console.print(f"[{theme_config['accent_color']}]📖 Reading file:[/] [dim]{file_path}[/]")
                    
                    try:
                        if not os.path.isabs(file_path):
                            file_path = os.path.join(workspace_dir, file_path)
                        
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Truncate if too long
                        if len(content) > 5000:
                            action_result = f"File content (truncated):\n{content[:5000]}...\n[TRUNCATED - file is {len(content)} chars]"
                        else:
                            action_result = f"File content:\n{content}"
                        
                        console.print(f"[{theme_config['success_color']}]✓ File read successfully[/]")
                    except Exception as e:
                        action_success = False
                        action_result = f"Error reading file: {str(e)}"
                        console.print(f"[{theme_config['warning_color']}]⚠ Failed to read file: {e}[/]")
            
            elif action == "cd":
                new_dir = response_json.get('path', '')
                
                if new_dir:
                    console.print(f"[{theme_config['accent_color']}]📂 Changing directory:[/] [dim]{new_dir}[/]")
                    
                    try:
                        if not os.path.isabs(new_dir):
                            new_dir = os.path.join(workspace_dir, new_dir)
                        
                        os.chdir(new_dir)
                        workspace_dir = new_dir
                        action_result = f"Changed directory to {new_dir}"
                        console.print(f"[{theme_config['success_color']}]✓ Directory changed[/]")
                    except Exception as e:
                        action_success = False
                        action_result = f"Error changing directory: {str(e)}"
                        console.print(f"[{theme_config['warning_color']}]⚠ Failed to change directory: {e}[/]")
            
            elif action == "search":
                query = response_json.get('query', '')
                
                if query:
                    console.print(f"[{theme_config['accent_color']}]🔍 Searching:[/] [dim]{query}[/]")
                    action_result = f"Search results for '{query}': [Web search not implemented - please use commands to install/verify packages or visit docs]"
                    console.print(f"[dim]{action_result}[/]")
            
            elif action == "done":
                console.print(f"[bold {theme_config['success_color']}]✓ AutoBot has completed the task![/]")
                console.print()
                break
            
            else:
                action_result = f"Unknown action: {action}. Please use: cmd, create_file, read_file, cd, search, or done"
                console.print(f"[{theme_config['warning_color']}]⚠ Unknown action: {action}[/]")
            
            console.print()
            
            # Send result back to Gemini
            status = "SUCCESS" if action_success else "ERROR"
            feedback_prompt = f"""[ACTION RESULT]
Status: {status}
Output:
{action_result}

Continue with the next step. Respond with JSON only!
Remember: When the task is complete, set "end": true"""
            
            with console.status(f"[bold {theme_config['primary_color']}]◆ AutoBot is thinking... (step {iteration})[/]", spinner="dots"):
                response_text, _ = await send_message(chat, feedback_prompt)
        
        if iteration >= max_iterations:
            console.print(f"[{theme_config['warning_color']}]⚠ AutoBot reached maximum iterations ({max_iterations}). Stopping this task.[/]")
        
        # Mark first task as done
        first_task = False
        
        console.print()
        console.rule(style=theme_config['border_color'])
        console.print()
        console.print(f"[bold {theme_config['accent_color']}]◆ Task completed! You can give another task or type /exit to leave.[/]")
        console.print()


async def chat_loop(client: GeminiClient, mode: str = "ask"):
    """Main chat loop."""
    
    # Start a chat session for continuous conversation
    chat = client.start_chat()
    
    # For agent mode or semi-agent mode, handle branch selection first
    if mode in ["semi-agent", "agent"] and git_preferences['enabled']:
        await handle_branch_selection()
    
    # For agent mode, show instructions
    if mode == "agent":
        clear_screen()
        print_banner()
        
        console.print(f"[bold {theme_config['primary_color']}]◆ Agent Mode ◆[/]")
        console.rule(style=theme_config['border_color'])
        console.print()
        console.print(f"[{theme_config['text_color']}]In this mode, Gemini can:[/]")
        console.print(f" [{theme_config['accent_color']}]•[/] Search your entire workspace for relevant files")
        console.print(f" [{theme_config['accent_color']}]•[/] Read specific files it needs")
        console.print(f" [{theme_config['accent_color']}]•[/] Make coordinated changes across multiple files")
        console.print(f" [{theme_config['accent_color']}]•[/] Work autonomously without you specifying files")
        console.print()
        console.print(f"[{theme_config['secondary_color']}]Just describe what you want to accomplish![/]")
        console.print()
        console.rule(style=theme_config['border_color'])
        console.print()
    
    # For image mode, show menu first
    if mode == "image":
        while True:
            clear_screen()
            print_banner()
            
            console.print()
            console.print(f"[bold {theme_config['accent_color']}]◆ Image Generation Mode[/]")
            console.print()
            console.print(f"[{theme_config['text_color']}]Current save path:[/] [{theme_config['accent_color']}]{image_settings['save_path']}[/]")
            console.print()
            
            # Create custom style
            custom_style = Style([
                ('pointer', f'fg:{theme_config["accent_color"]} bold'),
                ('highlighted', f'fg:{theme_config["primary_color"]} bold'),
                ('question', f'fg:{theme_config["secondary_color"]} bold'),
                ('instruction', 'fg:#555555'),
            ])
            
            image_choice = await questionary.select(
                "Choose an option:",
                choices=["◆ Generate Images", "◆ Save Settings", "◆ Back to Main Menu"],
                pointer="❯",
                style=custom_style,
                qmark="",
                instruction="(Use arrow keys)",
                show_selected=False,
                use_shortcuts=False
            ).ask_async()
            
            if image_choice == "◆ Back to Main Menu":
                return
            elif image_choice == "◆ Save Settings":
                await configure_image_settings()
                continue
            elif image_choice == "◆ Generate Images":
                break
    
    # Display mode indicator with diamonds
    mode_display = {
        "ask": "◆ Ask Mode",
        "semi-agent": "◆ System Agent Mode (AI Coding Assistant)",
        "agent": "◆ Agent Mode (Autonomous)",
        "image": "◆ Image Generation Mode"
    }
    console.print(f"\n[bold {theme_config['accent_color']}]{mode_display.get(mode, '◆ Ask')}[/]")
    if mode in ["ask", "semi-agent"]:
        console.print(f"[dim]◆ Commands: /exit /clear /mode /status /commit /push[/]")
        console.print(f"[dim]◆ File paths: Type [bold {theme_config['accent_color']}]/[/dim][dim] to see workspace files (e.g., [/dim][{theme_config['accent_color']}]/gemini_cli.py[/][dim])[/]\n")
        if mode == "semi-agent":
            console.print(f"[dim italic]System Agent Mode: I can read files, suggest modifications, and apply changes to your code.[/]\n")
    elif mode == "image":
        console.print(f"[dim]◆ Commands: /exit /clear /mode[/]")
        console.print(f"[dim]◆ Example: [/dim][{theme_config['text_color']}]Create a beautiful sunset over mountains[/]\n")
    else:
        console.print(f"[dim]◆ Commands: /exit /clear /mode[/]\n")
    
    while True:
        try:
            # Get input with file path autocomplete - Claude-style
            console.print()
        except KeyboardInterrupt:
            console.print(f"\n\n[bold {theme_config['primary_color']}]◆ Goodbye! ◆[/]\n")
            break
        
        try:
            user_input = await get_text_input_async(f"You")
        except (EOFError, KeyboardInterrupt):
            console.print(f"\n\n[bold {theme_config['primary_color']}]◆ Goodbye! ◆[/]\n")
            break
        
        try:
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ('/exit', '/quit', '/q'):
                # Check for uncommitted changes before exiting
                if mode == "semi-agent" and git_preferences['enabled'] and git_preferences['commit_mode'] == 'on_exit':
                    await handle_exit_git_commit(chat)
                
                console.print(f"\n[bold {theme_config['primary_color']}]◆ Goodbye! ◆[/]\n")
                break
            
            elif user_input.lower() == '/mode':
                console.print(f"\n[bold {theme_config['primary_color']}]◆ Returning to mode selection... ◆[/]\n")
                return
                
            elif user_input.lower() == '/clear':
                clear_screen()
                print_banner()
                continue
            
            elif user_input.lower() == '/help':
                console.print()
                console.print(f"[bold {theme_config['primary_color']}]◆ GemCLI Help ◆[/]")
                console.rule(style=theme_config['border_color'])
                console.print()
                
                # Mode capabilities
                console.print(f"[bold {theme_config['secondary_color']}]MODES & CAPABILITIES[/]")
                console.print()
                from rich.table import Table
                table = Table(show_header=True, header_style=f"bold {theme_config['accent_color']}", box=box.SIMPLE)
                table.add_column("Mode", style=theme_config['primary_color'], width=15)
                table.add_column("Ask", justify="center", width=8)
                table.add_column("Read Files", justify="center", width=12)
                table.add_column("Edit Files", justify="center", width=12)
                table.add_column("Search", justify="center", width=10)
                table.add_column("Auto Mode", justify="center", width=10)
                table.add_column("Sys Cmds", justify="center", width=10)
                
                table.add_row("Chat", "✓", "✗", "✗", "✗", "✗", "✗")
                table.add_row("System Agent", "✓", "✓", "✓", "✗", "✗", "✓")
                table.add_row("Agent", "✓", "✓", "✓", "✓", "✓", "✓")
                table.add_row("AutoBot", "✓", "✓", "✓", "✓", "✓", "✓")
                table.add_row("Image Gen", "✓", "✗", "✗", "✗", "✗", "✗")
                
                console.print(table)
                console.print()
                
                # System Commands info for System Agent and Agent modes
                if mode in ["semi-agent", "agent"]:
                    console.print(f"[bold {theme_config['secondary_color']}]SYSTEM COMMANDS[/]")
                    console.print()
                    console.print(f"  [{theme_config['text_color']}]In this mode, Gemini can execute system commands:[/]")
                    console.print(f"  [{theme_config['accent_color']}]•[/] Open/close applications (Chrome, Notepad, etc.)")
                    console.print(f"  [{theme_config['accent_color']}]•[/] Adjust brightness and volume")
                    console.print(f"  [{theme_config['accent_color']}]•[/] Open file explorer")
                    console.print(f"  [{theme_config['accent_color']}]•[/] Control media playback")
                    console.print(f"  [{theme_config['accent_color']}]•[/] System shutdown (when explicitly requested)")
                    console.print()
                    console.print(f"  [dim]Example: 'lower the brightness' or 'open chrome'[/]")
                    console.print()
                
                # Commands
                console.print(f"[bold {theme_config['secondary_color']}]AVAILABLE COMMANDS[/]")
                console.print()
                console.print(f"  [{theme_config['accent_color']}]/help[/]     - Show this help message")
                console.print(f"  [{theme_config['accent_color']}]/exit[/]     - Exit the current mode")
                console.print(f"  [{theme_config['accent_color']}]/quit[/]     - Same as /exit")
                console.print(f"  [{theme_config['accent_color']}]/clear[/]    - Clear the screen")
                console.print(f"  [{theme_config['accent_color']}]/mode[/]     - Switch between modes")
                
                if mode in ["semi-agent", "agent"]:
                    console.print(f"  [{theme_config['accent_color']}]/status[/]   - Show git repository status")
                    console.print(f"  [{theme_config['accent_color']}]/commit[/]   - Commit changes with AI-generated message")
                    console.print(f"  [{theme_config['accent_color']}]/push[/]     - Push commits to remote")
                
                console.print()
                
                # Settings
                console.print(f"[bold {theme_config['secondary_color']}]SETTINGS[/]")
                console.print()
                console.print(f"  [{theme_config['text_color']}]• Theme customization (6 color schemes)[/]")
                console.print(f"  [{theme_config['text_color']}]• Git integration (auto-commit, push)[/]")
                console.print(f"  [{theme_config['text_color']}]• Diff viewer preferences[/]")
                console.print(f"  [{theme_config['text_color']}]• Image generation settings[/]")
                console.print()
                console.print(f"[dim]Access via main menu > Settings[/]")
                console.print()
                console.rule(style=theme_config['border_color'])
                console.print()
                continue
            
            # Git commands
            elif user_input.lower() == '/status':
                console.print()
                git_info = get_git_status()
                
                if not git_info['is_repo']:
                    console.print(f"[{theme_config['warning_color']}]⚠ Not a git repository[/]\n")
                else:
                    console.print(f"[bold {theme_config['primary_color']}]◆ Git Status[/]")
                    console.print(f"[{theme_config['text_color']}]Branch:[/] [{theme_config['accent_color']}]{git_info['branch']}[/]")
                    console.print()
                    
                    if git_info['has_changes']:
                        console.print(git_info['status'])
                    else:
                        console.print(f"[{theme_config['success_color']}]✓ Working tree clean[/]")
                console.print()
                continue
            
            elif user_input.lower() == '/commit':
                console.print()
                git_info = get_git_status()
                
                if not git_info['is_repo']:
                    console.print(f"[{theme_config['warning_color']}]⚠ Not a git repository[/]\n")
                    continue
                
                if not git_info['has_changes']:
                    console.print(f"[{theme_config['warning_color']}]⚠ No changes to commit[/]\n")
                    continue
                
                # Generate commit message using AI
                console.print(f"[bold {theme_config['primary_color']}]◆ Generating commit message...[/]")
                commit_msg = await generate_commit_message(chat, None)
                
                if not commit_msg:
                    console.print(f"[{theme_config['warning_color']}]⚠ Failed to generate commit message[/]\n")
                    continue
                
                console.print()
                console.print(f"[bold {theme_config['secondary_color']}]◆ Suggested commit message:[/]")
                console.print(f"[{theme_config['accent_color']}]{commit_msg}[/]")
                console.print()
                
                # Ask for confirmation
                custom_style = Style([
                    ('pointer', f'fg:{theme_config["accent_color"]} bold'),
                    ('highlighted', f'fg:{theme_config["primary_color"]} bold'),
                ])
                
                confirm = await questionary.select(
                    "Commit with this message?",
                    choices=['◆ Yes, commit', '◆ No, cancel'],
                    pointer="❯",
                    style=custom_style,
                    qmark="",
                    show_selected=False,
                    use_shortcuts=False
                ).ask_async()
                
                if confirm == '◆ Yes, commit':
                    success, output = git_commit(commit_msg)
                    if success:
                        console.print(f"\n[bold {theme_config['success_color']}]✓ Committed successfully[/]")
                        console.print(f"[dim]{output}[/]")
                    else:
                        console.print(f"\n[bold red]✗ Commit failed:[/] {output}")
                else:
                    console.print(f"\n[{theme_config['warning_color']}]⚠ Commit cancelled[/]")
                
                console.print()
                continue
            
            elif user_input.lower() == '/push':
                console.print()
                git_info = get_git_status()
                
                if not git_info['is_repo']:
                    console.print(f"[{theme_config['warning_color']}]⚠ Not a git repository[/]\n")
                    continue
                
                console.print(f"[bold {theme_config['primary_color']}]◆ Pushing to remote...[/]")
                success, output = git_push()
                
                if success:
                    console.print(f"[bold {theme_config['success_color']}]✓ Pushed successfully[/]")
                    console.print(f"[dim]{output}[/]")
                else:
                    console.print(f"\n[bold red]✗ Push failed:[/] {output}")
                
                console.print()
                continue
            
            # Handle file paths
            modified_input = user_input
            referenced_files = []
            if mode in ["ask", "semi-agent"]:
                import re
                path_pattern = r'/([^\s/][^\s]*)'
                paths = re.findall(path_pattern, user_input)
                
                if paths:
                    file_contents = []
                    workspace_root = Path.cwd()
                    for path in paths:
                        try:
                            p = workspace_root / path.replace('/', os.sep)
                            
                            # Check if it's a directory
                            if p.exists() and p.is_dir():
                                # Get all files in the directory (non-recursive)
                                dir_files = [f for f in p.iterdir() if f.is_file()]
                                if dir_files:
                                    for file_path in dir_files:
                                        try:
                                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                                            relative_path = str(file_path.relative_to(workspace_root)).replace(os.sep, '/')
                                            file_contents.append(f"\n--- File: {relative_path} ---\n{content}\n--- End of {relative_path} ---")
                                            # Track referenced files for semi-agent mode
                                            if mode == "semi-agent":
                                                referenced_files.append({'path': relative_path, 'full_path': file_path})
                                        except Exception as e:
                                            console.print(f"[dim]Could not read {file_path.name}: {e}[/]")
                            
                            # Check if it's a file
                            elif p.exists() and p.is_file():
                                content = p.read_text(encoding='utf-8', errors='ignore')
                                file_contents.append(f"\n--- File: {path} ---\n{content}\n--- End of {path} ---")
                                # Track referenced files for semi-agent mode
                                if mode == "semi-agent":
                                    referenced_files.append({'path': path, 'full_path': p})
                        except Exception as e:
                            console.print(f"[{theme_config['warning_color']}]⚠ Could not access {path}: {e}[/]")
                    
                    if file_contents:
                        modified_input = user_input + "\n\n" + "\n".join(file_contents)
            
            # Add semi-agent or agent mode instructions
            if mode == "semi-agent":
                if referenced_files:
                    # Build list of file paths for the prompt
                    file_paths = [ref['path'] for ref in referenced_files]
                    files_list = ', '.join(file_paths)
                    
                    # Detect OS for system commands
                    os_name = "Windows" if os.name == 'nt' else ("macOS" if sys.platform == 'darwin' else "Linux")
                    
                    # Build OS-specific examples for semi-agent with files
                    if os_name == 'Windows':
                        os_examples_with_files = '''- Windows: {"SysPrmpt": "start chrome https://youtube.com", "reply": "Opening YouTube"}
- Windows: {"SysPrmpt1": "start chrome", "SysPrmpt2": "explorer .", "reply": "Opening Chrome and Explorer"}
- Windows: {"SysPrmpt": "powershell -Command (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,30)", "reply": "Lowering brightness"}'''
                    elif os_name == 'macOS':
                        os_examples_with_files = '''- macOS: {"SysPrmpt": "open -a 'Google Chrome' https://youtube.com", "reply": "Opening YouTube"}
- macOS: {"SysPrmpt1": "open -a 'Google Chrome'", "SysPrmpt2": "open .", "reply": "Opening Chrome and Finder"}
- macOS: {"SysPrmpt": "osascript -e 'set volume output volume 30'", "reply": "Setting volume to 30%"}'''
                    else:
                        os_examples_with_files = '''- Linux: {"SysPrmpt": "xdg-open https://youtube.com", "reply": "Opening YouTube"}
- Linux: {"SysPrmpt1": "google-chrome", "SysPrmpt2": "nautilus .", "reply": "Opening Chrome and File Manager"}'''
                    
                    first_file = file_paths[0] if file_paths else "example.py"
                    modified_input = f"""{modified_input}

[STRICT INSTRUCTION - YOU MUST FOLLOW THIS EXACTLY]
You are an AI coding agent running on {os_name}. Respond with a JSON object containing file modifications/creations AND/OR text replies AND/OR system commands.

⚠️ CRITICAL SAFETY RULES:
- NEVER delete files or use delete/rm commands
- NEVER execute destructive system commands
- Only modify files that are specified or clearly needed
- For system commands, only use safe operations (open apps, adjust brightness/volume, etc.)

Format (EXACTLY like this):
```json
{{
  "reply": "your text response if user asked a question (optional)",
  "{first_file}": "complete file content here",
  "new_file.py": "content for new file",
  "SysPrmpt": "system command to execute (optional)"
}}
```

Rules:
- Respond with ONE code block containing ONLY valid JSON
- Use "reply" key ONLY for conversational responses (e.g., answering 'how are you', explanations)
- Use file paths as keys for file operations (e.g., "{first_file}" for existing, "new_file.py" for new)
- Use "SysPrmpt" key for SYSTEM-LEVEL commands
⚠️ CRITICAL: You are on {os_name} - use ONLY {os_name} commands!
  * For multiple commands, use separate keys: "SysPrmpt1", "SysPrmpt2", etc.
  * Windows examples: "start chrome https://url", "explorer .", PowerShell commands
  * macOS examples: "open -a 'Google Chrome' https://url", "open .", osascript commands
  * Linux examples: "xdg-open https://url", "nautilus .", bash commands
  * NEVER mix OS commands - stick to {os_name} syntax!
- Values are COMPLETE file contents as strings for files, text for "reply", or command string for "SysPrmpt"
- Use \\n for newlines in the JSON strings
- You can include "reply", file operations, AND "SysPrmpt" in the same response
- NO explanations before or after the JSON block
- NO additional text outside the code block

Files available: {files_list}

Examples for {os_name}:
{os_examples_with_files}"""
                else:
                    # Detect OS for system commands
                    os_name = "Windows" if os.name == 'nt' else ("macOS" if sys.platform == 'darwin' else "Linux")
                    
                    # Build OS-specific examples
                    if os_name == 'Windows':
                        os_examples = '''- Windows: {"SysPrmpt": "start chrome https://youtube.com", "reply": "Opening YouTube"}
- Windows: {"SysPrmpt1": "start chrome", "SysPrmpt2": "explorer .", "reply": "Opening Chrome and Explorer"}
- Windows: {"SysPrmpt": "powershell -Command (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,30)", "reply": "Lowering brightness"}'''
                    elif os_name == 'macOS':
                        os_examples = '''- macOS: {"SysPrmpt": "open -a 'Google Chrome' https://youtube.com", "reply": "Opening YouTube"}
- macOS: {"SysPrmpt1": "open -a 'Google Chrome'", "SysPrmpt2": "open .", "reply": "Opening Chrome and Finder"}
- macOS: {"SysPrmpt": "osascript -e 'set volume output volume 30'", "reply": "Setting volume to 30%"}'''
                    else:
                        os_examples = '''- Linux: {"SysPrmpt": "xdg-open https://youtube.com", "reply": "Opening YouTube"}
- Linux: {"SysPrmpt1": "google-chrome", "SysPrmpt2": "nautilus .", "reply": "Opening Chrome and File Manager"}'''
                    
                    modified_input = f"""{modified_input}

[STRICT INSTRUCTION - YOU MUST FOLLOW THIS EXACTLY]
You are an AI coding agent running on {os_name}. Respond with a JSON object containing file creations AND/OR text replies AND/OR system commands.

⚠️ CRITICAL SAFETY RULES:
- NEVER delete files or use delete/rm commands
- NEVER execute destructive system commands
- Only create/modify files when clearly requested
- For system commands, only use safe operations (open apps, adjust brightness/volume, etc.)

Format (EXACTLY like this):
```json
{{
  "reply": "your text response if user asked a question (optional)",
  "filename.py": "complete file content here",
  "another_file.py": "another complete file content",
  "SysPrmpt": "system command to execute (optional)"
}}
```

Rules:
- Respond with ONE code block containing ONLY valid JSON
- Use "reply" key ONLY for conversational responses (e.g., answering 'how are you', explanations)
- Use filenames as keys for file operations (e.g., "hello.py", "script.py")
- Use "SysPrmpt" key for SYSTEM-LEVEL commands
⚠️ CRITICAL: You are on {os_name} - use ONLY {os_name} commands!
  * For multiple commands, use separate keys: "SysPrmpt1", "SysPrmpt2", etc.
  * Windows examples: "start chrome https://url", "explorer .", PowerShell commands
  * macOS examples: "open -a 'Google Chrome' https://url", "open .", osascript commands
  * Linux examples: "xdg-open https://url", "nautilus .", bash commands
  * NEVER mix OS commands - stick to {os_name} syntax!
- Values are COMPLETE file contents as strings for files, text for "reply", or command string for "SysPrmpt"
- Use \\n for newlines in the JSON strings
- You can include "reply", file operations, AND "SysPrmpt" in the same response
- NO explanations before or after the JSON block
- NO additional text outside the code block

Examples for {os_name}:
{os_examples}"""
            
            elif mode == "agent":
                # Agent mode: Give full autonomy with search/read/modify capabilities
                # Detect OS for system commands
                os_name = "Windows" if os.name == 'nt' else ("macOS" if sys.platform == 'darwin' else "Linux")
                
                
                # Build OS-specific examples for agent mode
                if os_name == 'Windows':
                    agent_os_examples = '''Windows:
- {"SysPrmpt": "start chrome https://youtube.com", "reply": "Opening YouTube"}
- {"SysPrmpt1": "start chrome", "SysPrmpt2": "explorer .", "reply": "Opening both"}
- {"SysPrmpt": "powershell -Command (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,10)", "reply": "Reducing brightness"}
- Volume: Use NirCmd or PowerShell audio controls'''
                elif os_name == 'macOS':
                    agent_os_examples = '''macOS:
- {"SysPrmpt": "open -a 'Google Chrome' https://youtube.com", "reply": "Opening YouTube"}
- {"SysPrmpt1": "open -a 'Google Chrome'", "SysPrmpt2": "open .", "reply": "Opening both"}
- {"SysPrmpt": "osascript -e 'set volume output volume 30'", "reply": "Setting volume"}
- {"SysPrmpt": "osascript -e 'tell application \"System Events\" to key code 14 using {control down}'", "reply": "Volume down"}'''
                else:
                    agent_os_examples = '''Linux:
- {"SysPrmpt": "xdg-open https://youtube.com", "reply": "Opening YouTube"}
- {"SysPrmpt1": "google-chrome", "SysPrmpt2": "nautilus .", "reply": "Opening both"}
- Volume: Use amixer or pactl commands'''
                
                modified_input = f"""{modified_input}

[STRICT INSTRUCTION - AUTONOMOUS AGENT MODE]
You are an autonomous AI coding agent running on {os_name} with workspace access. You can search files, read them, make modifications, AND execute system commands.

⚠️ CRITICAL SAFETY RULES:
- NEVER delete files or use delete/rm commands
- NEVER execute destructive system commands
- Only modify files when clearly needed for the task
- For system commands, only use safe operations (open apps, adjust brightness/volume, etc.)

Available commands (respond with JSON in code block):

1. SEARCH workspace:
```json
{{{{
  "search": "keyword|pattern|regex",
  "file_pattern": "**/*",
  "reply": "Searching for database functions..."
}}}}
```
⚠️ CRITICAL SEARCH RULES:
- ALWAYS extract keywords from the user's ACTUAL question
- If user says "help bob" → search for "bob", NOT generic "TODO|FIXME"
- If user says "find apples" → search for "apples", NOT "error|bug"
- Use the EXACT entities/names/topics the user mentioned
- Only use generic patterns (TODO, FIXME, error) if user EXPLICITLY asks for them
- file_pattern defaults to "**/*" (searches ALL file types: .py, .txt, .md, .json, etc.)

2. READ specific files:
```json
{{{{
  "read": ["/path/to/file1.py", "/path/to/file2.py"],
  "reply": "Reading database connection files..."
}}}}
```

3. MODIFY/CREATE files:
```json
{{{{
  "reply": "Added error handling to 3 files",
  "/path/to/file1.py": "complete file content",
  "/new_file.py": "new file content"
}}}}
```

4. EXECUTE system commands:
```json
{{{{
  "SysPrmpt": "system command to execute",
  "reply": "Executing your request..."
}}}}
```

System Command Examples for {os_name}:
⚠️ CRITICAL: Use ONLY {os_name} commands!
{agent_os_examples}

Workflow:
- If you need to find files, use "search" command first
- Extract ACTUAL keywords from user's question for search
- If you need file contents, use "read" command
- When ready to modify, provide complete file contents
- For system-level operations (open apps, adjust settings), use "SysPrmpt"
- You can combine commands as needed
- ONLY search/read if you actually need to - don't search if the task is simple

Rules:
- ONE code block with ONLY valid JSON per response
- "reply" key for status updates (optional)
- "SysPrmpt" key for system commands
- NO explanations outside the JSON
- Be efficient - only search/read what you need"""

            
            # Send to Gemini
            console.print()
            
            with console.status(f"[bold {theme_config['primary_color']}]◆ Gemini is thinking...[/]", spinner="dots"):
                response_text, response_images = await send_message(chat, modified_input)
            
            # Semi-agent or Agent mode: Check for file modifications and extract reply
            if mode in ["semi-agent", "agent"]:
                import re
                import json
                
                # Look for JSON code block
                file_modifications = []
                reply_text = None
                workspace_root = Path.cwd()
                
                # Try to find JSON code block
                json_pattern = r'```json\s*\n(.*?)\n```'
                json_match = re.search(json_pattern, response_text, re.DOTALL | re.IGNORECASE)
                
                if json_match:
                    try:
                        json_str = json_match.group(1).strip()
                        response_json = json.loads(json_str)
                        
                        # AGENT MODE: Handle search/read commands in a loop
                        if mode == "agent":
                            # Keep processing commands until we get a final reply or file modifications
                            while "search" in response_json or "read" in response_json:
                                # Handle SEARCH command
                                if "search" in response_json:
                                    # Extract reply for debugging
                                    if "reply" in response_json:
                                        reply_text = response_json.get("reply")
                                        if reply_text:
                                            console.print()
                                            console.print(f"[bold {theme_config['secondary_color']}]◆ Gemini[/]")
                                            console.print()
                                            console.print(f"[dim]{reply_text}[/]")
                                    
                                    search_query = response_json["search"]
                                    file_pattern = response_json.get("file_pattern", "**/*")
                                    
                                    console.print()
                                    console.print(f"[bold {theme_config['accent_color']}]◆ Searching workspace...[/]")
                                    console.print(f"[dim]Query: {search_query}, Pattern: {file_pattern}[/]")
                                    
                                    # Search workspace
                                    search_results = search_workspace(search_query, file_pattern)
                                    
                                    if search_results:
                                        console.print(f"[{theme_config['success_color']}]✓ Found {len(search_results)} file(s)[/]")
                                        console.print()
                                        
                                        # Show results to user
                                        for r in search_results:
                                            console.print(f"  [{theme_config['text_color']}]• {r['path']}[/] [dim]({r['size']}, {r['lines']} lines)[/]")
                                        
                                        # Automatically read all found files
                                        file_paths_list = [r['path'] for r in search_results]
                                        
                                        console.print()
                                        console.print(f"[bold {theme_config['accent_color']}]◆ Reading {len(file_paths_list)} file(s)...[/]")
                                        
                                        # Read files
                                        file_contents_dict = read_workspace_files(file_paths_list)
                                        
                                        # Format contents
                                        context = "File contents:\n\n"
                                        for path, content in file_contents_dict.items():
                                            console.print(f"[dim]✓ Read: {path}[/]")
                                            context += f"--- {path} ---\n{content}\n\n"
                                        
                                        # Send contents directly to Gemini - allow iterative search
                                        follow_up_prompt = f"{context}\n\n[MANDATORY] Respond with JSON in code block.\n\nYou just read the files above. Now decide:\n\n1. Need MORE info? → {{\"search\": \"keyword\"}} to search again\n2. Have ENOUGH info? → {{\"reply\": \"your answer to user\"}}\n3. Need to UPDATE files? → {{\"filename.txt\": \"content\", \"reply\": \"explanation\"}}\n\nExtract keywords from what you learned. Example: If file mentions 'apple', search for 'apple' or 'apples'.\n\nRespond with ONLY JSON:"
                                        
                                        console.print()
                                        with console.status(f"[bold {theme_config['primary_color']}]◆ Gemini is analyzing files...[/]", spinner="dots"):
                                            response_text, response_images = await send_message(chat, follow_up_prompt)
                                        
                                        # Process the final response - loop back for more commands
                                        json_match = re.search(json_pattern, response_text, re.DOTALL | re.IGNORECASE)
                                        if json_match:
                                            json_str = json_match.group(1).strip()
                                            response_json = json.loads(json_str)
                                            
                                            # Loop back to process search/read/modify commands
                                            # The while loop will check if there's another search/read command
                                        else:
                                            console.print(f"[{theme_config['warning_color']}]⚠ No JSON found in response after reading files[/]")
                                            console.print(f"[dim]Full response: {response_text}[/]")
                                            console.print()
                                            break  # Exit if no JSON
                                    else:
                                        console.print(f"[{theme_config['warning_color']}]⚠ No files found matching query[/]")
                                        console.print()
                                        break  # Exit the command loop
                                
                                # Handle READ command
                                elif "read" in response_json:
                                    files_to_read = response_json["read"]
                                    
                                    console.print()
                                    console.print(f"[bold {theme_config['accent_color']}]◆ Reading {len(files_to_read)} file(s)...[/]")
                                    
                                    # Read files
                                    file_contents_dict = read_workspace_files(files_to_read)
                                    
                                    # Format contents
                                    context = "File contents:\n\n"
                                    for path, content in file_contents_dict.items():
                                        console.print(f"[dim]✓ Read: {path}[/]")
                                        context += f"--- {path} ---\n{content}\n\n"
                                    
                                    # Send contents back to Gemini - force JSON response
                                    follow_up_prompt = f"{context}\n\n[MANDATORY] You can ONLY respond with JSON in a code block. NO other text allowed.\n\nJSON Format Rules:\n```json\n{{\n  \"search\": \"keyword\" → Search workspace for this keyword, we return filenames\n  \"reply\": \"text\" → Your text response to user\n  \"filename.txt\": \"content\" → Create or modify this file with content\n}}\n```\n\nWorkflow:\n1. If you need MORE info → send {{\"search\": \"keyword\"}}\n2. We find files → return filenames to you → you can search AGAIN if needed\n3. When you have ALL info → send {{\"reply\": \"final answer\"}} or {{\"filename\": \"content\"}}\n\nRespond NOW with ONLY JSON:"
                                    
                                    console.print()
                                    with console.status(f"[bold {theme_config['primary_color']}]◆ Gemini is deciding next action...[/]", spinner="dots"):
                                        response_text, response_images = await send_message(chat, follow_up_prompt)
                                    
                                    # Process the new response - loop back to check for more commands
                                    json_match = re.search(json_pattern, response_text, re.DOTALL | re.IGNORECASE)
                                    if json_match:
                                        json_str = json_match.group(1).strip()
                                        response_json = json.loads(json_str)
                                        
                                        # Continue the while loop to process any new search/read/modify commands
                                    else:
                                        console.print(f"[{theme_config['warning_color']}]⚠ No JSON after read command[/]")
                                        break  # Exit command loop
                            
                            # If we reach here, no more search/read commands to process
                            if "reply" in response_json:
                                reply_text = response_json.pop("reply")
                        else:
                            # Semi-agent mode - extract reply normally
                            if "reply" in response_json:
                                reply_text = response_json.pop("reply")
                        
                        # Check for system command execution (supports multiple commands)
                        system_commands = []
                        # Check for single SysPrmpt
                        if "SysPrmpt" in response_json:
                            system_commands.append(response_json.pop("SysPrmpt"))
                        # Check for numbered SysPrmpt keys (SysPrmpt1, SysPrmpt2, etc.)
                        i = 1
                        while f"SysPrmpt{i}" in response_json:
                            system_commands.append(response_json.pop(f"SysPrmpt{i}"))
                            i += 1
                        
                        # Process file modifications (works for both semi-agent and agent)
                        for file_path, new_content in response_json.items():
                            # Skip non-file keys
                            if file_path in ["search", "read", "file_pattern"]:
                                continue
                            
                            # Normalize the path (remove leading slash if present)
                            normalized_path = file_path.lstrip('/')
                            
                            # Check if it's an existing referenced file (semi-agent mode)
                            matched = False
                            if mode == "semi-agent":
                                for ref_file in referenced_files:
                                    ref_path = ref_file['path'].lstrip('/')
                                    if ref_path == normalized_path or ref_file['path'] == file_path:
                                        file_modifications.append({
                                            'path': ref_file['path'],
                                            'full_path': ref_file['full_path'],
                                            'new_content': new_content,
                                            'is_new': False
                                        })
                                        matched = True
                                        break
                            
                            # For agent mode or unmatched files, treat as new/existing file
                            if not matched:
                                file_full_path = workspace_root / normalized_path
                                is_new = not file_full_path.exists()
                                file_modifications.append({
                                    'path': normalized_path,
                                    'full_path': file_full_path,
                                    'new_content': new_content,
                                    'is_new': is_new
                                })
                    except json.JSONDecodeError as e:
                        console.print(f"\\n[{theme_config['warning_color']}]⚠ Failed to parse JSON response: {e}[/]")
                
                # Display response - either reply text or full response
                console.print()
                console.print(f"[bold {theme_config['secondary_color']}]◆ Gemini[/]")
                console.print()
                
                if reply_text:
                    # Display extracted reply text
                    console.print(Markdown(reply_text))
                elif not file_modifications:
                    # No reply key and no file modifications - show full response
                    console.print(Markdown(response_text))
                # If only file modifications without reply, skip displaying full response
                
                # Execute system commands if present
                if 'system_commands' in locals() and system_commands:
                    console.print()
                    console.print(f"[bold {theme_config['accent_color']}]◆ Executing System Command(s)[/]")
                    
                    for idx, cmd in enumerate(system_commands, 1):
                        if len(system_commands) > 1:
                            console.print(f"[dim]Command {idx}/{len(system_commands)}: {cmd}[/]")
                        else:
                            console.print(f"[dim]Command: {cmd}[/]")
                        
                        # Execute the command
                        success, output = execute_system_command(cmd)
                        
                        if success:
                            console.print(f"[bold {theme_config['success_color']}]✓ Command {idx} executed successfully[/]" if len(system_commands) > 1 else f"[bold {theme_config['success_color']}]✓ Command executed successfully[/]")
                            if output and output != "Command executed":
                                console.print(f"[dim]{output}[/]")
                        else:
                            console.print(f"[bold red]✗ Command {idx} failed[/]" if len(system_commands) > 1 else f"[bold red]✗ Command failed[/]")
                            console.print(f"[dim]{output}[/]")
                        
                        # Add spacing between multiple commands
                        if len(system_commands) > 1 and idx < len(system_commands):
                            console.print()
                    
                    console.print()
                
                # If modifications were found, show diffs and ask to apply them
                if file_modifications:
                    console.print()
                    console.print(f"[bold {theme_config['accent_color']}]◆ File Modifications Detected[/]")
                    console.print(f"[dim]Found {len(file_modifications)} file(s) to modify:[/]")
                    for mod in file_modifications:
                        status = "NEW" if mod['is_new'] else "MODIFIED"
                        console.print(f"  [{theme_config['primary_color']}]•[/] {mod['path']} [{theme_config['success_color'] if mod['is_new'] else theme_config['accent_color']}]({status})[/]")
                    console.print()
                    
                    # Open VS Code diff editors for all files
                    temp_files = []
                    for mod in file_modifications:
                        tmp_path = open_vscode_diff(
                            mod['full_path'],
                            mod['new_content'],
                            mod['path'],
                            mod['is_new']
                        )
                        if tmp_path:
                            temp_files.append(tmp_path)
                    
                    # Create custom style for confirmation
                    custom_style = Style([
                        ('pointer', f'fg:{theme_config["accent_color"]} bold'),
                        ('highlighted', f'fg:{theme_config["primary_color"]} bold'),
                        ('question', f'fg:{theme_config["secondary_color"]} bold'),
                        ('instruction', 'fg:#555555'),
                    ])
                    
                    apply_changes = await questionary.select(
                        "Apply these changes to the files?",
                        choices=["◆ Yes, apply changes", "◆ No, skip"],
                        pointer="❯",
                        style=custom_style,
                        qmark="",
                        instruction="(Use arrow keys)",
                        show_selected=False,
                        use_shortcuts=False
                    ).ask_async()
                    
                    # Clean up temp files
                    for tmp_file in temp_files:
                        try:
                            os.unlink(tmp_file)
                        except:
                            pass
                    
                    if apply_changes == "◆ Yes, apply changes":
                        modified_files = []
                        for mod in file_modifications:
                            try:
                                # Create parent directories if needed for new files
                                if mod['is_new']:
                                    mod['full_path'].parent.mkdir(parents=True, exist_ok=True)
                                
                                # Write new content
                                mod['full_path'].write_text(mod['new_content'], encoding='utf-8')
                                
                                action = "Created" if mod['is_new'] else "Modified"
                                console.print(f"[bold {theme_config['success_color']}]✓ {action}: {mod['path']}[/]")
                                modified_files.append(mod['path'])
                            except Exception as e:
                                console.print(f"[bold red]✗[/] Failed to {'create' if mod['is_new'] else 'modify'} {mod['path']}: {e}")
                        console.print()
                        
                        # Offer to commit changes based on preferences
                        if git_preferences['enabled'] and git_preferences['commit_mode'] == 'immediate':
                            git_info = get_git_status()
                            if git_info['is_repo'] and git_info['has_changes']:
                                console.print(f"[bold {theme_config['primary_color']}]◆ Would you like to commit these changes?[/]\n")
                                
                                custom_style = Style([
                                    ('pointer', f'fg:{theme_config["accent_color"]} bold'),
                                    ('highlighted', f'fg:{theme_config["primary_color"]} bold'),
                                ])
                                
                                commit_choice = await questionary.select(
                                    "",
                                    choices=['◆ Yes, generate commit message', '◆ No, skip'],
                                    pointer="❯",
                                    style=custom_style,
                                    qmark="",
                                    show_selected=False,
                                    use_shortcuts=False
                                ).ask_async()
                                
                                if commit_choice == '◆ Yes, generate commit message':
                                    console.print()
                                    console.print(f"[bold {theme_config['primary_color']}]◆ Generating commit message...[/]")
                                    commit_msg = await generate_commit_message(chat, modified_files)
                                    
                                    if commit_msg:
                                        console.print()
                                        console.print(f"[bold {theme_config['secondary_color']}]◆ Suggested commit message:[/]")
                                        console.print(f"[{theme_config['accent_color']}]{commit_msg}[/]")
                                        console.print()
                                        
                                        confirm = await questionary.select(
                                            "Commit with this message?",
                                            choices=['◆ Yes, commit', '◆ No, cancel'],
                                            pointer="❯",
                                            style=custom_style,
                                            qmark="",
                                            show_selected=False,
                                            use_shortcuts=False
                                        ).ask_async()
                                        
                                        if confirm == '◆ Yes, commit':
                                            success, output = git_commit(commit_msg, modified_files)
                                            if success:
                                                console.print(f"\n[bold {theme_config['success_color']}]✓ Committed successfully[/]")
                                                console.print(f"[dim]{output}[/]")
                                                
                                                # Auto-push if enabled
                                                if git_preferences['auto_push']:
                                                    console.print(f"[bold {theme_config['primary_color']}]◆ Pushing to remote...[/]")
                                                    push_success, push_output = git_push()
                                                    if push_success:
                                                        console.print(f"[bold {theme_config['success_color']}]✓ Pushed successfully[/]")
                                                    else:
                                                        console.print(f"[bold red]✗ Push failed:[/] {push_output}")
                                                console.print()
                                            else:
                                                console.print(f"\n[bold red]✗ Commit failed:[/] {output}\n")
                                        else:
                                            console.print(f"\n[{theme_config['warning_color']}]⚠ Commit cancelled[/]\n")
                                    else:
                                        console.print(f"\n[{theme_config['warning_color']}]⚠ Failed to generate commit message[/]\n")
                    else:
                        console.print(f"[{theme_config['warning_color']}]⚠ Changes not applied[/]\n")
            else:
                # Not in semi-agent mode - display response normally
                console.print()
                console.print(f"[bold {theme_config['secondary_color']}]◆ Gemini[/]")
                console.print()
                console.print(Markdown(response_text))
            
            # Display images if any
            if response_images:
                images_dir = image_settings['save_path']
                images_dir.mkdir(exist_ok=True)
                
                for idx, img_data in enumerate(response_images, 1):
                    try:
                        # Generate unique filename
                        import time
                        img_filename = f'image_{int(time.time())}_{idx}.png'
                        img_path = images_dir / img_filename
                        
                        # Download from URL with cookies (this method works)
                        if hasattr(img_data, 'url'):
                            import requests
                            url = img_data.url
                            cookies = img_data.cookies if hasattr(img_data, 'cookies') else {}
                            
                            resp = requests.get(url, cookies=cookies, stream=True)
                            resp.raise_for_status()
                            
                            img_path.write_bytes(resp.content)
                            img_abs_path = img_path.absolute()
                            
                            # Open image in VS Code/IDE viewer
                            console.print(f"[{theme_config['accent_color']}]✓ Saved:[/] {img_abs_path}\n")
                            webbrowser.open(str(img_abs_path))
                        
                    except Exception as e:
                        console.print(f"[red]Failed to process image {idx}: {e}[/]\n")
            
            console.print()  # Just add some spacing
        
        except KeyboardInterrupt:
            # User pressed Ctrl+C in the main loop - handle git commits for semi-agent/agent
            if mode in ["semi-agent", "agent"] and git_preferences['enabled'] and git_preferences['commit_mode'] == 'on_exit':
                await handle_exit_git_commit(chat)
            console.print(f"\n\n[bold {theme_config['primary_color']}]◆ Goodbye! ◆[/]\n")
            break
            
        except Exception as e:
            # Catch any other errors but don't exit
            import traceback
            console.print(f"\n[{theme_config['warning_color']}]⚠ Unexpected Error: {e}[/]")
            console.print(f"[dim]Traceback:\n{traceback.format_exc()}[/]")
            continue


async def customize_theme():
    """Allow user to customize theme colors."""
    clear_screen()
    print_banner()
    
    console.print(f"\n[bold {theme_config['primary_color']}]Theme Customization[/]")
    console.rule(style=theme_config['border_color'])
    
    # Vibrant color options
    colors = [
        ('#FFFFFF', '◆ White (Default)'),
        ('#00FFD4', '◆ Cyan/Turquoise'),
        ('#FF6B9D', '◆ Vibrant Pink'),
        ('#FFD700', '◆ Gold'),
        ('#00FF88', '◆ Neon Green'),
        ('#9D4EDD', '◆ Purple'),
        ('#FF006E', '◆ Hot Pink')
    ]
    
    console.print()
    console.print(f"[#FFFFFF]◆ White[/]  [#00FFD4]◆ Cyan[/]  [#FF6B9D]◆ Pink[/]  [#FFD700]◆ Gold[/]  [#00FF88]◆ Green[/]  [#9D4EDD]◆ Purple[/]  [#FF006E]◆ Hot Pink[/]")
    console.print()
    
    # Create custom style
    custom_style = Style([
        ('pointer', f'fg:{theme_config["accent_color"]} bold'),
        ('highlighted', f'fg:{theme_config["primary_color"]} bold'),
        ('question', f'fg:{theme_config["secondary_color"]} bold'),
        ('instruction', 'fg:#555555'),  # Dim gray for instruction text
    ])
    
    choice_list = [name for _, name in colors]
    
    selected_name = await questionary.select(
        "Select Theme Color:",
        choices=choice_list,
        pointer="❯",
        style=custom_style,
        qmark="",
        instruction="(Use arrow keys)",
        show_selected=False,
        use_shortcuts=False
    ).ask_async()
    
    if selected_name:
        for color_code, color_name in colors:
            if color_name == selected_name:
                theme_config['primary_color'] = color_code
                theme_config['accent_color'] = color_code
                break


# =============================================================================
# Main
# =============================================================================

async def main():
    """Main entry point."""
    
    print_banner()
    
    # Create custom style with vibrant colors
    custom_style = Style([
        ('pointer', f'fg:{theme_config["accent_color"]} bold'),
        ('highlighted', f'fg:{theme_config["primary_color"]} bold'),
        ('question', f'fg:{theme_config["secondary_color"]} bold'),
        ('selected', f'fg:{theme_config["accent_color"]} bold'),
        ('instruction', 'fg:#555555'),  # Dim gray for instruction text
    ])
    
    # Initial menu with diamond indicators
    console.print()
    choice = await questionary.select(
        "",
        choices=["◆ Connect to Gemini", "◆ Customize Theme", "◆ Settings", "◆ Exit"],
        pointer="❯",
        style=custom_style,
        qmark="",
        instruction="Choose an option (Use arrow keys)",
        show_selected=False,
        use_shortcuts=False
    ).ask_async()
    
    if choice == "◆ Exit":
        console.print(f"\n[bold {theme_config['primary_color']}]◆ Goodbye! ◆[/]\n")
        return
    elif choice == "◆ Customize Theme":
        await customize_theme()
        # Restart from beginning with updated theme
        await main()
        return
    elif choice == "◆ Settings":
        await settings_menu()
        # Restart from beginning
        await main()
        return
    
    # Safety message after choosing to connect
    clear_screen()
    print_banner()
    
    # Display big safety message with ASCII art and gradient
    safety_lines = [
        "███████╗ █████╗ ███████╗███████╗",
        "██╔════╝██╔══██╗██╔════╝██╔════╝",
        "███████╗███████║█████╗  █████╗  ",
        "╚════██║██╔══██║██╔══╝  ██╔══╝  ",
        "███████║██║  ██║██║     ███████╗",
        "╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝"
    ]
    
    # Gradient colors from white to black
    safety_gradient = ['#FFFFFF', '#DDDDDD', '#BBBBBB', '#999999', '#777777', '#555555']
    
    console.print()
    for i, line in enumerate(safety_lines):
        console.print(line, style=f"bold {safety_gradient[i]}", justify="center")
    
    console.print()
    from rich.text import Text
    line1 = Text("This is a CLIENT-SIDE application with NO SERVER.", style=theme_config['text_color'])
    line2 = Text("Your data stays on YOUR machine. 100% Private & Secure.", style=theme_config['text_color'])
    console.print(line1, justify="center")
    console.print(line2, justify="center")
    console.print()
    
    # Check for saved cookies
    saved_psid, saved_psidts = load_cookies()
    
    if saved_psid:
        console.print(f"\n[bold {theme_config['primary_color']}]Found saved cookies[/]", justify="center")
        console.print()
        
        use_saved = await questionary.select(
            "Use saved cookies?",
            choices=["◆ Yes", "◆ No"],
            pointer="❯",
            style=custom_style,
            qmark="",
            instruction="(Use arrow keys)",
            show_selected=False,
            use_shortcuts=False
        ).ask_async()
        
        if use_saved == "◆ Yes":
            psid, psidts = saved_psid, saved_psidts
            console.print(f"\n[bold {theme_config['success_color']}]✓ Using saved cookies[/]\n")
        else:
            psid, psidts = get_cookies()
            if psid:
                save_cookies(psid, psidts)
    else:
        psid, psidts = get_cookies()
        if psid:
            save_cookies(psid, psidts)
    
    if not psid:
        return
    
    # Initialize client
    client = await initialize_client(psid, psidts)
    
    if not client:
        console.print(f"\n[bold red]Failed to connect to Gemini[/]")
        return
    
    # Mode selection loop
    while True:
        clear_screen()
        print_banner()
        
        console.print()
        mode_choice = await questionary.select(
            "Select mode:",
            choices=["◆ Ask", "◆ System Agent", "◆ Agent (Autonomous)", "◆ AutoBot (Full Auto)", "◆ Generate Images", "◆ Exit"],
            pointer="❯",
            style=custom_style,
            qmark="",
            instruction="Choose a mode (Use arrow keys)",
            show_selected=False,
            use_shortcuts=False
        ).ask_async()
        
        if mode_choice == "◆ Exit":
            console.print(f"\n[bold {theme_config['primary_color']}]◆ Goodbye! ◆[/]\n")
            break
        
        # Handle AutoBot mode separately (it has its own loop)
        if mode_choice == "◆ AutoBot (Full Auto)":
            await autobot_loop(client)
            continue
        
        # Map choice to mode
        mode_map = {
            "◆ Ask": "ask",
            "◆ System Agent": "semi-agent",
            "◆ Agent (Autonomous)": "agent",
            "◆ Generate Images": "image"
        }
        mode = mode_map.get(mode_choice, "ask")
        
        # Start chat in selected mode
        clear_screen()
        print_banner()
        await chat_loop(client, mode)
    
    try:
        await client.close()
    except:
        pass


def run_cli():
    """Entry point for the CLI tool."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print(f"\n[bold {theme_config['primary_color']}]◆ Goodbye! ◆[/]")
        sys.exit(0)


if __name__ == "__main__":
    run_cli()
