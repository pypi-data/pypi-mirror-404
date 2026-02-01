# VibeVoice Authentication Flow

## Overview

VibeVoice uses an email-based authentication system with magic links for verification. No passwords are required.

## Architecture

### Components

1. **iOS App** - Mobile client with email verification UI
2. **Desktop App** - Python desktop client (uses same token authentication)
3. **Email Verification Lambda** - Handles email verification endpoints
4. **WebSocket Lambda** - Handles real-time communication
5. **DynamoDB Tables**:
   - `vv-users` - User accounts with email and verification status
   - `vv-tokens` - Device/session tokens (many-to-one with users)
   - `vv-connections` - Active WebSocket connections

### HTTP API Endpoints

Base URL: `https://fxvf7vo3e8.execute-api.eu-central-1.amazonaws.com/prod`

- `POST /auth` - Initial authentication check (validates token or creates anonymous user)
- `POST /verify` - Initiate email verification
- `GET /email_verification` - Verify email (magic link)
- `GET /check_verification` - Check verification status (polling)

## Authentication Flow

### Step 1: App Startup - Initial Authentication

```
User opens app
  ↓
Read stored token from UserDefaults["deviceToken"] (or empty string if none)
  ↓
POST /auth {"token": "<token_or_empty>"}
  ↓
If 200 OK:
  - If response contains new token → save to UserDefaults → show main app
  - If no new token → existing token valid → show main app
If 403 Forbidden:
  - Show EmailVerificationView
```

**iOS → POST /auth**

```http
POST https://fxvf7vo3e8.execute-api.eu-central-1.amazonaws.com/prod/auth
Content-Type: application/json

{
  "token": "<device_token_or_empty_string>"
}
```

**Backend Logic (depends on REQUIRE_EMAIL_AUTH flag):**

**If REQUIRE_EMAIL_AUTH = "yes":**
- Check if token exists and is valid
- If valid: return `200 OK {"status": "authenticated"}`
- If not valid: return `403 Forbidden {"error": "Authentication required"}`

**If REQUIRE_EMAIL_AUTH = "no" (default):**
- **If token is empty:**
  - Create anonymous user with `email="ANONYMOUS"`, `verified=true`
  - Generate device token
  - Return `200 OK {"token": "<new_token>"}`
- **If token is not empty:**
  - Check if valid
  - If valid: return `200 OK {"status": "authenticated"}`
  - If not valid: return `403 Forbidden {"error": "Not authenticated"}`

**Response (200 OK):**
```json
// Case 1: Existing valid token
{"status": "authenticated"}

// Case 2: New anonymous user token
{"token": "550e8400-e29b-41d4-a716-446655440000"}
```

**Response (403 Forbidden):**
```json
{
  "error": "Authentication required",
  "action": "show_email_verification"
}
```

### Step 2: Email Verification Request (if 403 from /auth)

### Step 2: Email Verification Request

**iOS → POST /verify**

```http
POST https://fxvf7vo3e8.execute-api.eu-central-1.amazonaws.com/prod/verify
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Backend Logic:**

1. Generate UUID `verification_token`
2. Query `vv-users` by email (EmailIndex)
3. **If user exists:**
   - Update: `verified = false`, `verification_token = <new_token>`
4. **If user doesn't exist:**
   - Create new user:
     ```json
     {
       "userId": "<uuid>",
       "email": "user@example.com",
       "verified": false,
       "verification_token": "<uuid>",
       "subscriptionType": "free",
       "charactersUsed": 0,
       "totalCharactersPurchased": 0,
       "createdAt": <timestamp>
     }
     ```
5. Send verification email via SES with link:
   ```
   https://fxvf7vo3e8.execute-api.eu-central-1.amazonaws.com/prod/email_verification?verification_token=<token>
   ```

**Response:**

```json
{
  "message": "Verification email sent",
  "email": "user@example.com"
}
```

### Step 3: App Starts Polling

**iOS → GET /check_verification (every 1 second)**

```http
GET https://fxvf7vo3e8.execute-api.eu-central-1.amazonaws.com/prod/check_verification?email=user@example.com
```

**Backend Logic:**

1. Query `vv-users` by email (EmailIndex)
2. Check `verified` field
3. **If verified == false:**
   - Return `403 Forbidden`
   ```json
   {"error": "Not verified yet"}
   ```
4. **If verified == true:**
   - Generate new UUID device token
   - Store in `vv-tokens`:
     ```json
     {
       "token": "<uuid>",
       "userId": "<user_id>",
       "createdAt": <timestamp>
     }
     ```
   - Return `200 OK`
   ```json
   {"token": "<uuid>"}
   ```

### Step 4: User Clicks Email Link (Browser)

```
User receives email
  ↓
