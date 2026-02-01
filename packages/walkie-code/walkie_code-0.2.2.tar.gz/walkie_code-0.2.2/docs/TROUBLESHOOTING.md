# VibeVoice Troubleshooting Guide

## Messages Not Reaching Desktop

### Symptoms
- Mobile app shows "Upload complete"
- Transcription completes successfully
- Desktop app doesn't receive the message

### Diagnostic Steps

#### 1. Check Device Tokens Match

**Mobile App:**
1. Tap the 🔑 key icon
2. Copy the device token
3. Example: `A1B2C3D4-E5F6-7890-ABCD-EF1234567890`

**Desktop App:**
1. Check `.vibevoice_config.json`:
```json
{
  "endpoint": "wss://api.ducku.io/prod/",
  "deviceToken": "A1B2C3D4-E5F6-7890-ABCD-EF1234567890"
}
```
2. Or check the startup output:
```
Device Token: A1B2C3D4-E5F6-7890-ABCD-EF1234567890
```

**Important:** Tokens must match EXACTLY (including hyphens and case)

#### 2. Check Lambda Logs

After redeploying the Lambda with enhanced logging:

```bash
cd backend
./deploy.sh
```

View CloudWatch logs:
```bash
aws logs tail /aws/lambda/claude-websocket-handler --follow
```

**Look for these log entries:**

When mobile connects:
```
[identify] Role: frontend, DeviceToken: ABC123...
[identify] Authenticated/created user: user-uuid
[register_connection] Adding device token to connection: ABC123...
[register_connection] Stored connection: {...}
```

When desktop connects:
```
[identify] Role: desktop, DeviceToken: ABC123...
[identify] Authenticated/created user: user-uuid
[register_connection] Adding device token to connection: ABC123...
```

When audio is transcribed:
```
[audioUploaded] Sender device token: ABC123...
[audioUploaded] Querying for desktop connections with token: ABC123...
[audioUploaded] Found 1 connections with token
[audioUploaded] Filtered to 1 desktop connections
[audioUploaded] Sent transcription to desktop connection-id
```

#### 3. Common Issues

**Issue: Device token is `None` in logs**
- **Cause:** Mobile/desktop not sending token during identify
- **Fix:** Make sure both apps are updated and restarted
- **Check:** iOS app should show token when you tap 🔑
- **Check:** Desktop should print token on startup

**Issue: "Found 0 connections with token"**
- **Cause:** Desktop not connected or using different token
- **Fix:** Ensure desktop is running and connected
- **Fix:** Restart desktop with correct token
- **Check:** Desktop should show "Listening for incoming messages..."

**Issue: Token mismatch**
- **Cause:** Mobile and desktop have different tokens
- **Fix:** Delete mobile app and reinstall (generates new token)
- **Fix:** Update desktop config with new token from mobile
- **Alternative:** Clear token on mobile (requires code change)

**Issue: DynamoDB errors**
- **Cause:** Tables not deployed or permissions missing
- **Fix:** Redeploy infrastructure:
```bash
cd backend
./deploy.sh
```
- **Check:** Verify tables exist:
```bash
aws dynamodb list-tables --query 'TableNames[?contains(@, `claude`)]'
```

#### 4. Manual DynamoDB Check

Check connections table:
```bash
aws dynamodb scan --table-name claude-connections \
  --projection-expression "connectionId,#r,deviceToken" \
  --expression-attribute-names '{"#r":"role"}'
```

Expected output:
```json
{
  "Items": [
    {
      "connectionId": "abc123==",
      "role": "frontend",
      "deviceToken": "ABC123-DEF456..."
    },
    {
      "connectionId": "xyz789==",
      "role": "desktop",
      "deviceToken": "ABC123-DEF456..."
    }
  ]
}
```

**Verify:**
- Both connections exist
- Both have the same `deviceToken`
- Roles are correct (`frontend` and `desktop`)

Check users table:
```bash
aws dynamodb scan --table-name claude-users
```

#### 5. WebSocket Connection Check

**Mobile App:**
- Should show green dot "Connected"
- Status should show "✓ Identified as frontend"

**Desktop App:**
- Should show "Identifying with device token..."
- Should show "Listening for incoming messages from frontend..."
- Should NOT show connection errors

#### 6. Test Message Flow

**Step 1:** Start desktop app
```bash
python send_text.py
```

Expected output:
```
Device Token: ABC123-DEF456...
Connecting to wss://api.ducku.io/prod/
Identifying with device token...
Listening for incoming messages from frontend...
```

**Step 2:** Send test message from desktop
The desktop automatically sends: "Desktop connected with token ABC123..."

**Step 3:** Check mobile app
Should see: "🔊 Playing response..."

If this works, the connection is bidirectional and tokens match!

**Step 4:** Test voice from mobile
1. Tap microphone
2. Speak a message
3. Release microphone
4. Wait for "Upload complete"

**Step 5:** Check desktop terminal
Should see:
```
Frontend message: [your transcribed text]
```

### Quick Fixes

**Reset Everything:**
1. Stop desktop app
2. Close mobile app completely
3. Redeploy Lambda: `cd backend && ./deploy.sh`
4. Start desktop app: `python send_text.py`
5. Open mobile app
6. Wait for "Connected" status

**Get Fresh Start:**
1. Delete mobile app from device
2. Reinstall mobile app (new token generated)
3. Copy new token from mobile
4. Update desktop config with new token
5. Restart desktop app

### Still Not Working?

Enable verbose AWS logging in Lambda:
1. Edit `backend/lambda/app.py`
2. Change log level: `logger.setLevel(logging.DEBUG)`
3. Redeploy: `./backend/deploy.sh`
4. Check CloudWatch logs for detailed trace

Contact support with:
- CloudWatch logs (last 10 minutes)
- DynamoDB scan output
- Mobile app status messages
- Desktop app terminal output
