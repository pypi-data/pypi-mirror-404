"""Integration tests for WorkflowService."""

from amsdal.manager import AmsdalManager

from amsdal_crm.models.activity import ActivityRelatedTo
from amsdal_crm.models.activity import Note
from amsdal_crm.models.deal import Deal
from amsdal_crm.models.workflow_rule import WorkflowRule
from amsdal_crm.services.workflow_service import WorkflowService


def test_execute_action_create_activity(
    crm_manager: AmsdalManager, mock_user, sample_pipeline, sample_stage, sample_entity
):
    """Test _execute_action with create_activity action type."""
    rule = WorkflowRule(
        name='Log Activity',
        entity_type='Deal',
        trigger_event='update',
        action_type='create_activity',
        action_config={'subject': 'Deal Updated', 'description': 'Deal was modified'},
        is_active=True,
    )

    deal = Deal(name='Test Deal', stage=sample_stage, entity=sample_entity)
    deal.save(force_insert=True)

    # Execute the action
    WorkflowService._execute_action(rule, deal)

    # Verify Note was created and saved
    notes = Note.objects.filter(related_to_type=ActivityRelatedTo.DEAL, related_to_id=deal._object_id).execute()
    assert len(notes) == 1
    note = notes[0]
    assert note.subject == 'Deal Updated'
    assert note.description == 'Deal was modified'
    assert note.related_to_type == ActivityRelatedTo.DEAL
    assert note.related_to_id == deal._object_id


def test_execute_action_create_activity_default_subject(
    crm_manager: AmsdalManager, mock_user, sample_pipeline, sample_stage, sample_entity
):
    """Test _execute_action creates activity with default subject."""
    rule = WorkflowRule(
        name='Auto Log',
        entity_type='Deal',
        trigger_event='create',
        action_type='create_activity',
        action_config={'description': 'Deal created automatically'},
        is_active=True,
    )

    deal = Deal(name='Test Deal', stage=sample_stage, entity=sample_entity)
    deal.save(force_insert=True)

    # Execute the action
    WorkflowService._execute_action(rule, deal)

    # Verify default subject was used
    notes = Note.objects.filter(related_to_type=ActivityRelatedTo.DEAL, related_to_id=deal._object_id).execute()
    assert len(notes) == 1
    note = notes[0]
    assert note.subject == 'Workflow: Auto Log'
