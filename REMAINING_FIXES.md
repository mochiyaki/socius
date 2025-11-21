# Remaining Fixes for Production-Ready Code

## Completed
- [x] Created types.py with all TypedDict models
- [x] Created exceptions.py with custom exception classes
- [x] Completely rewrote mcp_client.py with proper error handling
- [x] Fixed permissions.py placeholder function (renamed to `log_permission_response`)

## Remaining Tasks

### 1. Fix imessage_tool.py
File: `agent/tools/imessage_tool.py`

Issues:
- Import types and exceptions
- Add proper type hints to all methods
- Raise exceptions instead of returning error dicts
- Add complete docstrings with Raises sections

Changes needed:
```python
from types import iMessageSendResponse, iMessageHistory
from exceptions import iMessageConnectionError, iMessageSendError
import logging

logger = logging.getLogger(__name__)

def send_message(self, recipient: str, message: str) -> iMessageSendResponse:
    """
    Send an iMessage to a recipient

    Args:
        recipient: Phone number or email of the recipient
        message: Message content to send

    Returns:
        Response with success status and details

    Raises:
        iMessageConnectionError: Cannot connect to iMessage server
        iMessageSendError: Failed to send message
    """
    try:
        response = requests.post(...)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError as e:
        raise iMessageConnectionError(f"Cannot connect to iMessage server at {self.server_url}") from e
    except requests.exceptions.HTTPError as e:
        raise iMessageSendError(f"Failed to send iMessage: {e.response.text}") from e
```

### 2. Fix gmail_tool.py
File: `agent/tools/gmail_tool.py`

Issues:
- Line 128: Bare `except:` block - specify exception type
- Import types and exceptions
- Add proper type hints
- Raise exceptions for Gmail/Calendar errors

Changes needed:
```python
from types import EmailSendResponse, CalendarEventResponse, BusyTimeSlot
from exceptions import GmailAuthError, GmailSendError, CalendarAuthError, CalendarEventError
import logging

logger = logging.getLogger(__name__)

# Fix bare except at line 128:
try:
    level1 = next((i for i, level in enumerate(seniority_levels) if level in seniority1.lower()), -1)
    level2 = next((i for i, level in enumerate(seniority_levels) if level in seniority2.lower()), -1)
    # ... rest of logic
except StopIteration:
    # Handle if next() fails
    logger.debug("Could not determine seniority levels")

# Add Raises sections to all docstrings
```

### 3. Update agent.py type hints
File: `agent/core/agent.py`

Add imports:
```python
from types import (
    UserProfile,
    DetectionContext,
    DetectionResponse,
    IncomingMessageResponse,
    MatchResult
)
from exceptions import ProfileNotFoundError, AgentError
```

Update method signatures:
```python
def handle_new_person_nearby(
    self,
    other_user_id: str,
    context: DetectionContext
) -> DetectionResponse:
    """
    ...

    Raises:
        ProfileNotFoundError: If other user profile not found
        MCPConnectionError: If cannot connect to MCP server
        iMessageSendError: If message sending fails
    """

def handle_incoming_message(
    self,
    sender_id: str,
    message: str,
    conversation_id: str
) -> IncomingMessageResponse:
    """
    ...

    Raises:
        ProfileNotFoundError: If sender profile not found
        MCPConnectionError: If cannot connect to MCP server
        AgentError: For other agent errors
    """
```

### 4. Update main.py with response models
File: `agent/main.py`

Add Pydantic models for all responses:
```python
from pydantic import BaseModel
from types import DetectionResponse, IncomingMessageResponse
from exceptions import *

# Add error handler
@app.exception_handler(MCPConnectionError)
async def mcp_connection_error_handler(request, exc):
    return JSONResponse(
        status_code=503,
        content={"error": "MCP server unavailable", "detail": str(exc)}
    )

# Add for all custom exceptions...

# Update endpoint response types
@app.post('/users/{user_id}/detected', response_model=DetectionResponse)
async def user_detected(user_id: str, request: UserDetectedRequest):
    """
    ...

    Raises:
        HTTPException: 503 if MCP server unavailable
        HTTPException: 500 for other errors
    """
```

### 5. Remove all emojis
Files to update:
- `imessage-server/server.py` lines 277-279
- `README.md` - all instances
- `QUICKSTART.md` - all instances

Replace with plain text:
- Instead of "🚀 Starting..." use "Starting..."
- Instead of "✅" use "[DONE]" or remove
- Instead of "❌" use "[FAIL]" or remove

### 6. Update matching.py
File: `agent/core/matching.py`

Remove incomplete comment at line 88:
```python
# OLD:
# Related industries (basic keyword matching)
# This could be enhanced with industry taxonomy

# NEW: Just document current behavior
# Uses keyword matching to find related industries
```

Add imports and type hints:
```python
from types import UserProfile, MatchResult

def calculate_match_score(self, user1_profile: UserProfile, user2_profile: UserProfile) -> float:
def get_match_reason(self, user1_profile: UserProfile, user2_profile: UserProfile, score: float) -> str:
```

### 7. Complete all docstrings
Every function must have complete docstring with:
- Brief description
- Args section
- Returns section
- **Raises section** (this is what's missing from most functions)

Example template:
```python
def function_name(param: Type) -> ReturnType:
    """
    Brief description.

    Longer description if needed.

    Args:
        param: Description and constraints

    Returns:
        Description of return value

    Raises:
        SpecificError: When this specific error occurs
        AnotherError: When this other error occurs
    """
```

## Testing After Fixes

Create test file: `agent/test_imports.py`
```python
"""Test that all imports work correctly"""

try:
    from types import *
    from exceptions import *
    from tools.mcp_client import MCPClient
    from tools.imessage_tool import iMessageTool
    from tools.gmail_tool import GmailTool
    from core.agent import SociusAgent
    from core.matching import MatchingEngine
    from core.permissions import PermissionsManager
    print("All imports successful")
except Exception as e:
    print(f"Import error: {e}")
    raise
```

Run: `python agent/test_imports.py`

## Priority Order

1. Fix imessage_tool.py (critical - used by agent)
2. Fix gmail_tool.py (critical - used by agent)
3. Update agent.py types (critical - core component)
4. Update main.py error handling (important - API layer)
5. Remove emojis (cosmetic but per standards)
6. Update matching.py docs (minor)
7. Complete all docstrings (cleanup)

## Estimated Time

- imessage_tool.py: 30 min
- gmail_tool.py: 45 min
- agent.py: 1 hour
- main.py: 45 min
- Emojis: 15 min
- matching.py: 15 min
- Docstrings: 1 hour

Total: ~4.5 hours

## Validation Checklist

After all fixes:
- [ ] All imports work without errors
- [ ] No TODO/placeholder comments
- [ ] All functions have type hints
- [ ] All external calls have error handling
- [ ] All docstrings have Raises sections
- [ ] No bare except blocks
- [ ] No emojis in code
- [ ] No silent failures (empty dict returns)
- [ ] Custom exceptions used throughout
- [ ] Logging added where appropriate
