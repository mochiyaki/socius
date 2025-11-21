# Socius - AI Networking Agent

Socius is an AI-powered networking assistant that helps you connect with interesting people at events. The agent autonomously reaches out to high-match people, manages conversations, and schedules meetings on your behalf.

## Architecture

```
┌─────────────────┐
│   Mobile App    │  (iOS/Android - proximity detection)
│  (To be built)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│   Agent API     │────▶│  iMessage Server │  (macOS)
│  (Port 5000)    │     │   (Port 5001)    │
└────────┬────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│   MCP Server    │────▶│   Sanity.io      │
│  (Port 5002)    │     │   Redis          │
│ (Team builds)   │     │   SQLite         │
└─────────────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐
│  Gmail API      │
│  (Calendar +    │
│   Email)        │
└─────────────────┘
```

## Components

### 1. Agent API (`/agent`)
The core AI agent built with Claude + LangChain. Handles:
- Interest-based matching
- Conversation management
- Smart permissions
- Action execution (messaging, scheduling, email)

**Tech stack:** Python, FastAPI, Claude API, LangChain

**Run:**
```bash
cd agent
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python main.py
```

### 2. iMessage Server (`/imessage-server`)
macOS server that sends/receives iMessages via AppleScript.

**Tech stack:** Python, FastAPI, AppleScript

**Run (on Mac):**
```bash
cd imessage-server
pip install -r requirements.txt
python server.py
```

### 3. MCP Server (`/mcp-server`) - ✅ BUILT
Central data server providing REST API for:
- User profiles (Sanity.io)
- Conversation history (Redis cache)
- User preferences (SQLite)
- Message templates (Sanity.io)
- Interaction logs (SQLite)

**Tech stack:** Python, FastAPI, Redis, SQLite, Sanity HTTP API

**Run:**
```bash
cd mcp-server
pip install -r requirements.txt
cp .env.example .env
# Edit .env with Sanity API token
python main.py  # Runs on port 5002
```

See [mcp-server/README.md](mcp-server/README.md) for full setup instructions.

### 4. Gmail MCP Server (`/mcp-gmail-and-calendar`)
MCP server for Gmail operations (separate from main MCP server).

**Tech stack:** Python, FastMCP, Gmail API

See [mcp-gmail-and-calendar/README.md](mcp-gmail-and-calendar/README.md) for setup.

### 5. Proximity Service (`/proximity-service`)
**Status:** To be implemented (mobile app)

Will detect nearby users and notify Agent API.

## Features

### Core Features
- ✅ Interest-based matching algorithm
- ✅ Autonomous outreach to high-match people
- ✅ Permission-based action system
- ✅ iMessage integration (via macOS server)
- ✅ Gmail integration (email + calendar)
- ✅ Conversation management with Claude
- ✅ Adaptive communication style

### Smart Permissions
Users can configure when the agent acts autonomously:
- `ALWAYS_ASK` - Ask before every action
- `AUTO_HIGH_MATCH` - Auto-act for high matches (>75% compatibility)
- `ALWAYS_AUTO` - Always act automatically
- `NEVER` - Never perform this action

### Matching Algorithm
Calculates compatibility based on:
- Interest overlap (40% weight)
- Industry/field match (30% weight)
- Role/seniority compatibility (20% weight)
- Goals alignment (10% weight)

## Setup

### Prerequisites
- Python 3.9+
- macOS (for iMessage server)
- Anthropic API key
- Google Cloud project with Gmail/Calendar API enabled

### 1. Agent Setup

```bash
cd agent
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
```bash
ANTHROPIC_API_KEY=your_key_here
IMESSAGE_SERVER_URL=http://localhost:5001
MCP_SERVER_URL=http://localhost:5002
```

For Gmail integration, follow [Google's OAuth setup guide](https://developers.google.com/gmail/api/quickstart/python) and place credentials in `agent/credentials/gmail_credentials.json`.

### 2. iMessage Server Setup (Mac only)

```bash
cd imessage-server
pip install -r requirements.txt
```

Grant Full Disk Access:
1. System Preferences → Security & Privacy → Privacy
2. Full Disk Access → Add Terminal/iTerm
3. Restart Terminal

Run:
```bash
python server.py
```

### 3. Test the System

```bash
# Terminal 1: Start iMessage server
cd imessage-server
python server.py

# Terminal 2: Start Agent API
cd agent
python main.py

# Terminal 3: Test detection
curl -X POST http://localhost:5000/users/user123/detected \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "other_user_id": "user456",
    "context": {"event_name": "Test Event"}
  }'
```

## API Documentation

### Agent API (Port 5000)

Interactive docs: `http://localhost:5000/docs`

**Key endpoints:**
- `POST /users/{user_id}/detected` - Handle user detection
- `POST /users/{user_id}/messages/incoming` - Handle incoming messages
- `POST /users/{user_id}/task` - Execute arbitrary task
- `GET /users/{user_id}/profile` - Get user profile
- `PATCH /users/{user_id}/preferences` - Update preferences

### iMessage Server (Port 5001)

Interactive docs: `http://localhost:5001/docs`

**Key endpoints:**
- `POST /send` - Send iMessage
- `GET /messages` - Get recent messages
- `GET /logs` - Get send logs

## Development

### Project Structure

```
socius/
├── agent/                 # AI agent core
│   ├── core/             # Agent logic
│   │   ├── agent.py      # Main agent with Claude
│   │   ├── matching.py   # Matching algorithm
│   │   └── permissions.py # Permission system
│   ├── tools/            # Integration tools
│   │   ├── imessage_tool.py
│   │   ├── gmail_tool.py
│   │   └── mcp_client.py
│   ├── main.py           # FastAPI server
│   └── config.py         # Configuration
├── imessage-server/      # macOS iMessage bridge
│   ├── server.py
│   └── README.md
├── proximity-service/    # To be implemented
└── README.md
```

### Adding New Actions

1. Add tool function to `agent/core/agent.py`
2. Register with LangChain in `_setup_langchain_agent()`
3. Update permissions in `agent/core/permissions.py`
4. Add endpoint to `agent/main.py` if needed

### Testing

```bash
# Test matching algorithm
cd agent
python -m pytest tests/test_matching.py

# Test permissions
python -m pytest tests/test_permissions.py
```

## Next Steps

1. **Your team:** Build MCP server with Sanity.io, Redis, SQLite
2. **Mobile app:** Implement proximity detection (iOS/Android)
3. **Testing:** Create test user profiles and scenarios
4. **UI:** Build mobile app interface for approvals and chat handoff
5. **Production:** Add authentication, rate limiting, monitoring

## Security Notes

- iMessage server should only be accessible on trusted network
- Add API authentication before production
- Protect user data in MCP server with proper access controls
- Use environment variables for all secrets
- Consider end-to-end encryption for sensitive data

## License

Private project - All rights reserved

---

Built with ❤️ using Claude, LangChain, and FastAPI
