# VibeVoice Subscription System

## Overview

VibeVoice offers three subscription tiers with character-based usage tracking. Characters are consumed when the system generates speech responses using AWS Polly.

## Subscription Tiers

### 1. Free Trial
- **Price:** Free
- **Characters:** 2,000
- **Voice Quality:** Standard
- **Use Case:** Try VibeVoice before committing

### 2. Standard ($5)
- **Price:** $5
- **Characters:** 250,000 (~5 hours of coding)
- **Voice Quality:** Standard
- **Use Case:** Regular usage with good quality voice

### 3. Premium ($10)
- **Price:** $10
- **Characters:** 250,000 (~5 hours of coding)
- **Voice Quality:** Natural (Neural)
- **Use Case:** Best voice quality for immersive experience

## How It Works

### First Launch
1. User opens the mobile app
2. Subscription selection screen appears automatically
3. User selects a tier (defaults to "Free Trial")
4. User taps "Continue"
5. Selection is saved locally and sent to backend

### Character Tracking
- Characters are counted when **Claude's responses** are synthesized to speech
- Each text sent to AWS Polly increments the character counter
- User transcriptions (speech-to-text) are **NOT** counted
- Only the actual text length is counted (no HTML, no formatting)

### Usage Display
- Current usage shown in mobile app: "Usage: 1,234/250,000 characters"
- Updates in real-time after each response
- Visible below the connection status

### Changing Subscription
1. Tap the **💳 credit card icon** in top-right
2. Select new subscription tier
3. Tap "Continue"
4. App reconnects with new subscription
5. Character limit and voice quality updated immediately

## Technical Implementation

### Database Schema (UsersTable)

```
{
  "userId": "uuid",
  "deviceToken": "device-uuid",
  "subscriptionType": "free|standard|premium",
  "charactersLimit": 2000|250000,
  "charactersUsed": 1234,
  "createdAt": 1234567890
}
```

### API Flow

**1. Identify with Subscription:**
```json
{
  "action": "identify",
  "role": "frontend",
  "deviceToken": "abc-123",
  "subscriptionType": "premium"
}
```

**Response:**
```json
{
  "type": "identified",
  "subscription": {
    "subscriptionType": "premium",
    "charactersLimit": 250000,
    "charactersUsed": 1234,
    "charactersRemaining": 248766
  }
}
```

**2. Sending Text (Character Tracking):**
```python
# Lambda tracks characters when calling Polly
text_length = len(text)
users_table.update_item(
    Key={'userId': user_id},
    UpdateExpression='ADD charactersUsed :chars',
    ExpressionAttributeValues={':chars': text_length}
)
```

**3. Character Limit Exceeded:**
```json
{
  "type": "error",
  "message": "Character limit exceeded. Used: 251000, Limit: 250000"
}
```

### Voice Engine Selection

Voice engine is automatically selected based on subscription:
- **Free/Standard:** `Engine='standard'` (AWS Polly standard voices)
- **Premium:** `Engine='neural'` (AWS Polly neural voices - more natural)

## User Experience

### Mobile App Features

1. **Subscription View**
   - Beautiful card-based UI
   - Popular tier highlighted
   - Clear feature comparison
   - One-tap selection

2. **Usage Tracking**
   - Real-time character count
   - Displayed below connection status
   - Format: "Usage: X/Y characters"

3. **Easy Access**
   - 💳 icon in top-right to change subscription
   - 🔑 icon for device token
   - Intuitive navigation

### Desktop App

Desktop app doesn't need subscription selection - it uses the mobile app's subscription via the shared device token.

## Deployment

### 1. Deploy Infrastructure (DynamoDB Schema)
```bash
cd backend
./deploy.sh
```

This creates/updates the UsersTable with subscription fields.

### 2. Deploy Lambda Code
```bash
cd backend
./deploy_lambda.sh
```

This deploys the character tracking and subscription logic.

### 3. Build Mobile Apps

The subscription view is automatically shown on first launch. Users can change their subscription anytime via the 💳 icon.

## Future Enhancements

### Payment Integration
- Integrate with Stripe/RevenueCat for actual payments
- Handle subscription renewals
- Add purchase receipts

### Analytics
- Track conversion rates (free → paid)
- Monitor character usage patterns
- Identify power users

### Advanced Features
- Family sharing (multiple devices, shared character pool)
- Rollover unused characters
- Volume discounts for power users
- Enterprise tiers with unlimited usage

### Usage Notifications
- Alert when 80% of characters used
- Suggest upgrade when limit approached
- Weekly usage reports

## Monitoring

### Check User Subscriptions
```bash
aws dynamodb scan --table-name claude-users \
  --projection-expression "userId,subscriptionType,charactersUsed,charactersLimit"
```

### Check Character Usage by Tier
```bash
aws dynamodb scan --table-name claude-users \
  --filter-expression "subscriptionType = :tier" \
  --expression-attribute-values '{":tier":{"S":"premium"}}' \
  --projection-expression "charactersUsed,charactersLimit"
```

### Lambda Logs (Character Tracking)
```bash
aws logs tail /aws/lambda/claude-websocket-handler --follow \
  --filter-pattern "Added.*characters"
```

## Testing

### Test Character Tracking
1. Select "Free Trial" (2,000 characters)
2. Send several voice messages
3. Watch character counter increase
4. Try to exceed limit
5. Verify error message appears

### Test Subscription Change
1. Start with "Free Trial"
2. Send a message (note character count)
3. Change to "Premium"
4. Verify limit updated to 250,000
5. Verify voice quality improved

### Test Voice Quality Difference
1. Use "Free Trial" - note voice quality
2. Switch to "Premium"
3. Send same message
4. Notice more natural, expressive voice

## Pricing Strategy

Current pricing is placeholder. Consider:
- Cost of AWS Polly (Neural vs Standard)
- Cost of AWS Transcribe
- Desired profit margin
- Competitor pricing
- User willingness to pay

**AWS Polly Pricing Reference:**
- Standard: $4 per 1M characters
- Neural: $16 per 1M characters

Our 250K characters ≈ $4 AWS cost for neural, so $10 pricing provides healthy margin.
