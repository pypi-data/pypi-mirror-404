"""Claude session using official claude CLI binary"""

import os
import json
import subprocess
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime
from config import load_config, get_claude_settings


# Session storage location
SESSION_FILE = Path.home() / ".vibevoice_session.json"


class ClaudeSession:
    """Claude session wrapper using official claude CLI"""

    def __init__(
        self,
        project_path: Optional[str] = None,
        resume: bool = True,
        skip_permissions: Optional[bool] = None
    ):
        """
        Initialize Claude session

        Args:
            project_path: Project directory for context
            resume: Resume previous session if available (default: True)
            skip_permissions: Skip permission checks (None = load from config)
        """
        # Project path
        if project_path:
            self.project_path = Path(project_path)
        elif os.environ.get('PROJECT_PATH'):
            self.project_path = Path(os.environ['PROJECT_PATH'])
        else:
            self.project_path = Path.cwd()

        print(f'📁 Project context: {self.project_path}')

        # Load skip_permissions from config if not explicitly provided
        if skip_permissions is None:
            config = load_config()
            claude_settings = get_claude_settings(config)
            skip_permissions = claude_settings.get('skip_permissions', True)
            print(f'⚙️  Loaded skip_permissions from config: {skip_permissions}')

        # Session ID for conversation continuity
        self.session_id = None
        self.skip_permissions = skip_permissions

        # Conversation history for WebSocket context (optional)
        self.conversation_history = []

        # Resume previous session if requested
        if resume:
            self._load_session()

        # Generate new session ID if not loaded
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
            print(f'🆔 New session: {self.session_id[:8]}...')

        # Verify claude CLI is available
        if not self._check_claude_cli():
            print('⚠️  claude CLI not found!')
            print('   Install with: npm install -g @anthropic-ai/claude-sdk')
            print('   Or download from: https://docs.anthropic.com/en/docs/developer-tools/claude-cli')
            self.client = None
        else:
            self.client = True
            print('✅ claude CLI initialized')
            if self.skip_permissions:
                print('✅ Permissions: BYPASSED - Claude can edit files & run commands in any folder')
            else:
                print('⚠️  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
                print('⚠️  CLAUDE WILL ASK FOR PERMISSION TO EDIT FILES')
                print('⚠️  To auto-accept, restart with:')
                print('⚠️  vibe_voice_desktop --dangerously-skip-permissions')
                print('⚠️  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

    def _check_claude_cli(self) -> bool:
        """Check if claude CLI is available"""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _extract_summary(self, response: str) -> Optional[str]:
        """Extract SUMMARY section from response if present"""
        if "SUMMARY:" not in response:
            return None

        # Find SUMMARY: marker and extract everything after it
        summary_start = response.find("SUMMARY:")
        if summary_start == -1:
            return None

        # Extract from SUMMARY: to end
        summary_text = response[summary_start + len("SUMMARY:"):].strip()

        # If summary is empty or too short, return None
        if len(summary_text) < 10:
            return None

        return summary_text

    def _save_session(self):
        """Save conversation history to disk"""
        try:
            session_data = {
                "session_id": self.session_id,
                "project_path": str(self.project_path),
                "conversation_history": self.conversation_history
            }
            with open(SESSION_FILE, 'w') as f:
                json.dump(session_data, f, indent=2)
            print(f'💾 Session saved ({len(self.conversation_history)} messages)')
        except Exception as e:
            print(f'⚠️  Failed to save session: {e}')

    def _load_session(self):
        """Load conversation history from disk"""
        if not SESSION_FILE.exists():
            print('📝 No previous session found, starting fresh')
            return

        try:
            with open(SESSION_FILE, 'r') as f:
                session_data = json.load(f)

            self.session_id = session_data.get('session_id')
            self.conversation_history = session_data.get('conversation_history', [])
            print(f'✅ Resumed session {self.session_id[:8] if self.session_id else "unknown"}... with {len(self.conversation_history)} messages')
        except Exception as e:
            print(f'⚠️  Failed to load session: {e}')
            self.conversation_history = []

    def send_message(self, message: str, timeout: int = 300) -> str:
        """
        Send a message to Claude via CLI and get response

        Args:
            message: User message
            timeout: Timeout in seconds

        Returns:
            Claude's response
        """
        if not self.client:
            error = "Error: claude CLI not available. Please install it first."
            return {"full_response": error, "summary": None, "has_summary": False}

        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": message
            })

            # Log user message clearly with timestamp
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f'\n┌─────────────────────────────────────────────────')
            print(f'│ 👤 USER ({timestamp}): {message[:80]}{"..." if len(message) > 80 else ""}')
            print(f'├─────────────────────────────────────────────────')
            print(f'│ 🔄 Session: {self.session_id[:8]}...')
            print(f'│ 💬 History: {len(self.conversation_history)} messages')
            print(f'│ 🚩 skip_permissions flag: {self.skip_permissions}')

            # Build message with conversation context if history exists
            # Include last few exchanges so Claude understands context
            context_message = message
            if len(self.conversation_history) > 1:
                # Include last 3 exchanges (6 messages max) for context
                recent_history = self.conversation_history[:-1][-6:]
                if recent_history:
                    context_parts = ["Previous conversation context:"]
                    for msg in recent_history:
                        role = "User" if msg["role"] == "user" else "Assistant"
                        content = msg["content"][:200]  # Truncate long messages
                        context_parts.append(f"{role}: {content}")
                    context_parts.append(f"\nCurrent request: {message}")
                    context_message = "\n".join(context_parts)
                    print(f'│ 📚 Including {len(recent_history)} previous messages for context')

            # Add instruction for long responses to include summary
            full_message = f"""{context_message}

IMPORTANT: If your response involves multiple file changes, refactoring, or is longer than a few sentences,
please include a SUMMARY section at the end in this exact format:

SUMMARY:
[Brief 2-3 sentence summary of what was done]

This summary will be sent to mobile clients while the full response stays in the terminal."""

            # Build command (no --session-id due to subprocess conflicts)
            # Session continuity maintained by passing conversation history in prompt
            cmd = ["claude", "-p", full_message]

            # Add permission mode if requested
            if self.skip_permissions:
                # Use bypassPermissions mode which skips ALL permission checks
                # This allows Claude to run commands and edit files immediately in any folder
                cmd.extend([
                    "--permission-mode", "bypassPermissions"
                ])
                print(f'│ ⚠️  Permissions: BYPASSED (can edit files & run commands)')
            else:
                print(f'│ 🔒 Permissions: WILL ASK (run with --dangerously-skip-permissions)')

            print(f'│ 📝 Command: {" ".join(cmd)}')
            print(f'└─────────────────────────────────────────────────\n')

            # Call claude CLI with the message
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error"
                print(f'\n┌─────────────────────────────────────────────────')
                print(f'│ ❌ ERROR: {error_msg[:80]}')
                print(f'└─────────────────────────────────────────────────\n')
                error = f"Error: {error_msg}"
                return {"full_response": error, "summary": None, "has_summary": False}

            response = result.stdout.strip()

            # Extract summary if present
            summary = self._extract_summary(response)

            # Log Claude's FULL response with timestamp
            response_time = datetime.now().strftime('%H:%M:%S')
            print(f'\n┌─────────────────────────────────────────────────')
            print(f'│ 🤖 CLAUDE ({response_time}):')
            print(f'├─────────────────────────────────────────────────')
            # Print full response (not truncated)
            for line in response.split('\n'):
                print(f'│ {line}')
            print(f'├─────────────────────────────────────────────────')
            print(f'│ 📊 Response length: {len(response)} chars')
            if summary:
                print(f'│ 📱 Mobile summary: {summary[:100]}{"..." if len(summary) > 100 else ""}')
            print(f'└─────────────────────────────────────────────────\n')

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })

            # Auto-save session
            self._save_session()

            # Return dict with full response and optional summary
            return {
                "full_response": response,
                "summary": summary,
                "has_summary": summary is not None
            }

        except subprocess.TimeoutExpired:
            error_msg = f"Claude CLI timed out after {timeout} seconds"
            print(f'[DEBUG] {error_msg}')
            error = f"Error: {error_msg}"
            return {"full_response": error, "summary": None, "has_summary": False}

        except Exception as e:
            error_msg = f"Claude CLI error: {str(e)}"
            print(f'[DEBUG] {error_msg}')
            error = f"Error: {error_msg}"
            return {"full_response": error, "summary": None, "has_summary": False}

    def reset_conversation(self):
        """Reset conversation history and delete saved session"""
        msg_count = len(self.conversation_history)
        self.conversation_history = []

        # Delete saved session file
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()

        print(f'🔄 Conversation reset ({msg_count} messages cleared)')
        return "Conversation history cleared. Starting fresh."

    def close(self):
        """Save and close session"""
        msg_count = len(self.conversation_history)
        if msg_count > 0:
            self._save_session()
        print(f'👋 Claude session closed ({msg_count} messages)')
