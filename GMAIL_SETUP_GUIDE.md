# Gmail & Calendar Setup Guide for Socius Agent

## Quick Start - Get Agent Sending Emails in 5 Minutes

### Step 1: Google Cloud Setup (2 minutes)

1. Go to https://console.cloud.google.com/
2. Click "Select a project" → "New Project"
3. Name it "Socius Agent" → Click "Create"
4. Wait for project creation (~30 seconds)

### Step 2: Enable APIs (1 minute)

1. In the search bar, type "Gmail API" → Click "Enable"
2. In the search bar, type "Google Calendar API" → Click "Enable"

### Step 3: OAuth Consent Screen (1 minute)

1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose "External" → Click "Create"
3. Fill in:
   - App name: `Socius Agent`
   - User support email: Your email
   - Developer contact: Your email
4. Click "Save and Continue" (skip scopes for now)
5. Click "Save and Continue" (skip test users for now)

### Step 4: Create Credentials (1 minute)

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Choose "Desktop app"
4. Name it: `Socius Desktop`
5. Click "Create"
6. Click "Download JSON"
7. Save the file

### Step 5: Install Credentials

```bash
# Create credentials directory
mkdir -p /home/yab/socius/agent/credentials

# Move the downloaded file
mv ~/Downloads/client_secret_*.json /home/yab/socius/agent/credentials/gmail_credentials.json
```

### Step 6: Test It!

```bash
cd /home/yab/socius/agent

# Test Gmail connection (will open browser for OAuth)
python3 << 'EOF'
from tools.gmail_tool import GmailTool

# Initialize (will prompt for OAuth)
gmail = GmailTool()

# Send test email
result = gmail.send_email(
    to="yeabsiramulugeta67@gmail.com",
    subject="Test from Socius Agent",
    body="Hi! This is a test email from your AI agent. If you're seeing this, Gmail integration is working!"
)

print(f"✅ Email sent! Message ID: {result.message_id}")
EOF
```

## Detailed Guide

### What You'll Need:
- Google Account (Gmail)
- 5 minutes
- Internet connection

### OAuth Flow:

1. First run will open your browser
2. Sign in to your Google account
3. Click "Allow" to grant permissions
4. Credentials will be saved to `token.json`
5. Future runs will use saved token (no browser needed)

### Scopes Requested:

- `gmail.send` - Send emails on your behalf
- `gmail.readonly` - Read your emails
- `calendar` - Manage your calendar events

### Security Notes:

✅ OAuth tokens are stored locally
✅ Tokens can be revoked at https://myaccount.google.com/permissions
✅ App runs on your machine only
✅ No data is sent to external servers

## Agent Email & Calendar Capabilities

### 1. Send Email

**Endpoint:** `POST /users/{user_id}/send-email`

```json
{
  "recipient": "yeabsiramulugeta67@gmail.com",
  "subject": "Meeting Request",
  "body": "Would you like to meet for coffee?",
  "context": {
    "match_score": 0.85,
    "event": "AI Conference 2025"
  }
}
```

**What happens:**
1. Agent checks permissions (AUTO_HIGH_MATCH for >75% matches)
2. If auto-approved, sends email via Gmail API
3. Logs interaction to MCP Server
4. Returns email status

### 2. Create Calendar Event

**Endpoint:** `POST /users/{user_id}/schedule-meeting`

```json
{
  "attendees": ["yeabsiramulugeta67@gmail.com"],
  "title": "Coffee Meeting",
  "start_time": "2025-11-25T10:00:00",
  "duration_minutes": 60,
  "location": "Blue Bottle Coffee, SF"
}
```

**What happens:**
1. Checks attendee's calendar for conflicts
2. Finds available time slots
3. Creates calendar event
4. Sends calendar invite to attendee
5. Logs to MCP Server

### 3. Check Busy Times

**Endpoint:** `GET /users/{user_id}/busy-times?attendee=yeabsiramulugeta67@gmail.com&start=2025-11-25&end=2025-11-29`

**Returns:**
```json
{
  "busy_slots": [
    {
      "start": "2025-11-25T14:00:00",
      "end": "2025-11-25T15:00:00"
    }
  ],
  "suggested_times": [
    "2025-11-25T10:00:00",
    "2025-11-25T16:00:00",
    "2025-11-26T11:00:00"
  ]
}
```

## Full Integration Example

### Scenario: Agent meets Yeabsira at AI Conference

```python
# 1. User detection (proximity service)
POST /users/alice/detected
{
  "other_user_id": "yeabsira",
  "context": {"event": "AI Conference", "location": "SF"}
}

# Agent calculates match score: 85% (high match!)

# 2. Agent checks permissions
# AUTO_HIGH_MATCH for send_email → AUTO APPROVED

# 3. Agent sends introduction email
gmail.send_email(
    to="yeabsiramulugeta67@gmail.com",
    subject="Great to meet you at AI Conference!",
    body="Hi Yeabsira! I'm Alice's AI networking agent. Alice noticed you're working on similar projects in AI. Would you be interested in connecting for coffee?"
)

# 4. If Yeabsira replies positively...
# Agent checks both calendars for availability

busy_times = gmail.get_busy_times(
    attendees=["alice@example.com", "yeabsiramulugeta67@gmail.com"],
    start_date="2025-11-25",
    days=7
)

# 5. Agent suggests available time
# 6. Once confirmed, creates calendar event

event = gmail.create_calendar_event(
    title="Coffee: Alice & Yeabsira",
    attendees=["yeabsiramulugeta67@gmail.com"],
    start="2025-11-26T10:00:00-08:00",
    end="2025-11-26T11:00:00-08:00",
    location="Blue Bottle Coffee, SF",
    description="Discussing AI projects and potential collaboration"
)

# 7. Both get calendar invites!
```

## Testing Without Browser (Headless)

If you're on a server without a browser:

1. Run setup on your local machine first
2. Complete OAuth flow in browser
3. Copy `token.json` to server:

```bash
scp ~/.socius/agent/credentials/token.json server:/home/yab/socius/agent/credentials/
```

## Troubleshooting

### "Access blocked: This app's request is invalid"
- Add your email to test users in OAuth consent screen
- Or publish the app (not recommended for personal use)

### "Insufficient permissions"
- Check scopes in OAuth consent screen
- Re-authenticate by deleting token.json

### "Token expired"
- Delete `token.json`
- Run again to re-authenticate

## Rate Limits

Gmail API limits (free tier):
- 10,000 requests/day
- 100 requests/minute
- Plenty for personal networking!

## Next Steps

Once Gmail is set up:

1. ✅ Agent can autonomously send emails
2. ✅ Agent can create calendar meetings
3. ✅ Agent can check availability
4. ✅ All actions logged to MCP Server
5. ✅ Permissions control what's automatic

Try it with:
```bash
curl -X POST http://localhost:5000/users/alice/send-email \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "yeabsiramulugeta67@gmail.com",
    "subject": "Testing Socius Agent",
    "body": "Hi! This is my AI networking agent."
  }'
```
