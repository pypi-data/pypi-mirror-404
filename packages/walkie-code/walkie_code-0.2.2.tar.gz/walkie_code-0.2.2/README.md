# WalkieCode Desktop Client

WebSocket client that connects Claude CLI to voice commands from iOS app.

## Installation

```bash
pip install walkie_code
```

## Quick Start

```bash
# Run desktop client (sessions auto-resume, permissions auto-accepted by default)
walkie_code YOUR_DEVICE_TOKEN

# Start fresh conversation (don't resume previous session)
walkie_code YOUR_DEVICE_TOKEN --no-resume

# View help
walkie_code --help

# Configure device token
walkie_code config
```

## Configuration

Settings are stored in `.walkiecode_config.json` in your working directory:

```json
{
  "deviceToken": "your-device-token",
  "claude": {
    "skip_permissions": true,
    "timeout": 300,
    "model": "claude-sonnet-4-20250514",
    "permission_mode": "acceptEdits"
  }
}
```

**Claude Settings:**
- `skip_permissions`: Auto-accept file edits (default: `true`)
- `timeout`: Command timeout in seconds (default: `300`)
- `model`: Claude model to use (default: `"claude-sonnet-4-20250514"`)
- `permission_mode`: Permission mode for Claude CLI (default: `"acceptEdits"`)

## Connection Management

- ✅ Only one connection per working directory is supported
- ✅ If you try to open a second connection with the same token, it will be rejected
- ✅ Close the existing connection before starting a new one
- ✅ Connection lock file: `.walkiecode.lock` (auto-created/removed)
