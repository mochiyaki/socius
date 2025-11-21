"""
Gmail Tool for sending emails and managing calendar.
"""
import os
import pickle
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
import base64
from datetime import datetime, timedelta
from typing import Optional, List

from config import Config
from socius_types import EmailSendResponse, CalendarEventResponse, BusyTimeSlot
from exceptions import GmailAuthError, GmailSendError, CalendarAuthError, CalendarEventError

logger = logging.getLogger(__name__)

# Scopes for Gmail and Calendar access
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar'
]


class GmailTool:
    """Tool for Gmail email and calendar operations"""

    def __init__(self):
        """
        Initialize Gmail tool and authenticate with Google API.

        Raises:
            GmailAuthError: If authentication fails
            CalendarAuthError: If calendar service initialization fails
        """
        self.creds = None
        self.gmail_service = None
        self.calendar_service = None
        self._authenticate()

    def _authenticate(self) -> None:
        """
        Authenticate with Google API.

        Raises:
            GmailAuthError: If authentication fails
        """
        try:
            # Check if token exists
            if os.path.exists(Config.GMAIL_TOKEN_PATH):
                with open(Config.GMAIL_TOKEN_PATH, 'rb') as token:
                    self.creds = pickle.load(token)

            # If no valid credentials, let user log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(Config.GMAIL_CREDENTIALS_PATH):
                        raise GmailAuthError(
                            f"Gmail credentials not found at {Config.GMAIL_CREDENTIALS_PATH}"
                        )

                    flow = InstalledAppFlow.from_client_secrets_file(
                        Config.GMAIL_CREDENTIALS_PATH, SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)

                # Save credentials for next run
                os.makedirs(os.path.dirname(Config.GMAIL_TOKEN_PATH), exist_ok=True)
                with open(Config.GMAIL_TOKEN_PATH, 'wb') as token:
                    pickle.dump(self.creds, token)

            # Build services
            self.gmail_service = build('gmail', 'v1', credentials=self.creds)
            self.calendar_service = build('calendar', 'v3', credentials=self.creds)

            logger.info("Successfully authenticated with Gmail and Calendar APIs")

        except FileNotFoundError as e:
            raise GmailAuthError(f"Credentials file not found: {e}") from e
        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            raise GmailAuthError(f"Failed to authenticate with Gmail: {e}") from e

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> EmailSendResponse:
        """
        Send an email via Gmail.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            html: Whether body is HTML (default False for plain text)

        Returns:
            Response dict with success status and message ID

        Raises:
            GmailSendError: If email sending fails
        """
        try:
            message = MIMEText(body, 'html' if html else 'plain')
            message['to'] = to
            message['subject'] = subject

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            message_body = {'raw': raw}

            result = self.gmail_service.users().messages().send(
                userId='me',
                body=message_body
            ).execute()

            logger.info(f"Successfully sent email to {to}")

            return {
                'success': True,
                'message_id': result['id'],
                'recipient': to,
                'error': None
            }

        except HttpError as error:
            logger.error(f"Gmail API error sending email: {error}")
            raise GmailSendError(f"Gmail API error: {error}") from error

        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            raise GmailSendError(f"Failed to send email: {e}") from e

    def create_calendar_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        attendees: List[str],
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> CalendarEventResponse:
        """
        Create a calendar event.

        Args:
            summary: Event title
            start_time: Event start datetime
            end_time: Event end datetime
            attendees: List of attendee email addresses
            description: Optional event description
            location: Optional event location

        Returns:
            Response dict with success status and event details

        Raises:
            CalendarEventError: If event creation fails
        """
        try:
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': [{'email': email} for email in attendees],
            }

            if description:
                event['description'] = description

            if location:
                event['location'] = location

            result = self.calendar_service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'
            ).execute()

            logger.info(f"Successfully created calendar event: {summary}")

            return {
                'success': True,
                'event_id': result['id'],
                'event_link': result.get('htmlLink'),
                'attendees': attendees,
                'error': None
            }

        except HttpError as error:
            logger.error(f"Calendar API error creating event: {error}")
            raise CalendarEventError(f"Calendar API error: {error}") from error

        except Exception as e:
            logger.error(f"Unexpected error creating event: {e}")
            raise CalendarEventError(f"Failed to create event: {e}") from e

    def get_availability(
        self,
        start_date: datetime,
        end_date: datetime,
        calendar_id: str = 'primary'
    ) -> List[BusyTimeSlot]:
        """
        Get busy times in the specified date range.

        Args:
            start_date: Start of range to check
            end_date: End of range to check
            calendar_id: Calendar to check (default 'primary')

        Returns:
            List of busy time slots

        Raises:
            CalendarEventError: If availability check fails
        """
        try:
            body = {
                "timeMin": start_date.isoformat() + 'Z',
                "timeMax": end_date.isoformat() + 'Z',
                "items": [{"id": calendar_id}]
            }

            events_result = self.calendar_service.freebusy().query(body=body).execute()
            cal_busy = events_result['calendars'][calendar_id]['busy']

            return cal_busy

        except HttpError as error:
            logger.error(f"Calendar API error checking availability: {error}")
            raise CalendarEventError(f"Failed to check availability: {error}") from error

        except KeyError as e:
            logger.error(f"Unexpected response format: {e}")
            return []

    def find_free_slot(
        self,
        duration_minutes: int = 30,
        days_ahead: int = 7
    ) -> Optional[datetime]:
        """
        Find the next available free time slot.

        Args:
            duration_minutes: Required meeting duration in minutes
            days_ahead: How many days ahead to search

        Returns:
            datetime of the next free slot, or None if not found

        Raises:
            CalendarEventError: If availability check fails
        """
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)

        busy_times = self.get_availability(start_date, end_date)

        # Simple algorithm: find gaps between busy times
        current_time = start_date

        for busy_slot in busy_times:
            try:
                slot_start = datetime.fromisoformat(busy_slot['start'].replace('Z', '+00:00'))
                if (slot_start - current_time).total_seconds() >= duration_minutes * 60:
                    return current_time
                current_time = datetime.fromisoformat(busy_slot['end'].replace('Z', '+00:00'))
            except (KeyError, ValueError) as e:
                logger.warning(f"Invalid busy slot format: {e}")
                continue

        # Check if there's time after the last busy slot
        if (end_date - current_time).total_seconds() >= duration_minutes * 60:
            return current_time

        return None
