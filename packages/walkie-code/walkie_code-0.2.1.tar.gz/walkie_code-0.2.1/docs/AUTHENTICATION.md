# Device Token Authentication

## Overview

The system now uses device token-based authentication to connect iOS/mobile clients with desktop clients, enabling multi-user support where each user has their own isolated communication channel.

## How It Works

### 1. Device Token Generation (iOS App)

- When the iOS app launches, it automatically generates or retrieves a persistent device token (UUID)
- This token is stored in `UserDefaults` and persists across app launches
- The token is unique to each device installation

### 2. WebSocket Connection with Token

When connecting to the WebSocket:

**iOS/Mobile Client:**
```json
{
  "action": "identify",
  "role": "frontend",
  "deviceToken": "abc123-def456-..."
}
```

**Desktop Client:**
```json
{
  "action": "identify",
  "role": "desktop",
  "deviceToken": "abc123-def456-..."
}
```

### 3. Lambda Authentication Flow

1. Lambda receives the `identify` message with `deviceToken`
2. Queries the `UsersTable` DynamoDB table using the `DeviceTokenIndex` GSI
3. If user exists: Returns the `userId` and registers the connection
4. If user doesn't exist: Creates a new user entry with the token and registers the connection
5. Stores the connection with `deviceToken` and `userId` in the `ConnectionsTable`

### 4. Message Routing

Messages are now routed based on device token:

- **Frontend → Desktop**: When a frontend sends audio for transcription, it's only sent to desktop connections with the same device token
- **Desktop → Frontend**: When a desktop sends a response, it's only sent to frontend connections with the same device token

## User Guide

### iOS App Setup

1. Launch the iOS app
2. Tap the **key icon** (🔑) in the top-right corner
3. The device token will be displayed
4. Tap the **copy button** to copy the token to clipboard
5. Share this token with your desktop client

### Desktop Client Setup

1. Get the device token from your iOS app
2. Run the desktop client with the token:
   ```bash
   python send_text.py wss://YOUR-API-ID.execute-api.REGION.amazonaws.com/prod/ YOUR-DEVICE-TOKEN
   ```

Example:
```bash
python send_text.py wss://qcc76l29g6.execute-api.eu-central-1.amazonaws.com/prod/ "A1B2C3D4-E5F6-7890-ABCD-EF1234567890"
```

## Multi-User Support

Multiple users can now use the same infrastructure simultaneously:

- User A: iOS device (token: `abc-123`) ↔️ Desktop A (token: `abc-123`)
- User B: iOS device (token: `xyz-789`) ↔️ Desktop B (token: `xyz-789`)

Messages from User A will only reach User A's devices, and vice versa.

## Database Structure

### UsersTable (claude-users)

```
Primary Key: userId (String)
Attributes:
  - userId: UUID (auto-generated)
  - deviceToken: String (provided by client)
  - createdAt: Number (Unix timestamp)

Global Secondary Index: DeviceTokenIndex
  - Key: deviceToken
```

### ConnectionsTable (claude-connections)

```
Primary Key: connectionId (String)
Attributes:
  - connectionId: String (WebSocket connection ID)
  - role: String ("frontend" | "desktop")
  - deviceToken: String (user's device token)
  - userId: String (user's ID from UsersTable)

Global Secondary Indexes:
  - RoleIndex (key: role)
  - DeviceTokenIndex (key: deviceToken)
```

## Security Notes

- Device tokens are UUIDs, providing reasonable uniqueness
- Tokens are persistent per device installation
- No password or additional authentication required (suitable for personal use)
- For production, consider adding:
  - Token expiration
  - Token refresh mechanism
  - Additional authentication layers (OAuth, etc.)
  - Rate limiting per token

## Deployment

After making these changes, redeploy the infrastructure:

```bash
cd backend
./deploy.sh
```

This will:
1. Update the CloudFormation stack with the new `UsersTable`
2. Add the `DeviceTokenIndex` to both tables
3. Update Lambda with new environment variables and permissions
4. Deploy the updated Lambda code

## Troubleshooting

**Desktop can't connect:**
- Verify you're using the exact device token from the iOS app (including hyphens)
- Check that both clients are connected to the WebSocket

**Messages not routing:**
- Ensure both clients identified with the same device token
- Check Lambda logs for authentication errors

**Token lost:**
- If you delete and reinstall the iOS app, a new token will be generated
- The old desktop client will need the new token to reconnect
