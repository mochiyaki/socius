"""
Core Socius AI Agent with Claude + LangChain
"""
from anthropic import Anthropic
from langchain_anthropic import ChatAnthropic
from typing import Dict, List, Optional
import json

from config import Config
from tools.imessage_tool import iMessageTool
from tools.gmail_tool import GmailTool
from tools.mcp_client import MCPClient
from core.matching import MatchingEngine
from core.permissions import PermissionsManager, ActionType, PermissionLevel


class SociusAgent:
    """Main AI agent for Socius networking"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.anthropic = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

        # Initialize tools
        self.imessage_tool = iMessageTool()
        self.gmail_tool = GmailTool()
        self.mcp_client = MCPClient()

        # Initialize core systems
        self.matching_engine = MatchingEngine(Config.HIGH_MATCH_THRESHOLD)
        self.permissions_manager = PermissionsManager(self.mcp_client)

        # Get user profile and preferences
        self.user_profile = self.mcp_client.get_user_profile(user_id)
        self.user_preferences = self.mcp_client.get_user_preferences(user_id)

        # Initialize LangChain agent
        self._setup_langchain_agent()

    def _setup_langchain_agent(self):
        """Setup Claude with tool calling"""

        # Define tools for Claude API
        self.tools = [
            {
                "name": "send_imessage",
                "description": "Send an iMessage to someone. Input should have 'recipient' (phone number or email) and 'message' (text content) fields.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "recipient": {"type": "string", "description": "Phone number or email of the recipient"},
                        "message": {"type": "string", "description": "Message content to send"}
                    },
                    "required": ["recipient", "message"]
                }
            },
            {
                "name": "send_email",
                "description": "Send an email to someone.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email address"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email body content"}
                    },
                    "required": ["to", "subject", "body"]
                }
            },
            {
                "name": "schedule_meeting",
                "description": "Schedule a calendar meeting.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "Meeting title"},
                        "start_time": {"type": "string", "description": "Start time in ISO format"},
                        "duration_minutes": {"type": "integer", "description": "Duration in minutes"},
                        "attendees": {"type": "array", "items": {"type": "string"}, "description": "List of attendee emails"},
                        "description": {"type": "string", "description": "Optional meeting description"}
                    },
                    "required": ["summary", "start_time", "duration_minutes", "attendees"]
                }
            },
            {
                "name": "get_profile",
                "description": "Get a user's profile information.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User ID to fetch"}
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "calculate_match",
                "description": "Calculate compatibility match score between me and another user.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "other_user_id": {"type": "string", "description": "ID of the other user"}
                    },
                    "required": ["other_user_id"]
                }
            }
        ]

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent"""
        user_name = self.user_profile.get('name', 'User')
        user_role = self.user_profile.get('role', 'professional')
        user_interests = ', '.join(self.user_profile.get('interests', []))
        conversation_style = self.user_preferences.get('conversation_style', {})

        return f"""You are Socius, an AI networking assistant for {user_name}.

Your primary role is to help {user_name} connect with interesting people at events and build meaningful professional relationships.

About {user_name}:
- Role: {user_role}
- Interests: {user_interests}
- Communication style: {json.dumps(conversation_style)}

Your capabilities:
1. Send iMessages and emails on {user_name}'s behalf
2. Schedule calendar meetings
3. Calculate compatibility with potential connections
4. Adapt conversation style based on the person you're talking to

Guidelines:
- Be friendly, professional, and authentic
- Match {user_name}'s communication style (tone, length, formality)
- When reaching out, mention why you think there's a good connection
- Always prioritize building genuine relationships over forced networking
- For high-match people (compatibility > 75%), you can autonomously reach out
- For lower matches, describe why you want to connect and ask for approval first
- Learn from responses and adapt your approach

When someone responds:
1. Analyze their response tone and style
2. Find common ground or interesting topics
3. Keep the conversation flowing naturally
4. Look for opportunities to suggest meeting in person
5. Ask if {user_name} wants to take over the conversation when appropriate

Remember: You represent {user_name}, so maintain their reputation and authenticity."""

    def _execute_tool(self, tool_name: str, tool_input: Dict) -> Dict:
        """Execute a tool and return the result"""
        try:
            if tool_name == "send_imessage":
                result = self.imessage_tool.send_message(
                    tool_input['recipient'],
                    tool_input['message']
                )
                return result

            elif tool_name == "send_email":
                result = self.gmail_tool.send_email(
                    to=tool_input['to'],
                    subject=tool_input['subject'],
                    body=tool_input['body']
                )
                return result

            elif tool_name == "schedule_meeting":
                from datetime import datetime, timedelta

                start_time = datetime.fromisoformat(tool_input['start_time'])
                duration = int(tool_input.get('duration_minutes', 30))
                end_time = start_time + timedelta(minutes=duration)

                result = self.gmail_tool.create_calendar_event(
                    summary=tool_input['summary'],
                    start_time=start_time,
                    end_time=end_time,
                    attendees=tool_input['attendees'],
                    description=tool_input.get('description')
                )
                return result

            elif tool_name == "get_profile":
                profile = self.mcp_client.get_user_profile(tool_input['user_id'])
                return profile or {}

            elif tool_name == "calculate_match":
                other_profile = self.mcp_client.get_user_profile(tool_input['other_user_id'])
                score = self.matching_engine.calculate_match_score(
                    self.user_profile,
                    other_profile
                )
                reason = self.matching_engine.get_match_reason(
                    self.user_profile,
                    other_profile,
                    score
                )
                return {
                    'score': score,
                    'is_high_match': self.matching_engine.is_high_match(score),
                    'reason': reason
                }

            else:
                return {'error': f'Unknown tool: {tool_name}'}

        except Exception as e:
            return {'error': str(e)}

    def handle_new_person_nearby(self, other_user_id: str, context: Dict) -> Dict:
        """
        Handle when a new person is detected nearby

        Args:
            other_user_id: ID of the person detected
            context: Context about the detection (event, location, etc.)

        Returns:
            dict with action taken and details
        """
        # Get their profile
        other_profile = self.mcp_client.get_user_profile(other_user_id)

        if not other_profile:
            return {'action': 'skip', 'reason': 'No profile found'}

        # Calculate match score
        match_score = self.matching_engine.calculate_match_score(
            self.user_profile,
            other_profile
        )

        is_high_match = self.matching_engine.is_high_match(match_score)

        # Check permissions
        can_auto_message = self.permissions_manager.can_auto_execute(
            self.user_id,
            ActionType.SEND_MESSAGE,
            is_high_match
        )

        if can_auto_message:
            # Autonomously reach out
            return self._autonomous_outreach(other_user_id, other_profile, match_score, context)
        else:
            # Ask user for permission
            return {
                'action': 'request_permission',
                'other_user': other_profile,
                'match_score': match_score,
                'reason': self.matching_engine.get_match_reason(
                    self.user_profile,
                    other_profile,
                    match_score
                ),
                'context': context
            }

    def _autonomous_outreach(
        self,
        other_user_id: str,
        other_profile: Dict,
        match_score: float,
        context: Dict
    ) -> Dict:
        """Autonomously reach out to a high-match person"""

        # Get message templates
        templates = self.mcp_client.get_message_templates('introduction')

        # Craft personalized message using Claude
        match_reason = self.matching_engine.get_match_reason(
            self.user_profile,
            other_profile,
            match_score
        )

        prompt = f"""You're reaching out to {other_profile.get('name')} on behalf of {self.user_profile.get('name')}.

Context:
- You're both at: {context.get('event_name', 'the same event')}
- Match reason: {match_reason}
- Match score: {match_score:.0%}

{other_profile.get('name')}'s profile:
{json.dumps(other_profile, indent=2)}

Craft a brief, friendly iMessage introduction (2-3 sentences max). Be authentic and mention the specific connection point."""

        response = self.run(prompt)
        message = response.get('output', '')

        # Determine contact method
        contact_info = other_profile.get('contact', {})
        phone = contact_info.get('phone')
        email = contact_info.get('email')

        result = {}

        if phone:
            # Send iMessage
            send_result = self.imessage_tool.send_message(phone, message)
            result = {
                'action': 'sent_imessage',
                'recipient': other_profile.get('name'),
                'message': message,
                'success': send_result.get('success', False)
            }
        elif email:
            # Send email
            send_result = self.gmail_tool.send_email(
                to=email,
                subject=f"Great to connect at {context.get('event_name', 'the event')}!",
                body=message
            )
            result = {
                'action': 'sent_email',
                'recipient': other_profile.get('name'),
                'message': message,
                'success': send_result.get('success', False)
            }
        else:
            result = {
                'action': 'no_contact_method',
                'recipient': other_profile.get('name')
            }

        # Log the interaction
        self.mcp_client.log_interaction(
            self.user_id,
            other_user_id,
            'autonomous_outreach',
            {'match_score': match_score, 'context': context}
        )

        return result

    def handle_incoming_message(
        self,
        sender_id: str,
        message: str,
        conversation_id: str
    ) -> Dict:
        """
        Handle an incoming message from someone

        Args:
            sender_id: ID of the sender
            message: Message content
            conversation_id: Conversation ID

        Returns:
            dict with response and actions
        """
        # Get conversation history
        history = self.mcp_client.get_conversation_history(conversation_id)

        # Get sender profile
        sender_profile = self.mcp_client.get_user_profile(sender_id)

        # Save incoming message
        self.mcp_client.save_conversation_message(
            conversation_id,
            sender_id,
            message
        )

        # Analyze and respond using Claude
        prompt = f"""You received a message from {sender_profile.get('name', 'someone')}:

"{message}"

Conversation history:
{json.dumps(history[-5:], indent=2) if history else 'First message'}

Analyze the message and decide:
1. Should you respond, or ask {self.user_profile.get('name')} to take over?
2. If responding, what should you say?
3. Is this a good time to suggest meeting in person?
4. Any actions to take (schedule meeting, etc.)?

Respond naturally and keep building the relationship."""

        response = self.run(prompt)

        # Save outgoing response
        output = response.get('output', '')
        self.mcp_client.save_conversation_message(
            conversation_id,
            self.user_id,
            output,
            {'generated_by_agent': True}
        )

        return {
            'response': output,
            'should_notify_user': 'take over' in output.lower(),
            'conversation_id': conversation_id
        }

    def run(self, task: str, chat_history: Optional[List[Dict]] = None) -> Dict:
        """
        Run the agent with a specific task using Claude's tool calling

        Args:
            task: Task description
            chat_history: Optional conversation history

        Returns:
            dict with results
        """
        messages = []

        # Add chat history if provided
        if chat_history:
            messages.extend(chat_history)

        # Add user message
        messages.append({
            "role": "user",
            "content": task
        })

        # Call Claude with tool use
        response = self.anthropic.messages.create(
            model=Config.CLAUDE_MODEL,
            max_tokens=4096,
            system=self._get_system_prompt(),
            tools=self.tools,
            messages=messages
        )

        # Process tool uses
        while response.stop_reason == "tool_use":
            # Extract tool uses from response
            tool_results = []

            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input
                    tool_use_id = content_block.id

                    # Execute the tool
                    result = self._execute_tool(tool_name, tool_input)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(result)
                    })

            # Add assistant response and tool results to messages
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            messages.append({
                "role": "user",
                "content": tool_results
            })

            # Continue the conversation
            response = self.anthropic.messages.create(
                model=Config.CLAUDE_MODEL,
                max_tokens=4096,
                system=self._get_system_prompt(),
                tools=self.tools,
                messages=messages
            )

        # Extract final text response
        final_response = ""
        for content_block in response.content:
            if hasattr(content_block, 'text'):
                final_response += content_block.text

        return {
            "output": final_response,
            "messages": messages,
            "response": response
        }
