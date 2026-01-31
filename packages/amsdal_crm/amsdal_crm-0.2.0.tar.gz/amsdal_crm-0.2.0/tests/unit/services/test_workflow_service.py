"""Unit tests for WorkflowService."""

from unittest import mock

import pytest

from amsdal_crm.errors import WorkflowExecutionError
from amsdal_crm.models.activity import ActivityRelatedTo
from amsdal_crm.models.activity import Note
from amsdal_crm.models.deal import Deal
from amsdal_crm.models.entity import Entity
from amsdal_crm.models.pipeline import Pipeline
from amsdal_crm.models.stage import Stage
from amsdal_crm.models.workflow_rule import WorkflowRule
from amsdal_crm.services.workflow_service import WorkflowService


def test_execute_rules_no_matching_rules(unit_user):
    """Test execute_rules when no rules match."""
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    stage = Stage(pipeline=pipeline, name='Qualified', order=1, probability=25.0)
    entity = Entity(name='Test Entity')

    deal = Deal(name='Test Deal', stage=stage, entity=entity)

    with mock.patch.object(WorkflowRule.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.execute.return_value = []
        mock_filter.return_value = mock_chain

        # Should not raise any errors
        WorkflowService.execute_rules('Deal', 'update', deal)


def test_execute_rules_with_matching_rule(unit_user):
    """Test execute_rules executes matching rules."""
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    stage = Stage(pipeline=pipeline, name='Qualified', order=1, probability=25.0)
    entity = Entity(name='Test Entity')

    deal = Deal(name='Test Deal', stage=stage, entity=entity, amount=150000.0)
    deal._object_id = 'deal_123'


    rule = WorkflowRule(
        name='High Value Deal Alert',
        entity_type='Deal',
        trigger_event='update',
        condition_field='amount',
        condition_operator='greater_than',
        condition_value=100000.0,
        action_type='create_activity',
        action_config={'subject': 'High value deal', 'description': 'Deal value exceeds $100k'},
        is_active=True,
    )

    with mock.patch.object(WorkflowRule.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.execute.return_value = [rule]
        mock_filter.return_value = mock_chain

        with mock.patch.object(Note, 'save') as mock_save:
            WorkflowService.execute_rules('Deal', 'update', deal)

            # Verify action was executed (Note was saved)
            mock_save.assert_called_once()


def test_execute_rules_skips_non_matching_condition(unit_user):
    """Test execute_rules skips rules that don't match condition."""
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    stage = Stage(pipeline=pipeline, name='Qualified', order=1, probability=25.0)
    entity = Entity(name='Test Entity')

    deal = Deal(name='Test Deal', stage=stage, entity=entity, amount=5000.0)

    rule = WorkflowRule(
        name='High Value Deal Alert',
        entity_type='Deal',
        trigger_event='update',
        condition_field='amount',
        condition_operator='greater_than',
        condition_value=100000.0,
        action_type='create_activity',
        action_config={'subject': 'High value deal'},
        is_active=True,
    )

    with mock.patch.object(WorkflowRule.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.execute.return_value = [rule]
        mock_filter.return_value = mock_chain

        with mock.patch.object(Note, 'save') as mock_save:
            WorkflowService.execute_rules('Deal', 'update', deal)

            # Verify action was NOT executed
            mock_save.assert_not_called()


def test_evaluate_condition_no_condition():
    """Test _evaluate_condition returns True when no condition is set."""
    rule = WorkflowRule(
        name='Always Execute',
        entity_type='Deal',
        trigger_event='create',
        action_type='create_activity',
        action_config={},
        is_active=True,
    )

    entity = mock.Mock()
    result = WorkflowService._evaluate_condition(rule, entity)

    assert result is True


def test_evaluate_condition_equals(unit_user):
    """Test _evaluate_condition with equals operator."""
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    stage = Stage(pipeline=pipeline, name='Qualified', order=1, probability=25.0)
    entity = Entity(name='Test Entity')

    rule = WorkflowRule(
        name='Test Rule',
        entity_type='Deal',
        trigger_event='update',
        condition_field='status',
        condition_operator='equals',
        condition_value='closed_won',
        action_type='create_activity',
        action_config={},
    )

    deal = Deal(name='Test', stage=stage, entity=entity, status='closed_won')

    result = WorkflowService._evaluate_condition(rule, deal)
    assert result is True

    deal.status = 'open'
    result = WorkflowService._evaluate_condition(rule, deal)
    assert result is False


def test_evaluate_condition_not_equals(unit_user):
    """Test _evaluate_condition with not_equals operator."""
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    stage = Stage(pipeline=pipeline, name='Qualified', order=1, probability=25.0)
    entity = Entity(name='Test Entity')

    rule = WorkflowRule(
        name='Test Rule',
        entity_type='Deal',
        trigger_event='update',
        condition_field='status',
        condition_operator='not_equals',
        condition_value='closed_won',
        action_type='create_activity',
        action_config={},
    )

    deal = Deal(name='Test', stage=stage, entity=entity, status='open')

    result = WorkflowService._evaluate_condition(rule, deal)
    assert result is True

    deal.status = 'closed_won'
    result = WorkflowService._evaluate_condition(rule, deal)
    assert result is False


def test_evaluate_condition_contains():
    """Test _evaluate_condition with contains operator."""
    rule = WorkflowRule(
        name='Test Rule',
        entity_type='Deal',
        trigger_event='update',
        condition_field='name',
        condition_operator='contains',
        condition_value='Enterprise',
        action_type='create_activity',
        action_config={},
    )

    entity = mock.Mock()
    entity.name = 'Enterprise Deal Q2'

    result = WorkflowService._evaluate_condition(rule, entity)
    assert result is True

    entity.name = 'Small Business Deal'
    result = WorkflowService._evaluate_condition(rule, entity)
    assert result is False


def test_evaluate_condition_greater_than(unit_user):
    """Test _evaluate_condition with greater_than operator."""
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    stage = Stage(pipeline=pipeline, name='Qualified', order=1, probability=25.0)
    entity = Entity(name='Test Entity')

    rule = WorkflowRule(
        name='Test Rule',
        entity_type='Deal',
        trigger_event='update',
        condition_field='amount',
        condition_operator='greater_than',
        condition_value=50000.0,
        action_type='create_activity',
        action_config={},
    )

    deal = Deal(name='Test', stage=stage, entity=entity, amount=75000.0)

    result = WorkflowService._evaluate_condition(rule, deal)
    assert result is True

    deal.amount = 25000.0
    result = WorkflowService._evaluate_condition(rule, deal)
    assert result is False


def test_evaluate_condition_less_than(unit_user):
    """Test _evaluate_condition with less_than operator."""
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    stage = Stage(pipeline=pipeline, name='Qualified', order=1, probability=25.0)
    entity = Entity(name='Test Entity')

    rule = WorkflowRule(
        name='Test Rule',
        entity_type='Deal',
        trigger_event='update',
        condition_field='amount',
        condition_operator='less_than',
        condition_value=10000.0,
        action_type='create_activity',
        action_config={},
    )

    deal = Deal(name='Test', stage=stage, entity=entity, amount=5000.0)

    result = WorkflowService._evaluate_condition(rule, deal)
    assert result is True

    deal.amount = 15000.0
    result = WorkflowService._evaluate_condition(rule, deal)
    assert result is False


def test_execute_action_update_field(unit_user):
    """Test _execute_action with update_field action type."""
    rule = WorkflowRule(
        name='Auto-assign Territory',
        entity_type='Entity',
        trigger_event='create',
        action_type='update_field',
        action_config={'field_name': 'territory', 'value': 'West Coast'},
    )

    entity = mock.Mock()
    entity.territory = None

    with mock.patch.object(entity, 'save') as mock_save:
        WorkflowService._execute_action(rule, entity)

        # Verify field was updated
        assert entity.territory == 'West Coast'
        mock_save.assert_called_once()


def test_execute_action_create_activity(unit_user):
    """Test _execute_action with create_activity action type."""
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    stage = Stage(pipeline=pipeline, name='Qualified', order=1, probability=25.0)
    entity = Entity(name='Test Entity')

    rule = WorkflowRule(
        name='Log Activity',
        entity_type='Deal',
        trigger_event='update',
        action_type='create_activity',
        action_config={'subject': 'Deal Updated', 'description': 'Deal was modified'},
    )

    deal = Deal(name='Test Deal', stage=stage, entity=entity)
    deal._object_id = 'deal_789'


    # Capture Note instances as they're created
    created_notes = []
    original_init = Note.__init__

    def capture_init(self, **kwargs):
        original_init(self, **kwargs)
        created_notes.append(self)

    with mock.patch.object(Note, '__init__', capture_init):
        with mock.patch.object(Note, 'save'):
            WorkflowService._execute_action(rule, deal)

            # Verify Note was created with correct attributes
            assert len(created_notes) == 1
            note = created_notes[0]
            assert note.subject == 'Deal Updated'
            assert note.description == 'Deal was modified'
            assert note.related_to_type == ActivityRelatedTo.DEAL
            assert note.related_to_id == 'deal_789'


def test_execute_action_create_activity_default_subject(unit_user):
    """Test _execute_action creates activity with default subject."""
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    stage = Stage(pipeline=pipeline, name='Qualified', order=1, probability=25.0)
    entity = Entity(name='Test Entity')

    rule = WorkflowRule(
        name='Auto Log',
        entity_type='Deal',
        trigger_event='create',
        action_type='create_activity',
        action_config={'description': 'Deal created automatically'},
    )

    deal = Deal(name='Test Deal', stage=stage, entity=entity)
    deal._object_id = 'deal_999'


    # Capture Note instances as they're created
    created_notes = []
    original_init = Note.__init__

    def capture_init(self, **kwargs):
        original_init(self, **kwargs)
        created_notes.append(self)

    with mock.patch.object(Note, '__init__', capture_init):
        with mock.patch.object(Note, 'save'):
            WorkflowService._execute_action(rule, deal)

            # Verify default subject was used
            assert len(created_notes) == 1
            note = created_notes[0]
            assert note.subject == 'Workflow: Auto Log'


def test_execute_action_send_notification():
    """Test _execute_action with send_notification action type (placeholder)."""
    rule = WorkflowRule(
        name='Notify Manager',
        entity_type='Deal',
        trigger_event='update',
        action_type='send_notification',
        action_config={'recipient': 'manager@example.com', 'template': 'deal_updated'},
    )

    entity = mock.Mock()

    # Should not raise any errors (placeholder implementation does nothing)
    WorkflowService._execute_action(rule, entity)


def test_execute_rules_raises_error_on_action_failure(unit_user):
    """Test execute_rules raises WorkflowExecutionError when action fails."""
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    stage = Stage(pipeline=pipeline, name='Qualified', order=1, probability=25.0)
    entity = Entity(name='Test Entity')

    deal = Deal(name='Test Deal', stage=stage, entity=entity, amount=150000.0)

    rule = WorkflowRule(
        name='Failing Rule',
        entity_type='Deal',
        trigger_event='update',
        condition_field='amount',
        condition_operator='greater_than',
        condition_value=100000.0,
        action_type='create_activity',
        action_config={'subject': 'Test'},
    )

    with mock.patch.object(WorkflowRule.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.execute.return_value = [rule]
        mock_filter.return_value = mock_chain

        with mock.patch.object(Note, 'save') as mock_save:
            # Make save raise an exception
            mock_save.side_effect = Exception('Database error')

            with pytest.raises(WorkflowExecutionError, match='Failed to execute workflow rule'):
                WorkflowService.execute_rules('Deal', 'update', deal)


def test_execute_rules_filters_active_only(unit_user):
    """Test that execute_rules only loads active rules."""
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    stage = Stage(pipeline=pipeline, name='Qualified', order=1, probability=25.0)
    entity = Entity(name='Test Entity')

    deal = Deal(name='Test Deal', stage=stage, entity=entity)

    with mock.patch.object(WorkflowRule.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.execute.return_value = []
        mock_filter.return_value = mock_chain

        WorkflowService.execute_rules('Deal', 'update', deal)

        # Verify filter was called with is_active=True
        mock_filter.assert_called_once()
        call_kwargs = mock_filter.call_args[1]
        assert call_kwargs['entity_type'] == 'Deal'
        assert call_kwargs['trigger_event'] == 'update'
        assert call_kwargs['is_active'] is True


def test_execute_rules_multiple_rules(unit_user):
    """Test execute_rules executes multiple matching rules."""
    pipeline = Pipeline(name='Sales Pipeline', description='Test', is_active=True)
    stage = Stage(pipeline=pipeline, name='Qualified', order=1, probability=25.0)
    entity = Entity(name='Test Entity')

    deal = Deal(name='Big Deal', stage=stage, entity=entity, amount=200000.0)
    deal._object_id = 'deal_multi'


    rule1 = WorkflowRule(
        name='Rule 1',
        entity_type='Deal',
        trigger_event='update',
        condition_field='amount',
        condition_operator='greater_than',
        condition_value=100000.0,
        action_type='create_activity',
        action_config={'subject': 'High value'},
    )

    rule2 = WorkflowRule(
        name='Rule 2',
        entity_type='Deal',
        trigger_event='update',
        condition_field='name',
        condition_operator='contains',
        condition_value='Big',
        action_type='create_activity',
        action_config={'subject': 'Big deal'},
    )

    with mock.patch.object(WorkflowRule.objects, 'filter') as mock_filter:
        mock_chain = mock.Mock()
        mock_chain.execute.return_value = [rule1, rule2]
        mock_filter.return_value = mock_chain

        with mock.patch.object(Note, 'save') as mock_save:
            WorkflowService.execute_rules('Deal', 'update', deal)

            # Verify both rules were executed (2 Notes saved)
            assert mock_save.call_count == 2