Clicks verification link
  ↓
Opens in browser: GET /email_verification?verification_token=<token>
```

**Backend Logic:**

1. Query `vv-users` by `verification_token` (VerificationTokenIndex)
2. **If found:**
   - Update user: `verified = true`
   - Return HTML:
     ```html
     <h1>Email Successfully Verified</h1>
     <p>You can now close this window and return to the app.</p>
     ```
3. **If not found:**
   - Return HTML:
     ```html
     <h1>Verification Failed</h1>
     <p>Verification token was not found</p>
     ```

### Step 5: App Receives Token

```
Polling detects verified == true
  ↓
Receives device token in response
  ↓
Saves to UserDefaults["deviceToken"]
  ↓
Updates UI state (deviceToken binding)
  ↓
Shows main ContentView
```

### Step 6: Connect to WebSocket

**iOS/Desktop → WebSocket Identify**

```json
{
  "action": "identify",
  "role": "frontend",  // or "desktop"
  "token": "<device_token>",
  "subscriptionType": "free"
}
```

**Backend Logic:**

1. Query `vv-tokens` by token
2. Get `userId` from token
3. Query `vv-users` by `userId`
4. Verify `verified == true`
5. If valid:
   - Store connection in `vv-connections`:
     ```json
     {
       "connectionId": "<ws_connection_id>",
       "role": "frontend",
       "token": "<device_token>",
       "userId": "<user_id>"
     }
     ```
   - Return subscription info and S3 upload credentials
6. If invalid:
   - Return `401 Unauthorized`

## Database Schema

### vv-users

| Field | Type | Indexed | Description |
|-------|------|---------|-------------|
| userId | String | Primary Key | User ID (UUID) |
| email | String | EmailIndex | User email address |
| verification_token | String | VerificationTokenIndex | Current verification token |
| verified | Boolean | - | Email verification status |
| subscriptionType | String | - | free/standard/premium |
| charactersUsed | Number | - | Characters consumed |
| totalCharactersPurchased | Number | - | Total characters available |
| createdAt | Number | - | Unix timestamp |

### vv-tokens

| Field | Type | Indexed | Description |
|-------|------|---------|-------------|
| token | String | Primary Key | Device/session token (UUID) |
| userId | String | UserIdIndex | Associated user ID |
| createdAt | Number | - | Unix timestamp |

**Relationship:** Many tokens → One user (allows multiple devices/sessions)

### vv-connections

| Field | Type | Indexed | Description |
|-------|------|---------|-------------|
| connectionId | String | Primary Key | WebSocket connection ID |
| role | String | RoleIndex | frontend/desktop |
| token | String | TokenIndex | Device token |
| userId | String | - | User ID |

## Security Considerations

### Token Lifecycle

1. **Verification Token:**
   - Single-use (overwritten on new /verify request)
   - Not invalidated after verification (allows re-verification)
   - No expiration (TODO: Add TTL)

2. **Device Token:**
   - Long-lived session token
   - Stored in UserDefaults (iOS) or config file (Desktop)
   - One user can have multiple device tokens
   - No automatic expiration

### Future Improvements

1. **Add TTL to verification tokens** (e.g., 24 hours)
2. **Add token revocation** mechanism
3. **Add refresh tokens** for long-lived sessions
4. **Rate limiting** on /verify endpoint
5. **Device fingerprinting** for suspicious activity detection

## Error Handling

### Common Errors

| Scenario | Response | User Action |
|----------|----------|-------------|
| Email not verified yet | 403 Forbidden | Wait for email, click link |
| Invalid verification token | 404 HTML | Request new verification |
| Token not found | 401 Unauthorized | Re-authenticate |
| Rate limit exceeded | 429 Too Many Requests | Wait and retry |
| Database error | 500 Internal Server Error | Retry later |

## Development & Testing

### Mock Mode (Development)

For local development without SES:
- Email sending can fail gracefully
- Verification token is still generated
- Can manually call `/email_verification?verification_token=<token>` in browser

### Testing the Flow

1. **Start iOS Simulator:**
   ```bash
   open VibeVoice.xcodeproj
   # Run in simulator
   ```

2. **Enter email in app**

3. **Check Lambda logs:**
   ```bash
   aws logs tail /aws/lambda/email-verification-handler --follow
   ```

4. **Get verification token from logs:**
   ```
   [/verify] Created new user <uuid> with verification token
   ```

5. **Manually verify (if email fails):**
   ```bash
   curl "https://fxvf7vo3e8.execute-api.eu-central-1.amazonaws.com/prod/email_verification?verification_token=<token>"
   ```

6. **Watch app poll and receive token**

### Desktop Client Authentication

The desktop client uses the same token-based auth:

```bash
# Configure token
vibe_voice_desktop config
# Enter token when prompted

