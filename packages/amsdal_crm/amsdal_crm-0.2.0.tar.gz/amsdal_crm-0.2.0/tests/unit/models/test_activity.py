"""Unit tests for Activity models."""

from datetime import UTC
from datetime import datetime
from unittest import mock

from amsdal_crm.models.activity import Activity
from amsdal_crm.models.activity import ActivityRelatedTo
from amsdal_crm.models.activity import ActivityType
from amsdal_crm.models.activity import Call
from amsdal_crm.models.activity import EmailActivity
from amsdal_crm.models.activity import Event
from amsdal_crm.models.activity import Note
from amsdal_crm.models.activity import Task


def test_activity_creation(unit_user):
    """Test creating a base activity."""
    activity = Activity(
        activity_type=ActivityType.NOTE,
        subject='Test Note',
        description='Test description',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id='entity_123',
    )

    assert activity.subject == 'Test Note'
    assert activity.activity_type == ActivityType.NOTE
    assert activity.related_to_type == ActivityRelatedTo.ENTITY
    assert activity.related_to_id == 'entity_123'


def test_activity_display_name(unit_user):
    """Test activity display_name property."""
    activity = Activity(
        activity_type=ActivityType.NOTE,
        subject='Meeting Notes',
        related_to_type=ActivityRelatedTo.DEAL,
        related_to_id='deal_123',
    )

    assert activity.display_name == 'note: Meeting Notes'


def test_activity_default_is_completed(unit_user):
    """Test activity has is_completed=False by default."""
    activity = Activity(
        activity_type=ActivityType.TASK,
        subject='Follow up',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id='entity_123',
    )

    assert activity.is_completed is False


def test_activity_has_object_permission_owner(unit_user):
    """Test that assigned user has permission."""
    activity = Activity(
        activity_type=ActivityType.NOTE,
        subject='Test',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id='entity_123',
    )
    object.__setattr__(activity, 'assigned_to', unit_user)

    assert activity.has_object_permission(unit_user, 'read') is True
    assert activity.has_object_permission(unit_user, 'update') is True
    assert activity.has_object_permission(unit_user, 'delete') is True


def test_activity_has_object_permission_non_owner(unit_user):
    """Test that non-assigned user doesn't have permission."""
    activity = Activity(
        activity_type=ActivityType.NOTE,
        subject='Test',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id='entity_123',
    )
    object.__setattr__(activity, 'assigned_to', unit_user)

    other_user = mock.Mock()
    other_user.email = 'other@example.com'
    other_user.permissions = []

    assert activity.has_object_permission(other_user, 'read') is False


def test_task_creation(unit_user):
    """Test creating a Task activity."""
    task = Task(
        subject='Call customer',
        description='Follow up on proposal',
        related_to_type=ActivityRelatedTo.DEAL,
        related_to_id='deal_123',
        priority='high',
        status='in_progress',
    )

    assert task.activity_type == ActivityType.TASK
    assert task.priority == 'high'
    assert task.status == 'in_progress'


def test_task_default_priority(unit_user):
    """Test task has default priority of medium."""
    task = Task(
        subject='Test Task',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id='entity_123',
    )

    assert task.priority == 'medium'


def test_task_default_status(unit_user):
    """Test task has default status of not_started."""
    task = Task(
        subject='Test Task',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id='entity_123',
    )

    assert task.status == 'not_started'


def test_event_creation(unit_user):
    """Test creating an Event activity."""
    start_time = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
    end_time = datetime(2026, 6, 1, 11, 0, tzinfo=UTC)

    event = Event(
        subject='Client Meeting',
        description='Discuss Q2 results',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id='entity_123',
        start_time=start_time,
        end_time=end_time,
        location='Conference Room A',
    )

    assert event.activity_type == ActivityType.EVENT
    assert event.start_time == start_time
    assert event.end_time == end_time
    assert event.location == 'Conference Room A'


def test_email_activity_creation(unit_user):
    """Test creating an EmailActivity."""
    email = EmailActivity(
        subject='Proposal Sent',
        description='Sent Q2 proposal',
        related_to_type=ActivityRelatedTo.DEAL,
        related_to_id='deal_123',
        from_address='sales@example.com',
        to_addresses=['client@example.com'],
        cc_addresses=['manager@example.com'],
        body='Please find attached our proposal...',
        is_outbound=True,
    )

    assert email.activity_type == ActivityType.EMAIL
    assert email.from_address == 'sales@example.com'
    assert email.to_addresses == ['client@example.com']
    assert email.cc_addresses == ['manager@example.com']
    assert email.is_outbound is True


def test_email_activity_default_is_outbound(unit_user):
    """Test email activity has is_outbound=True by default."""
    email = EmailActivity(
        subject='Test Email',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id='entity_123',
        from_address='test@example.com',
        to_addresses=['recipient@example.com'],
        body='Test body',
    )

    assert email.is_outbound is True


def test_note_creation(unit_user):
    """Test creating a Note activity."""
    note = Note(
        subject='Call Notes',
        description='Customer expressed interest in enterprise plan',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id='entity_123',
    )

    assert note.activity_type == ActivityType.NOTE
    assert note.subject == 'Call Notes'


def test_call_creation(unit_user):
    """Test creating a Call activity."""
    call = Call(
        subject='Discovery Call',
        description='Initial discussion about needs',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id='entity_123',
        phone_number='+1234567890',
        duration_seconds=1800,  # 30 minutes
        call_outcome='Interested in enterprise plan',
    )

    assert call.activity_type == ActivityType.CALL
    assert call.phone_number == '+1234567890'
    assert call.duration_seconds == 1800
    assert call.call_outcome == 'Interested in enterprise plan'


def test_activity_polymorphic_relationships(unit_user):
    """Test activity can link to different entity types."""
    # Entity activity
    entity_activity = Note(
        subject='Entity Note',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id='entity_123',
    )
    assert entity_activity.related_to_type == ActivityRelatedTo.ENTITY

    # Deal activity
    deal_activity = Note(
        subject='Deal Note',
        related_to_type=ActivityRelatedTo.DEAL,
        related_to_id='deal_123',
    )
    assert deal_activity.related_to_type == ActivityRelatedTo.DEAL
