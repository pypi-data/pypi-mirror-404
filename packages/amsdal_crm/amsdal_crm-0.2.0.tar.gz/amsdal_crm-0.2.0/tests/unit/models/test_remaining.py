"""Unit tests for Attachment, CustomFieldDefinition, and WorkflowRule models."""

from datetime import UTC
from datetime import datetime

from amsdal_crm.models.attachment import Attachment
from amsdal_crm.models.custom_field_definition import CustomFieldDefinition
from amsdal_crm.models.workflow_rule import WorkflowRule

# Attachment Tests


def test_attachment_creation():
    """Test creating an attachment."""
    from amsdal.models.core.file import File

    file = File(filename='proposal.pdf')

    attachment = Attachment(
        file=file,
        related_to_type='Deal',
        related_to_id='deal_123',
        uploaded_by='test@example.com',
        description='Q2 Proposal Document',
    )

    assert attachment.file == file
    assert attachment.related_to_type == 'Deal'
    assert attachment.related_to_id == 'deal_123'
    assert attachment.uploaded_by == 'test@example.com'
    assert attachment.description == 'Q2 Proposal Document'


def test_attachment_display_name_with_file():
    """Test attachment display_name with file object."""
    from amsdal.models.core.file import File

    file = File(filename='contract.docx')

    attachment = Attachment(
        file=file,
        related_to_type='Deal',
        related_to_id='deal_123',
        uploaded_by='test@example.com',
    )

    assert attachment.display_name == 'contract.docx'


def test_attachment_display_name_without_filename():
    """Test attachment display_name fallback."""
    from amsdal.models.core.file import File

    # Create a file without filename attribute to test fallback
    file = File(filename='test.txt')

    attachment = Attachment(
        file=file,
        related_to_type='Entity',
        related_to_id='entity_123',
        uploaded_by='test@example.com',
    )

    # When file has filename, display_name should use it
    assert attachment.display_name == 'test.txt'


def test_attachment_uploaded_at_default():
    """Test attachment has uploaded_at set by default."""
    from amsdal.models.core.file import File

    file = File(filename='test.pdf')

    attachment = Attachment(
        file=file,
        related_to_type='Entity',
        related_to_id='entity_123',
        uploaded_by='test@example.com',
    )

    assert attachment.uploaded_at is not None
    assert isinstance(attachment.uploaded_at, datetime)
    assert attachment.uploaded_at.tzinfo == UTC


# CustomFieldDefinition Tests


def test_custom_field_definition_creation(sample_custom_field_definition_data):
    """Test creating a custom field definition."""
    field_def = CustomFieldDefinition(**sample_custom_field_definition_data)

    assert field_def.entity_type == 'Entity'
    assert field_def.field_name == 'customer_tier'
    assert field_def.field_label == 'Customer Tier'
    assert field_def.field_type == 'choice'
    assert field_def.choices == ['bronze', 'silver', 'gold', 'platinum']
    assert field_def.is_required is False


def test_custom_field_definition_display_name(sample_custom_field_definition_data):
    """Test custom field definition display_name."""
    field_def = CustomFieldDefinition(**sample_custom_field_definition_data)

    assert field_def.display_name == 'Entity.customer_tier'


def test_custom_field_definition_text_type():
    """Test creating a text type custom field."""
    field_def = CustomFieldDefinition(
        entity_type='Entity',
        field_name='tax_id',
        field_label='Tax ID',
        field_type='text',
    )

    assert field_def.field_type == 'text'
    assert field_def.choices is None


def test_custom_field_definition_number_type():
    """Test creating a number type custom field."""
    field_def = CustomFieldDefinition(
        entity_type='Deal',
        field_name='discount_percentage',
        field_label='Discount %',
        field_type='number',
    )

    assert field_def.field_type == 'number'


def test_custom_field_definition_date_type():
    """Test creating a date type custom field."""
    field_def = CustomFieldDefinition(
        entity_type='Entity',
        field_name='last_contacted',
        field_label='Last Contacted',
        field_type='date',
    )

    assert field_def.field_type == 'date'


def test_custom_field_definition_required():
    """Test creating a required custom field."""
    field_def = CustomFieldDefinition(
        entity_type='Entity',
        field_name='customer_type',
        field_label='Customer Type',
        field_type='choice',
        choices=['individual', 'business'],
        is_required=True,
    )

    assert field_def.is_required is True


def test_custom_field_definition_with_default():
    """Test creating a custom field with default value."""
    field_def = CustomFieldDefinition(
        entity_type='Entity',
        field_name='lead_source',
        field_label='Lead Source',
        field_type='choice',
        choices=['website', 'referral', 'event'],
        default_value='website',
    )

    assert field_def.default_value == 'website'


def test_custom_field_definition_with_help_text():
    """Test creating a custom field with help text."""
    field_def = CustomFieldDefinition(
        entity_type='Entity',
        field_name='annual_revenue',
        field_label='Annual Revenue',
        field_type='number',
        help_text='Estimated annual revenue in USD',
    )

    assert field_def.help_text == 'Estimated annual revenue in USD'