# Or use directly
vibe_voice_desktop <TOKEN>
```

The desktop sends the same identify message:
```python
{
    "action": "identify",
    "role": "desktop",
    "token": "<device_token>"
}
```

## Deployment Checklist

- [ ] Deploy CloudFormation stack with new tables
- [ ] Verify DynamoDB tables created (vv-users, vv-tokens, vv-connections)
- [ ] Verify SES from email address (noreply@vibevoice.com)
- [ ] Update iOS app with HTTP API endpoint
- [ ] Test complete flow end-to-end
- [ ] Monitor Lambda logs for errors
- [ ] Set up CloudWatch alarms for failed authentications

## API Reference

### POST /auth

Initial authentication check. Validates existing token or creates anonymous user (based on REQUIRE_EMAIL_AUTH flag).

**Request:**
```json
{
  "token": "550e8400-e29b-41d4-a716-446655440000"  // or "" for empty
}
```

**Response (200 OK - existing valid token):**
```json
{
  "status": "authenticated"
}
```

**Response (200 OK - new anonymous user):**
```json
{
  "token": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (403 Forbidden):**
```json
{
  "error": "Authentication required",
  "action": "show_email_verification"
}
```

**Errors:**
- `403` - Token invalid or authentication required
- `500` - Database error

---

### POST /verify

Initiates email verification process.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Verification email sent",
  "email": "user@example.com"
}
```

**Errors:**
- `400` - Missing email
- `500` - Database or SES error

---

### GET /email_verification

Verifies email address (magic link endpoint).

**Query Parameters:**
- `verification_token` (required) - UUID verification token

**Response (200 OK):**
```html
<h1>Email Successfully Verified</h1>
```

**Response (404 Not Found):**
```html
<h1>Verification Failed</h1>
<p>Verification token was not found</p>
```

---

### GET /check_verification

Checks if email is verified and returns device token.

**Query Parameters:**
- `email` (required) - Email address to check

**Response (200 OK):**
```json
{
  "token": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (403 Forbidden):**
```json
{
  "error": "Not verified yet"
}
```

**Errors:**
- `400` - Missing email parameter
- `403` - Email not verified
- `500` - Database error
