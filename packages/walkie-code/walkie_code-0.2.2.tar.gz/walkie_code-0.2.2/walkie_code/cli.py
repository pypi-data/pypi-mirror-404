#!/usr/bin/env python3
"""
WalkieCode Desktop Client - Main CLI

Usage:
export ANTHROPIC_API_KEY=your_key_here
walkie_code                  # Uses config or prompts for token
walkie_code config           # Prompt for and save device token
walkie_code [DEVICE_TOKEN]   # Uses provided token

Config file: .walkiecode_config.json (in working directory)
"""

__version__ = "0.2.1"

import sys
import time
import argparse
from .config import (load_config, save_config, get_device_token, DEFAULT_ENDPOINT,
                     check_existing_connection, create_connection_lock, remove_connection_lock)
from .websocket_client import WebSocketClient
from .session import ClaudeSession


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='WalkieCode Desktop Client')
    parser.add_argument('command', nargs='?',
                       help='Command: "config" to set device token, or device token to use')
    parser.add_argument('-r', '--resume', action='store_true', default=True,
                       help='Resume previous session (default: True)')
    parser.add_argument('--no-resume', action='store_false', dest='resume',
                       help='Start fresh conversation without resuming')
    parser.add_argument('--dangerously-skip-permissions', action='store_true',
                       help='Skip permission checks (use with caution)')
    return parser.parse_args()


def handle_config_command():
    """Handle config command to set device token"""
    print("=" * 60)
    print("WalkieCode Desktop Client - Configuration")
    print("=" * 60)
    print()
    print("Enter device token from iOS app (tap the key 🔑 icon):")
    new_token = input("Device Token: ").strip()
    print()
    
    if new_token:
        config = load_config()
        config['deviceToken'] = new_token
        save_config(config)
        print(f"✓ Device token saved: {new_token}")
    else:
        print("Error: No token provided")
    
    sys.exit(0)


def get_connection_params(args):
    """Get device token and endpoint from args or config"""
    config = load_config()
    
    # Handle "config" command
    if args.command == 'config':
        handle_config_command()
    
    # Get device token
    if args.command:
        device_token = args.command
        # Save token to config if provided via CLI
        if device_token:
            config['deviceToken'] = device_token
            save_config(config, silent=True)
    else:
        device_token = get_device_token(config)
    
    if not device_token:
        print("Error: Device token is required")
        print("Run 'walkie_code config' to set up your device token")
        sys.exit(1)
    
    endpoint = DEFAULT_ENDPOINT
    return device_token, endpoint


def main():
    """Main application loop"""
    args = parse_arguments()
    device_token, endpoint = get_connection_params(args)

    # Check for existing connection with same token
    existing_token = check_existing_connection()
    if existing_token:
        print("Error: Another connection is already active")
        print("Multiple connections are not supported")
        print("Please close the existing connection first")
        sys.exit(1)

    # Create connection lock
    if not create_connection_lock(device_token):
        print("Error: Could not create connection lock")
        sys.exit(1)

    try:
        print(f"Device Token: {device_token}")
        print(f"WebSocket Endpoint: {endpoint}")
        print()

        # Initialize Claude session
        # If --dangerously-skip-permissions is provided, use True
        # Otherwise, pass None to load from config (defaults to True)
        claude_session = ClaudeSession(
            resume=args.resume,
            skip_permissions=True if args.dangerously_skip_permissions else None
        )

        if not claude_session.client:
            print("\n❌ Cannot start without claude CLI. Please install it first.")
            print("   npm install -g @anthropic-ai/claude-sdk")
            sys.exit(1)
        
        # Initialize WebSocket client
        ws_client = WebSocketClient(endpoint, device_token)

        # Track pending response to retry after reconnection
        pending_response = None

        # Main connection loop with auto-reconnect
        while True:
            try:
                # Connect to WebSocket
                ws_client.connect()

                # Send pending response if we have one from before disconnection
                if pending_response:
                    try:
                        print(f'📤 Retrying pending response ({len(pending_response)} chars)...')
                        ws_client.send_message(pending_response)
                        print('✅ Pending response sent successfully')
                        pending_response = None
                    except Exception as e:
                        print(f'⚠️ Failed to send pending response, will retry: {e}')

                print('Listening for incoming messages from frontend...')

                # Message processing loop
                while True:
                    try:
                        # Receive message
                        data = ws_client.receive_message()
                        
                        # Skip empty messages (ping/pong, keepalive)
                        if data is None:
                            continue
                        
                        # Process frontend message
                        if data.get('type') == 'frontendMessage':
                            message = data.get('message', '')
                            print(f'Frontend message: {message}')

                            # Send "AI is working" notification
                            try:
                                ws_client.send_notification('🤖 AI is working on your request...')
                                print('📤 Sent "AI is working" system notification')
                            except Exception as e:
                                print(f'Warning: Failed to send notification: {e}')

                            # Process message with Claude (with tool use support)
                            result = claude_session.send_message(message)

                            # Extract appropriate response for mobile client
                            # Use summary if available, otherwise full response
                            if result["has_summary"]:
                                mobile_response = result["summary"]
                                print(f'📱 Sending SUMMARY to mobile ({len(mobile_response)} chars)')
                                print(f'💻 Full response ({len(result["full_response"])} chars) available in terminal')
                            else:
                                mobile_response = result["full_response"]
                                print(f'📱 Sending full response to mobile ({len(mobile_response)} chars)')

                            # Save as pending before sending (in case connection drops)
                            pending_response = mobile_response

                            # Send response back to frontend
                            ws_client.send_message(mobile_response)

                            # Clear pending response after successful send
                            pending_response = None
                    
                    except Exception as e:
                        error_msg = f'Error processing message: {str(e)}'
                        print(error_msg)

                        # Check if it's a socket closed error - break to trigger reconnect
                        if 'already closed' in str(e).lower() or 'connection' in str(e).lower():
                            print('🔌 Socket closed, breaking to reconnect...')
                            break

                        try:
                            ws_client.send_message(f'Error: {error_msg}')
                        except:
                            pass
            
            except KeyboardInterrupt:
                print('\n👋 Shutting down...')
                claude_session.close()
                ws_client.close()
                sys.exit(0)
            
            except Exception as e:
                print(f'❌ Connection error: {e}')
                ws_client.close()
                
                # Exponential backoff retry
                delay = ws_client.get_retry_delay()
                print(f'🔄 Reconnecting in {delay} seconds...')
                time.sleep(delay)
    
    finally:
        # Always clean up the connection lock
        remove_connection_lock()


if __name__ == '__main__':
    main()