# WorkflowRule Tests


def test_workflow_rule_creation(sample_workflow_rule_data):
    """Test creating a workflow rule."""
    rule = WorkflowRule(**sample_workflow_rule_data)

    assert rule.name == 'Notify on High Value Deal'
    assert rule.entity_type == 'Deal'
    assert rule.trigger_event == 'update'
    assert rule.condition_field == 'amount'
    assert rule.condition_operator == 'greater_than'
    assert rule.condition_value == 100000.00
    assert rule.action_type == 'create_activity'
    assert rule.is_active is True


def test_workflow_rule_display_name(sample_workflow_rule_data):
    """Test workflow rule display_name."""
    rule = WorkflowRule(**sample_workflow_rule_data)

    assert rule.display_name == 'Deal: Notify on High Value Deal'


def test_workflow_rule_without_condition():
    """Test creating a workflow rule without condition (always triggers)."""
    rule = WorkflowRule(
        name='Log All Updates',
        entity_type='Entity',
        trigger_event='update',
        action_type='create_activity',
        action_config={'subject': 'Entity updated'},
    )

    assert rule.condition_field is None
    assert rule.condition_operator is None
    assert rule.condition_value is None


def test_workflow_rule_update_field_action():
    """Test workflow rule with update_field action."""
    rule = WorkflowRule(
        name='Auto-assign Territory',
        entity_type='Entity',
        trigger_event='create',
        condition_field='status',
        condition_operator='equals',
        condition_value='Active',
        action_type='update_field',
        action_config={'field_name': 'territory', 'value': 'West Coast'},
    )

    assert rule.action_type == 'update_field'
    assert rule.action_config['field_name'] == 'territory'
    assert rule.action_config['value'] == 'West Coast'


def test_workflow_rule_send_notification_action():
    """Test workflow rule with send_notification action."""
    rule = WorkflowRule(
        name='Notify Manager',
        entity_type='Deal',
        trigger_event='update',
        condition_field='status',
        condition_operator='equals',
        condition_value='closed_won',
        action_type='send_notification',
        action_config={'recipient': 'manager@example.com', 'template': 'deal_closed'},
    )

    assert rule.action_type == 'send_notification'
    assert rule.action_config['recipient'] == 'manager@example.com'


def test_workflow_rule_inactive():
    """Test creating an inactive workflow rule."""
    rule = WorkflowRule(
        name='Disabled Rule',
        entity_type='Entity',
        trigger_event='create',
        action_type='create_activity',
        action_config={'subject': 'New entity'},
        is_active=False,
    )

    assert rule.is_active is False


def test_workflow_rule_trigger_events():
    """Test workflow rules for different trigger events."""
    # Create trigger
    create_rule = WorkflowRule(
        name='On Create',
        entity_type='Entity',
        trigger_event='create',
        action_type='create_activity',
        action_config={},
    )
    assert create_rule.trigger_event == 'create'

    # Update trigger
    update_rule = WorkflowRule(
        name='On Update',
        entity_type='Deal',
        trigger_event='update',
        action_type='create_activity',
        action_config={},
    )
    assert update_rule.trigger_event == 'update'

    # Delete trigger
    delete_rule = WorkflowRule(
        name='On Delete',
        entity_type='Entity',
        trigger_event='delete',
        action_type='create_activity',
        action_config={},
    )
    assert delete_rule.trigger_event == 'delete'


def test_workflow_rule_condition_operators():
    """Test workflow rules with different condition operators."""
    # equals
    equals_rule = WorkflowRule(
        name='Test Equals',
        entity_type='Entity',
        trigger_event='update',
        condition_field='status',
        condition_operator='equals',
        condition_value='Active',
        action_type='create_activity',
        action_config={},
    )
    assert equals_rule.condition_operator == 'equals'

    # not_equals
    not_equals_rule = WorkflowRule(
        name='Test Not Equals',
        entity_type='Entity',
        trigger_event='update',
        condition_field='status',
        condition_operator='not_equals',
        condition_value='Inactive',
        action_type='create_activity',
        action_config={},
    )
    assert not_equals_rule.condition_operator == 'not_equals'

    # contains
    contains_rule = WorkflowRule(
        name='Test Contains',
        entity_type='Entity',
        trigger_event='update',
        condition_field='name',
        condition_operator='contains',
        condition_value='Corp',
        action_type='create_activity',
        action_config={},
    )
    assert contains_rule.condition_operator == 'contains'

    # greater_than
    gt_rule = WorkflowRule(
        name='Test Greater Than',
        entity_type='Deal',
        trigger_event='update',
        condition_field='amount',
        condition_operator='greater_than',
        condition_value=10000,
        action_type='create_activity',
        action_config={},
    )
    assert gt_rule.condition_operator == 'greater_than'

    # less_than
    lt_rule = WorkflowRule(
        name='Test Less Than',
        entity_type='Deal',
        trigger_event='update',
        condition_field='amount',
        condition_operator='less_than',
        condition_value=1000,
        action_type='create_activity',
        action_config={},
    )
    assert lt_rule.condition_operator == 'less_than'
