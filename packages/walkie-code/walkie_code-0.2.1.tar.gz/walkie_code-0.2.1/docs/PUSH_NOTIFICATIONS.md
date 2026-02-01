# VibeVoice Push Notifications Setup

## Overview

VibeVoice uses Apple Push Notification service (APNs) to notify users when a response is ready while their device is offline or in background mode.

## Architecture

1. **iOS App** requests push notification permissions and registers with APNs
2. **APNs** provides a unique device token to the iOS app
3. **iOS App** sends the APNs device token to Lambda via WebSocket
4. **Lambda** stores the APNs token in DynamoDB (`vv-tokens` table)
5. When desktop sends a response and **mobile is offline**, Lambda:
   - Stores message as "dead message" in DynamoDB
   - Sends push notification via APNs HTTP/2 API
6. User **taps notification**, app wakes up, reconnects WebSocket
7. Lambda **delivers dead message** and plays audio

## APNs Setup (Apple Developer Portal)

### Step 1: Create APNs Auth Key

1. Go to [Apple Developer Portal](https://developer.apple.com/account/)
2. Navigate to **Certificates, Identifiers & Profiles**
3. Select **Keys** from left sidebar
4. Click **+** to create new key
5. Name it "VibeVoice APNs Key"
6. Check **Apple Push Notifications service (APNs)**
7. Click **Continue** → **Register**
8. **Download the .p8 file** (you can only download it once!)
9. Note the **Key ID** (e.g., `AB12CD34EF`)

### Step 2: Get Team ID

1. In Apple Developer Portal, click your name in top right
2. Select **Membership**
3. Note your **Team ID** (e.g., `ABCDEFGH12`) V723T992T2

### Step 3: Get App Bundle ID

1. Open Xcode project `VibeVoice.xcodeproj`
2. Select the **VibeVoice** target 
3. Go to **Signing & Capabilities** tab vibevoice.VibeVoice
4. Note the **Bundle Identifier** (e.g., `com.vibevoice.app`)

## Lambda Configuration

### Environment Variables

Add these environment variables to the `claude-websocket-handler` Lambda function:

```bash
APNS_TEAM_ID=ABCDEFGH12
APNS_KEY_ID=AB12CD34EF
APNS_BUNDLE_ID=vibevoice.VibeVoice
APNS_USE_SANDBOX=true  # Use 'false' for production, 'true' for development
APNS_KEY_CONTENT=<p8_file_content>
```

### Getting P8 File Content

Convert the .p8 file to a single-line string:

```bash
# Read the .p8 file and escape newlines
cat AuthKey_AB12CD34EF.p8 | awk 'NF {sub(/\r/, ""); printf "%s\\n",$0;}'
```

Copy the output (it will look like this):

```
-----BEGIN PRIVATE KEY-----\nMIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQgABCDEFGHIJKLMNOP\nQRSTUVWXYZabcdefghijklmnopqrstuv+gCgYIKoZIzj0DAQehRANCAASG1234567\nABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuv\n-----END PRIVATE KEY-----\n
```

Use this value for `APNS_KEY_CONTENT`.

### Update Lambda Environment Variables

#### Option 1: AWS Console

1. Go to [Lambda Console](https://eu-central-1.console.aws.amazon.com/lambda)
2. Select `claude-websocket-handler` function
3. Go to **Configuration** → **Environment variables**
4. Click **Edit**
5. Add the APNs environment variables
6. Click **Save**

#### Option 2: AWS CLI

```bash
aws lambda update-function-configuration \
  --function-name claude-websocket-handler \
  --environment Variables="{
    CONNECTIONS_TABLE=vv-connections,
    USERS_TABLE=vv-users,
    TOKENS_TABLE=vv-tokens,
    AUDIO_BUCKET=claude-voice-audio-381492018552,
    APNS_TEAM_ID=ABCDEFGH12,
    APNS_KEY_ID=AB12CD34EF,
    APNS_BUNDLE_ID=com.vibevoice.app,
    APNS_USE_SANDBOX=true,
    APNS_KEY_CONTENT='-----BEGIN PRIVATE KEY-----\nMIG...'
  }" \
  --region eu-central-1
```

#### Option 3: Update CloudFormation Template

Edit `backend/infra/template.yaml`:

```yaml
ClaudeWebSocketHandler:
  Type: AWS::Lambda::Function
  Properties:
    # ... existing properties ...
    Environment:
      Variables:
        CONNECTIONS_TABLE: !Ref ConnectionsTable
        USERS_TABLE: !Ref UsersTable
        TOKENS_TABLE: !Ref TokensTable
        AUDIO_BUCKET: !Ref AudioBucket
        APNS_TEAM_ID: ABCDEFGH12
        APNS_KEY_ID: AB12CD34EF
        APNS_BUNDLE_ID: com.vibevoice.app
        APNS_USE_SANDBOX: 'true'
        APNS_KEY_CONTENT: |
          -----BEGIN PRIVATE KEY-----
          MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQg...
          -----END PRIVATE KEY-----
```

Then deploy:

```bash
cd backend
./deploy.sh
```

## iOS App Setup

### Enable Push Notifications Capability

1. Open Xcode project
2. Select **VibeVoice** target
3. Go to **Signing & Capabilities** tab
4. Click **+ Capability**
5. Add **Push Notifications**
6. Ensure **Background Modes** is enabled with:
   - ✅ Remote notifications

### Push Notification Entitlements

Xcode should automatically create `VibeVoice.entitlements` with:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>aps-environment</key>
    <string>development</string>  <!-- or "production" -->
</dict>
</plist>
```

## Deployment

### 1. Deploy Lambda with Dependencies

```bash
cd /Users/rax/sandbox/claude_voice/backend
./deploy_websocket_lambda.sh
```

This will:
- Install `PyJWT`, `cryptography`, and `requests` packages
- Package Lambda with dependencies
- Deploy to AWS

### 2. Update Lambda Environment Variables

Use one of the methods above to add APNs configuration.

### 3. Build iOS App

```bash
cd /Users/rax/sandbox/claude_voice/VibeVoice
# Open in Xcode
open VibeVoice.xcodeproj

# Or build from command line
xcodebuild -project VibeVoice.xcodeproj -scheme VibeVoice -sdk iphoneos build
```

## Testing

### Test Push Notifications

1. **Build and run iOS app** on a physical device (simulator doesn't support push)
2. **Grant push notification permissions** when prompted
3. **Check console logs** for APNs device token:
   ```
   ✅ APNs device token received: a1b2c3d4e5f6...
   ```
4. **Connect to desktop app**:
   ```bash
   cd /Users/rax/sandbox/claude_voice/desktop
   python -m venv venv
   source venv/bin/activate
   pip install -e .
   vibe_voice_desktop config  # Enter device token from iOS app
   vibe_voice_desktop
   ```
5. **Lock iPhone screen** (or force quit app)
6. **Send message from desktop**
7. **Push notification should arrive** on iPhone
8. **Tap notification** → app opens → message plays

### Check Lambda Logs

```bash
aws logs tail /aws/lambda/claude-websocket-handler --follow
```

Look for:
```
[identify] ✅ Stored APNs token for 6fe2ef34-...: a1b2c3d4e5f6...
[sendText] ⚠️ No frontends online for token 6fe2ef34-..., storing as DEAD MESSAGE
[sendText] ✅ DEAD MESSAGE stored for token 6fe2ef34-...
[sendText] 📲 Sending push notification to wake device
[send_apns] Sending push to api.sandbox.push.apple.com: VibeVoice Response Ready - ...
[send_apns] ✅ Push notification sent successfully
```

### Troubleshooting

#### Push Not Received

1. **Check APNs token registered:**
   ```bash
   aws dynamodb get-item \
     --table-name vv-tokens \
     --key '{"token": {"S": "YOUR_DEVICE_TOKEN"}}' \
     --region eu-central-1
   ```
   Look for `apnsToken` field.

2. **Check Lambda environment variables:**
   ```bash
   aws lambda get-function-configuration \
     --function-name claude-websocket-handler \
     --region eu-central-1 \
     --query 'Environment.Variables'
   ```

3. **Check APNs endpoint:**
   - Development: `api.sandbox.push.apple.com` (APNS_USE_SANDBOX=true)
   - Production: `api.push.apple.com` (APNS_USE_SANDBOX=false)

4. **Verify bundle ID matches:**
   - iOS app bundle ID
   - APNs Auth Key app ID
   - APNS_BUNDLE_ID environment variable

#### "Invalid Token" Error

- Ensure you're using the correct APNs environment (sandbox vs production)
- Rebuild and reinstall the app to get a fresh APNs device token
- Check that the app's provisioning profile includes push notifications

#### "Forbidden" Error

- Verify APNs Auth Key has push notification capability
- Check Team ID and Key ID are correct
- Ensure .p8 key content is properly formatted

## DynamoDB Schema

The `vv-tokens` table now includes:

| Field | Type | Description |
|-------|------|-------------|
| token | String | Device token (primary key) |
| userId | String | User ID |
| createdAt | Number | Creation timestamp |
| apnsToken | String | APNs device token (optional) |
| deadMessage | Map | Undelivered message (optional) |

## APNs Payload

Push notifications are sent with this payload:

```json
{
  "aps": {
    "alert": {
      "title": "VibeVoice Response Ready",
      "body": "<response_text_truncated_to_200_chars>"
    },
    "sound": "default",
    "badge": 1
  }
}
```

## Security Notes

1. **Never commit .p8 files** to version control
2. **Use AWS Secrets Manager** for production (not environment variables)
3. **Rotate APNs keys** periodically
4. **Use production APNs endpoint** for App Store builds
5. **Validate device tokens** before storage

## Production Checklist

- [ ] Create production APNs Auth Key
- [ ] Set `APNS_USE_SANDBOX=false`
- [ ] Update iOS app to production provisioning profile
- [ ] Store .p8 key in AWS Secrets Manager
- [ ] Enable CloudWatch alarms for push notification failures
- [ ] Test push notifications on production APNs endpoint
- [ ] Monitor APNs feedback service for invalid tokens
