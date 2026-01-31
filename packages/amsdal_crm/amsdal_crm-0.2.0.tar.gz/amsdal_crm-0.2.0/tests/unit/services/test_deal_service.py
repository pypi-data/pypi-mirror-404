"""Unit tests for DealService."""

from unittest import mock
from unittest.mock import AsyncMock

import pytest

from amsdal_crm.constants import CRMLifecycleEvent
from amsdal_crm.models.activity import ActivityRelatedTo
from amsdal_crm.models.activity import Note
from amsdal_crm.models.deal import Deal
from amsdal_crm.models.entity import Entity
from amsdal_crm.models.pipeline import Pipeline
from amsdal_crm.models.stage import Stage
from amsdal_crm.services.deal_service import DealService


def test_move_deal_to_stage(unit_user):
    """Test moving a deal to a new stage."""
    # Create pipeline
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    entity = Entity(name='Test Entity')

    # Create old and new stages
    old_stage = Stage(
        pipeline=pipeline,
        name='Qualified',
        order=1,
        probability=25.0,
    )

    new_stage = Stage(
        pipeline=pipeline,
        name='Proposal',
        order=3,
        probability=50.0,
    )
    new_stage._object_id = 'stage_456'

    # Create deal
    deal = Deal(
        name='Test Deal',
        stage=old_stage,
        entity=entity,
        amount=10000.0,
    )
    deal._object_id = 'deal_123'

    with mock.patch.object(Stage.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.get.return_value = mock_chain
        mock_chain.execute.return_value = new_stage
        mock_filter.return_value = mock_chain

        with mock.patch.object(Deal, 'save'):
            with mock.patch.object(Note, 'save'):
                with mock.patch('amsdal_crm.services.deal_service.LifecycleProducer') as mock_producer:
                    updated_deal = DealService.move_deal_to_stage(
                        deal=deal, new_stage_id='stage_456', note=None, user_email=unit_user.email
                    )

                    # Verify deal stage was updated
                    assert updated_deal.stage == new_stage

                    # Verify lifecycle event was emitted
                    mock_producer.publish.assert_any_call(
                        CRMLifecycleEvent.ON_DEAL_STAGE_CHANGE,
                        deal=deal,
                        old_stage='Qualified',
                        new_stage='Proposal',
                        user_email=unit_user.email,
                    )


def test_move_deal_to_stage_creates_activity(unit_user):
    """Test that moving a deal creates an activity log entry."""
    # Create pipeline
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    entity = Entity(name='Test Entity')

    old_stage = Stage(
        pipeline=pipeline,
        name='Lead',
        order=1,
        probability=10.0,
    )

    new_stage = Stage(
        pipeline=pipeline,
        name='Qualified',
        order=2,
        probability=25.0,
    )
    new_stage._object_id = 'stage_123'

    deal = Deal(name='Test Deal', stage=old_stage, entity=entity)
    deal._object_id = 'deal_789'

    with mock.patch.object(Stage.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.get.return_value = mock_chain
        mock_chain.execute.return_value = new_stage
        mock_filter.return_value = mock_chain

        # Capture Note instances as they're created
        created_notes = []
        original_init = Note.__init__

        def capture_init(self, **kwargs):
            original_init(self, **kwargs)
            created_notes.append(self)

        with mock.patch.object(Deal, 'save'):
            with mock.patch.object(Note, '__init__', capture_init):
                with mock.patch.object(Note, 'save'):
                    with mock.patch('amsdal_crm.services.deal_service.LifecycleProducer'):
                        DealService.move_deal_to_stage(
                            deal=deal, new_stage_id='stage_123', note=None, user_email=unit_user.email
                        )

                        # Verify Note was created with correct attributes
                        assert len(created_notes) == 1
                        note = created_notes[0]
                        assert note.subject == 'Deal moved: Lead → Qualified'
                        assert note.related_to_type == ActivityRelatedTo.DEAL
                        assert note.related_to_id == 'deal_789'


def test_move_deal_to_stage_with_custom_note(unit_user):
    """Test moving a deal with a custom note."""
    # Create pipeline
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    entity = Entity(name='Test Entity')

    old_stage = Stage(
        pipeline=pipeline,
        name='Proposal',
        order=3,
        probability=50.0,
    )

    new_stage = Stage(
        pipeline=pipeline,
        name='Negotiation',
        order=4,
        probability=75.0,
    )
    new_stage._object_id = 'stage_999'

    deal = Deal(name='Test Deal', stage=old_stage, entity=entity)
    deal._object_id = 'deal_555'

    custom_note = 'Client agreed to pricing, moving to final negotiations'

    with mock.patch.object(Stage.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.get.return_value = mock_chain
        mock_chain.execute.return_value = new_stage
        mock_filter.return_value = mock_chain

        # Capture Note instances as they're created
        created_notes = []
        original_init = Note.__init__

        def capture_init(self, **kwargs):
            original_init(self, **kwargs)
            created_notes.append(self)

        with mock.patch.object(Deal, 'save'):
            with mock.patch.object(Note, '__init__', capture_init):
                with mock.patch.object(Note, 'save'):
                    with mock.patch('amsdal_crm.services.deal_service.LifecycleProducer'):
                        DealService.move_deal_to_stage(
                            deal=deal, new_stage_id='stage_999', note=custom_note, user_email=unit_user.email
                        )

                        # Verify custom note was used
                        assert len(created_notes) == 1
                        note = created_notes[0]
                        assert note.description == custom_note


def test_move_deal_to_closed_won_emits_event(unit_user):
    """Test that moving to closed won stage emits ON_DEAL_WON event."""
    # Create pipeline
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    entity = Entity(name='Test Entity')

    old_stage = Stage(
        pipeline=pipeline,
        name='Negotiation',
        order=4,
        probability=75.0,
    )

    new_stage = Stage(
        pipeline=pipeline,
        name='Closed Won',
        order=5,
        probability=100.0,
        status='closed_won',
    )
    new_stage._object_id = 'stage_won'

    deal = Deal(name='Won Deal', stage=old_stage, entity=entity)
    deal._object_id = 'deal_won_123'

    with mock.patch.object(Stage.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.get.return_value = mock_chain
        mock_chain.execute.return_value = new_stage
        mock_filter.return_value = mock_chain

        with mock.patch.object(Deal, 'save'):
            with mock.patch.object(Note, 'save'):
                with mock.patch('amsdal_crm.services.deal_service.LifecycleProducer') as mock_producer:
                    DealService.move_deal_to_stage(
                        deal=deal, new_stage_id='stage_won', note=None, user_email=unit_user.email
                    )

                    # Verify ON_DEAL_STAGE_CHANGE was emitted
                    mock_producer.publish.assert_any_call(
                        CRMLifecycleEvent.ON_DEAL_STAGE_CHANGE,
                        deal=deal,
                        old_stage='Negotiation',
                        new_stage='Closed Won',
                        user_email=unit_user.email,
                    )

                    # Verify ON_DEAL_WON was emitted
                    mock_producer.publish.assert_any_call(
                        CRMLifecycleEvent.ON_DEAL_WON, deal=deal, user_email=unit_user.email
                    )


def test_move_deal_to_closed_lost_emits_event(unit_user):
    """Test that moving to closed lost stage emits ON_DEAL_LOST event."""
    # Create pipeline
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    entity = Entity(name='Test Entity')

    old_stage = Stage(
        pipeline=pipeline,
        name='Negotiation',
        order=4,
        probability=75.0,
    )

    new_stage = Stage(
        pipeline=pipeline,
        name='Closed Lost',
        order=6,
        probability=0.0,
        status='closed_lost',
    )
    new_stage._object_id = 'stage_lost'

    deal = Deal(name='Lost Deal', stage=old_stage, entity=entity)
    deal._object_id = 'deal_lost_456'

    with mock.patch.object(Stage.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.get.return_value = mock_chain
        mock_chain.execute.return_value = new_stage
        mock_filter.return_value = mock_chain

        with mock.patch.object(Deal, 'save'):
            with mock.patch.object(Note, 'save'):
                with mock.patch('amsdal_crm.services.deal_service.LifecycleProducer') as mock_producer:
                    DealService.move_deal_to_stage(
                        deal=deal, new_stage_id='stage_lost', note=None, user_email=unit_user.email
                    )

                    # Verify ON_DEAL_STAGE_CHANGE was emitted
                    mock_producer.publish.assert_any_call(
                        CRMLifecycleEvent.ON_DEAL_STAGE_CHANGE,
                        deal=deal,
                        old_stage='Negotiation',
                        new_stage='Closed Lost',
                        user_email=unit_user.email,
                    )

                    # Verify ON_DEAL_LOST was emitted
                    mock_producer.publish.assert_any_call(
                        CRMLifecycleEvent.ON_DEAL_LOST, deal=deal, user_email=unit_user.email
                    )


def test_move_deal_to_regular_stage_no_win_loss_event(unit_user):
    """Test that moving to regular stage doesn't emit win/loss events."""
    # Create pipeline
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    entity = Entity(name='Test Entity')

    old_stage = Stage(
        pipeline=pipeline,
        name='Lead',
        order=1,
        probability=10.0,
    )

    new_stage = Stage(
        pipeline=pipeline,
        name='Qualified',
        order=2,
        probability=25.0,
    )
    new_stage._object_id = 'stage_regular'

    deal = Deal(name='Regular Deal', stage=old_stage, entity=entity)

    with mock.patch.object(Stage.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.get.return_value = mock_chain
        mock_chain.execute.return_value = new_stage
        mock_filter.return_value = mock_chain

        with mock.patch.object(Deal, 'save'):
            with mock.patch.object(Note, 'save'):
                with mock.patch('amsdal_crm.services.deal_service.LifecycleProducer') as mock_producer:
                    DealService.move_deal_to_stage(
                        deal=deal, new_stage_id='stage_regular', note=None, user_email=unit_user.email
                    )

                    # Verify ON_DEAL_STAGE_CHANGE was emitted
                    mock_producer.publish.assert_any_call(
                        CRMLifecycleEvent.ON_DEAL_STAGE_CHANGE,
                        deal=deal,
                        old_stage='Lead',
                        new_stage='Qualified',
                        user_email=unit_user.email,
                    )

                    # Verify ON_DEAL_WON and ON_DEAL_LOST were NOT emitted
                    all_events = [call[0][0] for call in mock_producer.publish.call_args_list]
                    assert CRMLifecycleEvent.ON_DEAL_WON not in all_events
                    assert CRMLifecycleEvent.ON_DEAL_LOST not in all_events


@pytest.mark.asyncio
async def test_amove_deal_to_stage_async(unit_user):
    """Test async version of move_deal_to_stage."""
    # Create pipeline
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    entity = Entity(name='Test Entity')

    old_stage = Stage(
        pipeline=pipeline,
        name='Lead',
        order=1,
        probability=10.0,
    )

    new_stage = Stage(
        pipeline=pipeline,
        name='Qualified',
        order=2,
        probability=25.0,
    )
    new_stage._object_id = 'stage_async'

    deal = Deal(name='Async Deal', stage=old_stage, entity=entity)
    deal._object_id = 'deal_async_123'

    with mock.patch.object(Stage.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.get.return_value = mock_chain

        # Mock async execute
        async def async_execute():
            return new_stage

        mock_chain.aexecute = async_execute
        mock_filter.return_value = mock_chain

        with mock.patch.object(Deal, 'asave') as mock_asave:
            with mock.patch.object(Note, 'asave') as mock_asave_note:
                with mock.patch(
                    'amsdal_crm.services.deal_service.LifecycleProducer',
                    new_callable=AsyncMock,
                ) as mock_producer:
                    # Mock async saves
                    async def async_save(*args, **kwargs):
                        pass

                    mock_asave.side_effect = async_save
                    mock_asave_note.side_effect = async_save

                    updated_deal = await DealService.amove_deal_to_stage(
                        deal=deal, new_stage_id='stage_async', note=None, user_email=unit_user.email
                    )

                    # Verify deal stage was updated
                    assert updated_deal.stage == new_stage

                    # Verify async save was called
                    mock_asave.assert_called_once()
                    mock_asave_note.assert_called_once()

                    # Verify lifecycle event was emitted
                    mock_producer.publish_async.assert_any_call(
                        CRMLifecycleEvent.ON_DEAL_STAGE_CHANGE,
                        deal=deal,
                        old_stage='Lead',
                        new_stage='Qualified',
                        user_email=unit_user.email,
                    )


@pytest.mark.asyncio
async def test_amove_deal_to_closed_won_async(unit_user):
    """Test async moving to closed won stage."""
    # Create pipeline
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    entity = Entity(name='Test Entity')

    old_stage = Stage(
        pipeline=pipeline,
        name='Negotiation',
        order=4,
        probability=75.0,
    )

    new_stage = Stage(
        pipeline=pipeline,
        name='Closed Won',
        order=5,
        probability=100.0,
        status='closed_won',
    )
    new_stage._object_id = 'stage_won_async'

    deal = Deal(name='Async Won Deal', stage=old_stage, entity=entity)

    with mock.patch.object(Stage.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.get.return_value = mock_chain

        async def async_execute():
            return new_stage

        mock_chain.aexecute = async_execute
        mock_filter.return_value = mock_chain

        with mock.patch.object(Deal, 'asave') as mock_asave:
            with mock.patch.object(Note, 'asave') as mock_asave_note:
                with mock.patch(
                    'amsdal_crm.services.deal_service.LifecycleProducer',
                    new_callable=AsyncMock,
                ) as mock_producer:

                    async def async_save(*args, **kwargs):
                        pass

                    mock_asave.side_effect = async_save
                    mock_asave_note.side_effect = async_save

                    await DealService.amove_deal_to_stage(
                        deal=deal, new_stage_id='stage_won_async', note=None, user_email=unit_user.email
                    )

                    # Verify ON_DEAL_WON was emitted
                    mock_producer.publish_async.assert_any_call(
                        CRMLifecycleEvent.ON_DEAL_WON, deal=deal, user_email=unit_user.email
                    )
