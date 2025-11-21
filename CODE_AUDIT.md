# Code Audit - Violations Found

## Summary
This document lists all violations of the CLAUDE.md standards found in the current codebase.

## Critical Issues

### 1. Placeholder Code in `agent/core/permissions.py`

**Lines 131-152:** `learn_from_response()` method
```python
def learn_from_response(...):
    """
    Learn from user's approval/rejection of an action

    This is a placeholder for future ML-based learning.  # VIOLATION: Explicit placeholder
    For now, it just logs the interaction.

    ...
    """
    # Log the interaction for future learning
    self.mcp_client.log_interaction(...)

    # Future enhancement: Use ML to adjust permissions automatically  # VIOLATION: TODO comment
    # based on patterns in user approvals/rejections
```

**Violations:**
- Line 131: Docstring admits "This is a placeholder for future ML-based learning"
- Line 151-152: Comments about "Future enhancement" that isn't implemented
- Function pretends to "learn" but only logs

**Required Fix:**
- Either implement actual learning logic
- OR rename to `log_permission_response()` and remove claims about learning
- OR remove the function entirely if not needed

---

### 2. Type Hint Violations - Missing Specific Types

**File: `agent/tools/mcp_client.py`**

**All methods return generic `Dict`, `List`, `bool`, `Any`** without specific structure definition.

Examples:
- Line 21: `def get_user_profile(self, user_id: str) -> Dict:` - What's in the dict?
- Line 42: `def get_conversation_history(...) -> List[Dict]:` - What's the message structure?
- Line 160: `def cache_get(self, key: str) -> Any:` - Too generic

**Required Fix:**
Define TypedDict classes for all return structures:
```python
from typing import TypedDict, List, Optional

class UserProfile(TypedDict):
    user_id: str
    name: str
    email: str
    role: str
    industry: str
    interests: List[str]
    # ... complete schema

class ConversationMessage(TypedDict):
    sender: str
    message: str
    timestamp: float
    metadata: Dict[str, Any]
```

---

**File: `agent/core/agent.py`**

Multiple methods return generic `Dict` without specification:
- Line 208: `def handle_new_person_nearby(...) -> Dict:` - What's the structure?
- Line 344: `def handle_incoming_message(...) -> Dict:` - What fields?
- Line 405: `def run(self, task: str) -> Dict:` - What's in the response?

---

**File: `agent/main.py`**

- Line 83: `def get_or_create_agent(user_id: str) -> SociusAgent:` - Good!
- But many endpoint functions don't specify response types beyond generic dicts

---

### 3. Error Handling Violations

**File: `agent/tools/imessage_tool.py`**

Lines 33-38:
```python
except requests.exceptions.RequestException as e:
    return {
        "success": False,
        "error": f"Failed to connect to iMessage server: {str(e)}"
    }
```

**Issue:** Silent failure - function returns error dict but caller might not check it.

**Required Fix:** Either raise exception or use Result type pattern

---

**File: `agent/tools/gmail_tool.py`**

Line 128: Bare `except:` block
```python
try:
    level1 = next(...)
    level2 = next(...)
    # ...
except:  # VIOLATION: Bare except
    pass
```

**Required Fix:** Specify exception type or remove try/except if not needed

---

**File: `agent/tools/mcp_client.py`**

**Every single method** has this pattern:
```python
try:
    response = requests.get(...)
    return response.json() if response.status_code == 200 else {}
except requests.exceptions.RequestException:
    return {}  # VIOLATION: Silent failure with empty dict
```

**Issues:**
- Returns empty dict on failure - caller can't distinguish between "no data" and "error"
- No logging of errors
- Swallows all request exceptions

**Required Fix:**
```python
def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
    """
    Get user profile from MCP server.

    Args:
        user_id: User ID to fetch

    Returns:
        User profile if found and request succeeds, None otherwise

    Raises:
        MCPConnectionError: If cannot connect to MCP server
        MCPError: If server returns error response
    """
    try:
        response = requests.get(
            f"{self.server_url}/profiles/{user_id}",
            timeout=10
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return UserProfile(**response.json())

    except requests.exceptions.ConnectionError as e:
        raise MCPConnectionError(f"Cannot connect to MCP server at {self.server_url}: {e}")

    except requests.exceptions.Timeout:
        raise MCPConnectionError(f"MCP server timeout after 10s")

    except requests.exceptions.HTTPError as e:
        raise MCPError(f"MCP server error: {e.response.status_code} {e.response.text}")
```

---

### 4. Incomplete Implementation

**File: `agent/core/matching.py`**

Line 88: Comment admits incompleteness
```python
# Related industries (basic keyword matching)
# This could be enhanced with industry taxonomy  # VIOLATION: Incomplete feature
```

**Issue:** Comment indicates feature is basic/incomplete but no plan to fix

**Required Fix:** Either:
- Implement proper industry taxonomy
- OR remove comment and document current behavior as intended
- OR add to backlog and remove from code

---

### 5. Documentation Violations

**File: `agent/core/agent.py`**

Many methods lack complete docstrings:
- `_send_imessage_wrapper` (line 139) - no Raises section
- `_send_email_wrapper` (line 151) - no Raises section
- `_schedule_meeting_wrapper` (line 164) - no Raises section

All can raise `json.JSONDecodeError` or `KeyError` but don't document it.

---

### 6. Emoji Violations

**File: `README.md`, `QUICKSTART.md`, `imessage-server/server.py`**

Multiple emojis in:
- Print statements (line 277-279 in imessage-server/server.py): "🚀", "📱", "⚙️"
- Documentation: "✅", "❌", "📁", etc.

**Required Fix:** Remove all emojis or move to user-facing UI only

---

### 7. Missing Type Definitions

**Files: Multiple**

No TypedDict or Pydantic models defined for:
- User profiles
- Conversation messages
- Match results
- API responses
- Permission settings
- Context objects

**Required Fix:** Create `agent/types.py` with all data models

---

## Files That Need Complete Rewrite

1. **`agent/tools/mcp_client.py`** - All methods have silent failure pattern
2. **`agent/core/permissions.py`** - Contains placeholder function
3. **`agent/types.py`** - Needs to be created with all type definitions

## Files That Need Significant Updates

1. **`agent/core/agent.py`** - Add proper type hints, error handling
2. **`agent/tools/gmail_tool.py`** - Fix bare except, improve error handling
3. **`agent/tools/imessage_tool.py`** - Better error handling
4. **`agent/main.py`** - Add response type models

## Total Violation Count

- Placeholder code: 1 function
- Type hint issues: ~30+ functions
- Error handling issues: ~25+ locations
- Documentation issues: ~15+ functions
- Emoji violations: ~20+ locations
- Missing type definitions: ~10+ data structures

## Recommended Action Plan

1. Create `agent/types.py` with all TypedDict/Pydantic models
2. Completely rewrite `agent/tools/mcp_client.py` with proper error handling
3. Fix or remove placeholder in `agent/core/permissions.py`
4. Add type hints throughout codebase
5. Add proper error handling with custom exceptions
6. Remove all emojis from code
7. Complete all docstrings with Raises sections

Estimated effort: 4-6 hours of focused refactoring to bring to compliance.
