"""
Gmail Tool for sending emails and managing calendar.
"""
import os
import logging
from datetime import datetime
from typing import Optional, List

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from mcp_gmail.config import settings
from mcp_gmail.gmail import (
    create_draft,
    get_gmail_service,
    get_headers_dict,
    get_labels,
    get_message,
    get_thread,
    list_messages,
    modify_message_labels,
    parse_message_body,
    search_messages,
    send_email as gmail_send_email
)

logger = logging.getLogger(__name__)

EMAIL_PREVIEW_LENGTH = 200


class GmailTool:
    """Tool for Gmail email and calendar operations"""

    def __init__(self):
        """
        Initialize Gmail tool and build Gmail & Calendar services.
        """
        try:
            self.service = get_gmail_service(
                credentials_path=settings.credentials_path,
                token_path=settings.token_path,
                scopes=settings.scopes
            )
            self.calendar_service = build("calendar", "v3", credentials=self.service._http.credentials)
            logger.info("Gmail and Calendar services initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize GmailTool: {e}")
            raise RuntimeError(f"Failed to initialize GmailTool: {e}") from e

    # ---------- Helper Methods ----------

    def _format_message(self, message) -> str:
        """Format a Gmail message for display."""
        headers = get_headers_dict(message)
        body = parse_message_body(message)

        from_header = headers.get("From", "Unknown")
        to_header = headers.get("To", "Unknown")
        subject = headers.get("Subject", "No Subject")
        date = headers.get("Date", "Unknown Date")

        return f"""
From: {from_header}
To: {to_header}
Subject: {subject}
Date: {date}

{body}
"""

    def _validate_date_format(self, date_str: Optional[str]) -> bool:
        """Validate date string format YYYY/MM/DD."""
        if not date_str:
            return True
        try:
            datetime.strptime(date_str, "%Y/%m/%d")
            return True
        except ValueError:
            return False

    # ---------- Email Methods ----------

    def get_email_message(self, message_id: str) -> str:
        """Get the content of an email message by its ID."""
        message = get_message(self.service, message_id, user_id=settings.user_id)
        return self._format_message(message)

    def get_emails(self, message_ids: List[str]) -> str:
        """Get content of multiple email messages by IDs."""
        if not message_ids:
            return "No message IDs provided."

        retrieved = []
        errors = []

        for msg_id in message_ids:
            try:
                message = get_message(self.service, msg_id, user_id=settings.user_id)
                retrieved.append((msg_id, message))
            except Exception as e:
                errors.append((msg_id, str(e)))

        result = f"Retrieved {len(retrieved)} emails:\n"
        for i, (msg_id, message) in enumerate(retrieved, 1):
            result += f"\n--- Email {i} (ID: {msg_id}) ---\n"
            result += self._format_message(message)

        if errors:
            result += f"\n\nFailed to retrieve {len(errors)} emails:\n"
            for i, (msg_id, error) in enumerate(errors, 1):
                result += f"\n--- Email {i} (ID: {msg_id}) ---\nError: {error}\n"

        return result

    def get_email_thread(self, thread_id: str) -> str:
        """Get all messages in an email thread."""
        thread = get_thread(self.service, thread_id, user_id=settings.user_id)
        messages = thread.get("messages", [])

        result = f"Email Thread (ID: {thread_id})\n"
        for i, message in enumerate(messages, 1):
            result += f"\n--- Message {i} ---\n"
            result += self._format_message(message)
        return result

    def compose_email(
        self, to: str, subject: str, body: str, cc: Optional[str] = None, bcc: Optional[str] = None
    ) -> str:
        """Compose a new email draft."""
        sender = self.service.users().getProfile(userId=settings.user_id).execute().get("emailAddress")
        draft = create_draft(
            self.service,
            sender=sender,
            to=to,
            subject=subject,
            body=body,
            user_id=settings.user_id,
            cc=cc,
            bcc=bcc
        )
        draft_id = draft.get("id")
        return f"""
Email draft created with ID: {draft_id}
To: {to}
Subject: {subject}
CC: {cc or ""}
BCC: {bcc or ""}
Body: {body[:EMAIL_PREVIEW_LENGTH]}{"..." if len(body) > EMAIL_PREVIEW_LENGTH else ""}
"""

    def send_email(
        self, to: str, subject: str, body: str, cc: Optional[str] = None, bcc: Optional[str] = None
    ) -> str:
        """Send an email via Gmail."""
        sender = self.service.users().getProfile(userId=settings.user_id).execute().get("emailAddress")
        message = gmail_send_email(
            self.service,
            sender=sender,
            to=to,
            subject=subject,
            body=body,
            user_id=settings.user_id,
            cc=cc,
            bcc=bcc
        )
        message_id = message.get("id")
        return f"""
Email sent successfully with ID: {message_id}
To: {to}
Subject: {subject}
CC: {cc or ""}
BCC: {bcc or ""}
Body: {body[:EMAIL_PREVIEW_LENGTH]}{"..." if len(body) > EMAIL_PREVIEW_LENGTH else ""}
"""

    def search_emails(
        self,
        from_email: Optional[str] = None,
        to_email: Optional[str] = None,
        subject: Optional[str] = None,
        has_attachment: bool = False,
        is_unread: bool = False,
        after_date: Optional[str] = None,
        before_date: Optional[str] = None,
        label: Optional[str] = None,
        max_results: int = 10,
    ) -> str:
        """Search emails with filters."""
        if after_date and not self._validate_date_format(after_date):
            return f"Error: after_date '{after_date}' is not valid"
        if before_date and not self._validate_date_format(before_date):
            return f"Error: before_date '{before_date}' is not valid"

        messages = search_messages(
            self.service,
            user_id=settings.user_id,
            from_email=from_email,
            to_email=to_email,
            subject=subject,
            has_attachment=has_attachment,
            is_unread=is_unread,
            after=after_date,
            before=before_date,
            labels=[label] if label else None,
            max_results=max_results
        )

        result = f"Found {len(messages)} messages matching criteria:\n"
        for msg_info in messages:
            msg_id = msg_info.get("id")
            message = get_message(self.service, msg_id, user_id=settings.user_id)
            headers = get_headers_dict(message)
            from_header = headers.get("From", "Unknown")
            subject_header = headers.get("Subject", "No Subject")
            date = headers.get("Date", "Unknown Date")
            result += f"\nMessage ID: {msg_id}\nFrom: {from_header}\nSubject: {subject_header}\nDate: {date}\n"
        return result

    def query_emails(self, query: str, max_results: int = 10) -> str:
        """Search emails using a raw Gmail query string."""
        messages = list_messages(self.service, user_id=settings.user_id, max_results=max_results, query=query)
        result = f'Found {len(messages)} messages matching query: "{query}"\n'
        for msg_info in messages:
            msg_id = msg_info.get("id")
            message = get_message(self.service, msg_id, user_id=settings.user_id)
            headers = get_headers_dict(message)
            from_header = headers.get("From", "Unknown")
            subject_header = headers.get("Subject", "No Subject")
            date = headers.get("Date", "Unknown Date")
            result += f"\nMessage ID: {msg_id}\nFrom: {from_header}\nSubject: {subject_header}\nDate: {date}\n"
        return result

    def list_available_labels(self) -> str:
        """Get all Gmail labels for the user."""
        labels = get_labels(self.service, user_id=settings.user_id)
        result = "Available Gmail Labels:\n"
        for label in labels:
            label_id = label.get("id", "Unknown")
            name = label.get("name", "Unknown")
            type_info = label.get("type", "user")
            result += f"\nLabel ID: {label_id}\nName: {name}\nType: {type_info}\n"
        return result

    def mark_message_read(self, message_id: str) -> str:
        """Mark a message as read by removing UNREAD label."""
        result = modify_message_labels(
            self.service, user_id=settings.user_id, message_id=message_id, remove_labels=["UNREAD"], add_labels=[]
        )
        headers = get_headers_dict(result)
        subject = headers.get("Subject", "No Subject")
        return f"Message marked as read:\nID: {message_id}\nSubject: {subject}"

    def add_label_to_message(self, message_id: str, label_id: str) -> str:
        """Add a label to a message."""
        modify_message_labels(self.service, user_id=settings.user_id, message_id=message_id, remove_labels=[], add_labels=[label_id])
        labels = get_labels(self.service, user_id=settings.user_id)
        label_name = next((l.get("name") for l in labels if l.get("id") == label_id), label_id)
        headers = get_headers_dict(get_message(self.service, message_id, user_id=settings.user_id))
        subject = headers.get("Subject", "No Subject")
        return f"Label added to message:\nID: {message_id}\nSubject: {subject}\nAdded Label: {label_name} ({label_id})"

    def remove_label_from_message(self, message_id: str, label_id: str) -> str:
        """Remove a label from a message."""
        labels = get_labels(self.service, user_id=settings.user_id)
        label_name = next((l.get("name") for l in labels if l.get("id") == label_id), label_id)
        modify_message_labels(self.service, user_id=settings.user_id, message_id=message_id, remove_labels=[label_id], add_labels=[])
        headers = get_headers_dict(get_message(self.service, message_id, user_id=settings.user_id))
        subject = headers.get("Subject", "No Subject")
        return f"Label removed from message:\nID: {message_id}\nSubject: {subject}\nRemoved Label: {label_name} ({label_id})"

    # ---------- Calendar Methods ----------

    def get_calendar_event(self, event_id: str, calendar_id: str = "primary") -> str:
        """Fetch a single Google Calendar event by ID."""
        try:
            event = self.calendar_service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            return f"Event ID: {event_id}\nSummary: {event.get('summary')}\nStart: {event['start']}\nEnd: {event['end']}"
        except Exception as e:
            return f"Error retrieving event: {e}"

    def list_calendars(self) -> str:
        """List all calendars for the user."""
        calendars = self.calendar_service.calendarList().list().execute().get("items", [])
        return "\n".join([f"- {cal.get('summary')} (ID: {cal.get('id')})" for cal in calendars])

    def create_event(self, summary: str, start: str, end: str, description: Optional[str] = None, calendar_id: str = "primary") -> str:
        """Create a calendar event."""
        event_data = {"summary": summary, "description": description, "start": {"dateTime": start}, "end": {"dateTime": end}}
        event = self.calendar_service.events().insert(calendarId=calendar_id, body=event_data).execute()
        return f"Event created:\nID: {event['id']}\nSummary: {summary}"

    def update_event(self, event_id: str, summary: Optional[str] = None, description: Optional[str] = None, start: Optional[str] = None, end: Optional[str] = None, calendar_id: str = "primary") -> str:
        """Update an existing event."""
        event = self.calendar_service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        if summary: event["summary"] = summary
        if description: event["description"] = description
        if start: event["start"] = {"dateTime": start}
        if end: event["end"] = {"dateTime": end}
        updated = self.calendar_service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
        return f"Event updated: {updated['id']}"

    def delete_event(self, event_id: str, calendar_id: str = "primary") -> str:
        """Delete a calendar event."""
        self.calendar_service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return f"Event {event_id} deleted."

    def quick_add_event(self, text: str, calendar_id: str = "primary") -> str:
        """Quick add a calendar event using natural language."""
        event = self.calendar_service.events().quickAdd(calendarId=calendar_id, text=text).execute()
        return f"Quick-created event:\nID: {event['id']}\nSummary: {event.get('summary')}"
