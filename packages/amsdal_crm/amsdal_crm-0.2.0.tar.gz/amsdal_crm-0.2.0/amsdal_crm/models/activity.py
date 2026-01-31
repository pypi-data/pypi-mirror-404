"""Activity Models."""

from datetime import datetime
from enum import Enum
from typing import ClassVar
from typing import Literal

from amsdal.contrib.auth.models.user import User
from amsdal.models.mixins import TimestampMixin
from amsdal_models.classes.data_models.indexes import IndexInfo
from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class ActivityType(str, Enum):
    """Activity type enumeration."""

    TASK = 'task'
    EVENT = 'event'
    EMAIL = 'email'
    NOTE = 'note'
    CALL = 'call'


class ActivityRelatedTo(str, Enum):
    """What type of record this activity is related to."""

    ENTITY = 'Entity'
    DEAL = 'Deal'


class Activity(TimestampMixin, Model):
    """Base activity model with polymorphic related_to field.

    Activities can be linked to Contacts, Accounts, or Deals using
    a generic foreign key pattern (related_to_type + related_to_id).
    """

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    __indexes__: ClassVar[list[IndexInfo]] = [
        IndexInfo(name='idx_activity_related_to', field='related_to_id'),
        IndexInfo(name='idx_activity_created_at', field='created_at'),
        IndexInfo(name='idx_activity_due_date', field='due_date'),
    ]

    # Discriminator
    activity_type: ActivityType = Field(title='Activity Type')

    # Core fields
    subject: str = Field(title='Subject')
    description: str | None = Field(default=None, title='Description')

    # Polymorphic relationship (generic FK pattern)
    related_to_type: ActivityRelatedTo | None = Field(title='Related To Type')
    related_to_id: str | None = Field(title='Related To ID')

    assigned_to: User | None = Field(default=None, title='Assigned To')
    # Timing
    due_date: datetime | None = Field(default=None, title='Due Date')
    completed_at: datetime | None = Field(default=None, title='Completed At')

    # Status
    is_completed: bool = Field(default=False, title='Is Completed')

    @property
    def display_name(self) -> str:
        """Return display name for the activity."""
        return f'{self.activity_type.value}: {self.subject}'

    def has_object_permission(self, user: 'User', action: str) -> bool:
        """Check if user has permission to perform action on this activity.

        Args:
            user: The user attempting the action
            action: The action being attempted (read, create, update, delete)

        Returns:
            True if user has permission, False otherwise
        """
        # Owner has all permissions
        if self.assigned_to and self.assigned_to.email == user.email:
            return True

        # Check admin permissions
        if user.permissions:
            for permission in user.permissions:
                if permission.model == '*' and permission.action in ('*', action):
                    return True
                if permission.model == 'Activity' and permission.action in ('*', action):
                    return True

        return False


class Task(Activity):
    """Task activity with priority and status."""

    activity_type: Literal[ActivityType.TASK] = Field(ActivityType.TASK, title='Activity Type')
    priority: Literal['low', 'medium', 'high'] = Field('medium', title='Priority')
    status: Literal['not_started', 'in_progress', 'waiting', 'completed'] = Field('not_started', title='Status')


class Event(Activity):
    """Event/meeting activity with start/end times."""

    activity_type: Literal[ActivityType.EVENT] = Field(ActivityType.EVENT, title='Activity Type')
    start_time: datetime = Field(title='Start Time')
    end_time: datetime = Field(title='End Time')
    location: str | None = Field(None, title='Location')


class EmailActivity(Activity):
    """Email activity with sender/recipients."""

    activity_type: Literal[ActivityType.EMAIL] = Field(ActivityType.EMAIL, title='Activity Type')
    from_address: str = Field(title='From Address')
    to_addresses: list[str] = Field(title='To Addresses')
    cc_addresses: list[str] | None = Field(None, title='CC Addresses')
    body: str = Field(title='Email Body')
    is_outbound: bool = Field(True, title='Is Outbound')


class Note(Activity):
    """Simple note activity."""

    activity_type: Literal[ActivityType.NOTE] = Field(ActivityType.NOTE, title='Activity Type')


class Call(Activity):
    """Phone call activity."""

    activity_type: Literal[ActivityType.CALL] = Field(ActivityType.CALL, title='Activity Type')
    phone_number: str = Field(title='Phone Number')
    duration_seconds: int | None = Field(None, title='Duration (seconds)')
    call_outcome: str | None = Field(None, title='Call Outcome')
