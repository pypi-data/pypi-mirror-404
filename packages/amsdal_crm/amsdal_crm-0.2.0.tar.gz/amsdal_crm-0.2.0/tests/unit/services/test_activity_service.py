"""Unit tests for ActivityService."""

from datetime import UTC
from datetime import datetime
from unittest import mock

import pytest

from amsdal_crm.models.activity import Activity
from amsdal_crm.models.activity import ActivityRelatedTo
from amsdal_crm.models.activity import Note
from amsdal_crm.models.activity import Task
from amsdal_crm.services.activity_service import ActivityService


def test_get_timeline_entity(unit_user):
    """Test getting activity timeline for an entity."""
    entity_id = 'entity_123'

    # Create mock activities
    activity1 = Note(
        subject='Meeting notes',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id=entity_id,
    )
    activity1.created_at = datetime(2026, 1, 5, tzinfo=UTC)

    activity2 = Task(
        subject='Follow up',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id=entity_id,
    )
    activity2.created_at = datetime(2026, 1, 10, tzinfo=UTC)

    with mock.patch.object(Activity.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.order_by.return_value = mock_chain
        mock_chain.execute.return_value = [activity2, activity1]  # Newest first
        mock_filter.return_value = mock_chain

        activities = ActivityService.get_timeline(ActivityRelatedTo.ENTITY, entity_id)

        assert len(activities) == 2
        assert activities[0].subject == 'Follow up'
        assert activities[1].subject == 'Meeting notes'
        # Verify correct filtering and ordering
        mock_chain.order_by.assert_called_once_with('-created_at')


def test_get_timeline_deal(unit_user):
    """Test getting activity timeline for a deal."""
    deal_id = 'deal_789'

    activity = Note(
        subject='Deal update',
        related_to_type=ActivityRelatedTo.DEAL,
        related_to_id=deal_id,
    )

    with mock.patch.object(Activity.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.order_by.return_value = mock_chain
        mock_chain.execute.return_value = [activity]
        mock_filter.return_value = mock_chain

        activities = ActivityService.get_timeline(ActivityRelatedTo.DEAL, deal_id)

        assert len(activities) == 1
        assert activities[0].subject == 'Deal update'


def test_get_timeline_empty(unit_user):
    """Test getting timeline when there are no activities."""
    entity_id = 'entity_999'

    with mock.patch.object(Activity.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.order_by.return_value = mock_chain
        mock_chain.execute.return_value = []
        mock_filter.return_value = mock_chain

        activities = ActivityService.get_timeline(ActivityRelatedTo.ENTITY, entity_id)

        assert activities == []


def test_get_timeline_respects_limit(unit_user):
    """Test that timeline respects limit parameter."""
    entity_id = 'entity_123'

    # Create 5 mock activities
    activities = []
    for i in range(5):
        activity = Note(
            subject=f'Note {i}',
            related_to_type=ActivityRelatedTo.ENTITY,
            related_to_id=entity_id,
        )
        activity.created_at = datetime(2026, 1, i + 1, tzinfo=UTC)
        activities.append(activity)

    with mock.patch.object(Activity.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.order_by.return_value = mock_chain
        mock_chain.execute.return_value = activities  # Return all 5
        mock_filter.return_value = mock_chain

        result = ActivityService.get_timeline(ActivityRelatedTo.ENTITY, entity_id, limit=3)

        # Verify only 3 were returned (sliced)
        assert len(result) == 3


def test_get_timeline_default_limit(unit_user):
    """Test that timeline uses default limit of 100."""
    entity_id = 'entity_123'

    # Create 120 mock activities (more than default limit)
    activities = []
    for i in range(120):
        activity = Note(
            subject=f'Note {i}',
            related_to_type=ActivityRelatedTo.ENTITY,
            related_to_id=entity_id,
        )
        activities.append(activity)

    with mock.patch.object(Activity.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.order_by.return_value = mock_chain
        mock_chain.execute.return_value = activities
        mock_filter.return_value = mock_chain

        result = ActivityService.get_timeline(ActivityRelatedTo.ENTITY, entity_id)

        # Verify default limit of 100 was applied
        assert len(result) == 100


def test_get_timeline_ordered_by_date(unit_user):
    """Test that timeline is ordered by created_at desc."""
    entity_id = 'entity_123'

    # Create activities with different timestamps
    old_activity = Note(
        subject='Old note',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id=entity_id,
    )
    old_activity.created_at = datetime(2026, 1, 1, tzinfo=UTC)

    new_activity = Note(
        subject='New note',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id=entity_id,
    )
    new_activity.created_at = datetime(2026, 1, 10, tzinfo=UTC)

    middle_activity = Note(
        subject='Middle note',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id=entity_id,
    )
    middle_activity.created_at = datetime(2026, 1, 5, tzinfo=UTC)

    with mock.patch.object(Activity.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.order_by.return_value = mock_chain
        # Returned in desc order
        mock_chain.execute.return_value = [new_activity, middle_activity, old_activity]
        mock_filter.return_value = mock_chain

        activities = ActivityService.get_timeline(ActivityRelatedTo.ENTITY, entity_id)

        # Verify order: newest first
        assert activities[0].subject == 'New note'
        assert activities[1].subject == 'Middle note'
        assert activities[2].subject == 'Old note'


def test_get_timeline_filters_by_latest_version(unit_user):
    """Test that timeline filters by latest version."""
    entity_id = 'entity_123'

    with mock.patch.object(Activity.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.order_by.return_value = mock_chain
        mock_chain.execute.return_value = []
        mock_filter.return_value = mock_chain

        ActivityService.get_timeline(ActivityRelatedTo.ENTITY, entity_id)

        # Verify filter was called with correct arguments
        mock_filter.assert_called_once()
        call_kwargs = mock_filter.call_args[1]
        assert call_kwargs['related_to_type'] == ActivityRelatedTo.ENTITY
        assert call_kwargs['related_to_id'] == entity_id
        assert '_address__object_version' in call_kwargs


@pytest.mark.asyncio
async def test_aget_timeline_async(unit_user):
    """Test async version of get_timeline."""
    entity_id = 'entity_123'

    activity = Note(
        subject='Async note',
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id=entity_id,
    )

    with mock.patch.object(Activity.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.order_by.return_value = mock_chain

        # Mock async execute
        async def async_execute():
            return [activity]

        mock_chain.aexecute = async_execute
        mock_filter.return_value = mock_chain

        activities = await ActivityService.aget_timeline(ActivityRelatedTo.ENTITY, entity_id)

        assert len(activities) == 1
        assert activities[0].subject == 'Async note'


@pytest.mark.asyncio
async def test_aget_timeline_with_limit(unit_user):
    """Test async timeline with custom limit."""
    entity_id = 'entity_123'

    activities = []
    for i in range(5):
        activity = Note(
            subject=f'Async note {i}',
            related_to_type=ActivityRelatedTo.ENTITY,
            related_to_id=entity_id,
        )
        activities.append(activity)

    with mock.patch.object(Activity.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.order_by.return_value = mock_chain

        # Mock async execute - return all 5 activities
        async def async_execute():
            return activities

        mock_chain.aexecute = async_execute
        mock_filter.return_value = mock_chain

        result = await ActivityService.aget_timeline(ActivityRelatedTo.ENTITY, entity_id, limit=2)

        # Verify only 2 were returned (sliced)
        assert len(result) == 2
