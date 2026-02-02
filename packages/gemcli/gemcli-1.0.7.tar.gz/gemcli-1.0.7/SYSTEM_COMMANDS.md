# System Command Feature

## Overview
The CLI tool supports executing system-level commands through the AI in **System Agent** and **Agent** modes. Gemini can control your system to:
- **Open/Close applications** (Chrome, Notepad, Calculator, etc.)
- **Adjust system settings** (brightness, volume)
- **Launch file explorer** and navigate directories
- **Execute terminal commands**
- **Shut down or restart** the system (when requested)

When you ask Gemini to perform system operations, it responds with a special `SysPrmpt` key that triggers safe command execution.

## How It Works

### 1. User Request
You can ask Gemini to perform system operations naturally:
- "Lower the brightness"
- "Increase volume"
- "Open Chrome"
- "Open File Explorer"
- "Launch Notepad"
- "Start Calculator"
- "Turn off the system"
- "Play music"

### 2. AI Response
Gemini will recognize these as system commands and respond with a JSON object containing the `SysPrmpt` key:

```json
{
  "SysPrmpt": "start chrome",
  "reply": "Opening Chrome browser for you"
}
```

### 3. Command Execution
The CLI tool automatically:
1. Detects the `SysPrmpt` key in the response
2. Extracts the command
3. Executes it in the system terminal
4. Displays the result to you

## Supported Commands

### Windows Examples

#### Open Applications
```json
{"SysPrmpt": "start chrome"}
{"SysPrmpt": "start notepad"}
{"SysPrmpt": "start calc"}
{"SysPrmpt": "start firefox"}
```

#### Multiple Commands (Chaining)
```json
{"SysPrmpt": "start chrome; explorer ."}
{"SysPrmpt": "start notepad; start calc"}
```
**Note:** Use semicolon (`;`) to chain commands in PowerShell. The system automatically converts `&&` to `;` if needed.

#### Open File Explorer
```json
{"SysPrmpt": "explorer ."}
{"SysPrmpt": "explorer C:\\Users"}
```

#### Adjust Brightness
```json
{
  "SysPrmpt": "powershell -Command '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,30)'",
  "reply": "Setting brightness to 30%"
}
```

#### Volume Control
```json
{"SysPrmpt": "powershell -Command '(New-Object -ComObject WScript.Shell).SendKeys([char]174)'"}
```

#### System Information
```json
{"SysPrmpt": "systeminfo | findstr /C:\"OS Name\" /C:\"OS Version\""}
```

### Mac/Linux Examples

#### Open Applications
```json
{"SysPrmpt": "open -a 'Google Chrome'"}
{"SysPrmpt": "open -a 'TextEdit'"}
{"SysPrmpt": "open -a 'Calculator'"}
```

#### Open File Browser
```json
{"SysPrmpt": "open ."}
{"SysPrmpt": "open ~/Documents"}
```

#### Adjust Brightness (Mac)
```json
{"SysPrmpt": "brightness 0.5"}
```

## Usage Examples

### In System Agent Mode

```
You: lower the brightness

Gemini: Setting brightness to 30%
◆ Executing System Command
Command: powershell -Command '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,30)'

✓ Command executed successfully
```

### In Agent Mode

```
You: open chrome and file explorer

Gemini: Opening Chrome browser and File Explorer for you
◆ Executing System Command
Command: start chrome && explorer .

✓ Command executed successfully
```

### Combined with File Operations

```
You: create a hello.py file and open notepad

Gemini:
{
  "hello.py": "print('Hello, World!')\n",
  "SysPrmpt": "start notepad",
  "reply": "Created hello.py and opening Notepad"
}

◆ File Modifications Detected
Found 1 file(s) to modify:
  • hello.py (NEW)

◆ Executing System Command
Command: start notepad

✓ Command executed successfully
```

## Safety Features

### Timeout Protection
- Commands automatically timeout after 30 seconds
- Prevents hanging or infinite processes

### Error Handling
- Graceful error messages if command fails
- Displays error output for debugging

### Sandboxing
- Commands run in a subprocess with limited scope
- No direct system access beyond terminal commands

## Technical Details

### Command Execution Function
```python
def execute_system_command(command: str) -> Tuple[bool, str]:
    """
    Execute system commands like opening applications, adjusting settings, etc.
    Returns (success: bool, output: str)
    """
    # Implementation details in gemini_cli.py
```

### JSON Response Format
```json
{
  "reply": "Optional conversational response",
  "filename.py": "Optional file content",
  "SysPrmpt": "system command to execute"
}
```

### Processing Order
1. Parse JSON response
2. Extract `reply`, `SysPrmpt`, and file operations
3. Display reply text
4. Execute system command (if present)
5. Apply file modifications (if present)

## Best Practices

### For Users
1. Be specific about what application or action you want
2. Review the command before execution in the displayed output
3. Test commands in a safe environment first

### For AI Responses
1. Always include a `reply` key to explain the action
2. Use platform-specific commands when possible
3. Keep commands simple and direct
4. Avoid complex shell scripts in a single command

## Limitations

1. **Platform Dependent**: Commands must be valid for the user's OS
2. **Timeout**: Commands must complete within 30 seconds
3. **No Interactive Commands**: Commands that require user input during execution won't work
4. **Security**: Only available in System Agent and Agent modes, not in basic Ask mode

## Troubleshooting

### Command Not Executing
- Check if the command is valid for your OS
- Ensure the application is installed
- Verify the command syntax

### Permission Errors
- Some system commands may require administrator privileges
- Run the CLI tool with elevated permissions if needed

### Timeout Issues
- Long-running commands will timeout after 30 seconds
- Use background commands for services or servers

## Future Enhancements

Potential future additions:
- Interactive command confirmation
- Command history and favorites
- Platform detection and automatic command translation
- Scheduled command execution
- Command macros and shortcuts
