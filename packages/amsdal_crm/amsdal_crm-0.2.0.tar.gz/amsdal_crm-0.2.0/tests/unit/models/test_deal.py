"""Unit tests for Deal model."""

from datetime import UTC
from datetime import datetime
from unittest import mock

from amsdal_crm.models.deal import Deal


def test_deal_creation(unit_deal_data):
    """Test creating a deal."""
    deal = Deal(**unit_deal_data)

    assert deal.name == 'Enterprise Deal'
    assert deal.amount == 50000.00
    assert deal.currency == 'USD'


def test_deal_display_name(unit_deal_data):
    """Test deal display_name property."""
    deal = Deal(**unit_deal_data)

    assert deal.display_name == 'Enterprise Deal'


def test_deal_stage_name_with_stage_object(unit_stage, unit_entity):
    """Test deal stage_name with stage object."""
    deal = Deal(
        name='Test Deal',
        stage=unit_stage,
        entity=unit_entity,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert deal.stage_name == 'Qualified'


def test_deal_default_currency(unit_stage, unit_entity):
    """Test deal has default currency of USD."""
    deal = Deal(
        name='Test Deal',
        stage=unit_stage,
        entity=unit_entity,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert deal.currency == 'USD'


def test_deal_default_status(unit_stage, unit_entity):
    """Test deal has default status of open."""
    deal = Deal(
        name='Test Deal',
        stage=unit_stage,
        entity=unit_entity,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert deal.status == 'open'


def test_deal_has_object_permission_owner(unit_user, unit_deal_data):
    """Test that owner has permission."""
    deal = Deal(**unit_deal_data)
    object.__setattr__(deal, 'assigned_to', unit_user)

    assert deal.has_object_permission(unit_user, 'read') is True
    assert deal.has_object_permission(unit_user, 'update') is True
    assert deal.has_object_permission(unit_user, 'delete') is True


def test_deal_has_object_permission_non_owner(unit_deal_data):
    """Test that non-owner doesn't have permission."""
    deal = Deal(**unit_deal_data)

    other_user = mock.Mock()
    other_user.email = 'other@example.com'
    other_user.permissions = []

    assert deal.has_object_permission(other_user, 'read') is False


def test_deal_has_object_permission_admin(unit_admin_user, unit_deal_data):
    """Test that admin has permission."""
    deal = Deal(**unit_deal_data)

    assert deal.has_object_permission(unit_admin_user, 'read') is True
    assert deal.has_object_permission(unit_admin_user, 'update') is True


def test_deal_pre_update_syncs_closed_status_won(unit_pipeline, unit_entity):
    """Test that pre_update syncs status with stage."""
    from amsdal_crm.models.stage import Stage

    stage = Stage(
        pipeline=unit_pipeline,
        name='Closed Won',
        order=5,
        probability=100.0,
        status='closed_won',
    )

    deal = Deal(
        name='Test Deal',
        stage=stage,
        entity=unit_entity,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService'):
        with mock.patch('amsdal_models.classes.helpers.reference_loader.ReferenceLoader') as mock_loader:
            mock_loader.return_value.load_reference.return_value = stage
            with mock.patch('amsdal.models.mixins.TimestampMixin.pre_update'):
                deal.pre_update()

    assert deal.status == 'closed_won'
    assert deal.closed_date is not None


def test_deal_pre_update_syncs_closed_status_lost(unit_pipeline, unit_entity):
    """Test that pre_update syncs status for lost deals."""
    from amsdal_crm.models.stage import Stage

    stage = Stage(
        pipeline=unit_pipeline,
        name='Closed Lost',
        order=6,
        probability=0.0,
        status='closed_lost',
    )

    deal = Deal(
        name='Test Deal',
        stage=stage,
        entity=unit_entity,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService'):
        with mock.patch('amsdal_models.classes.helpers.reference_loader.ReferenceLoader') as mock_loader:
            mock_loader.return_value.load_reference.return_value = stage
            with mock.patch('amsdal.models.mixins.TimestampMixin.pre_update'):
                deal.pre_update()

    assert deal.status == 'closed_lost'
    assert deal.closed_date is not None


def test_deal_pre_update_doesnt_overwrite_closed_date(unit_pipeline, unit_entity):
    """Test that pre_update doesn't overwrite existing closed_date."""
    from amsdal_crm.models.stage import Stage

    stage = Stage(
        pipeline=unit_pipeline,
        name='Closed Won',
        order=5,
        probability=100.0,
        status='closed_won',
    )

    existing_closed_date = datetime(2026, 1, 1, tzinfo=UTC)
    deal = Deal(
        name='Test Deal',
        stage=stage,
        entity=unit_entity,
        closed_date=existing_closed_date,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService'):
        with mock.patch('amsdal_models.classes.helpers.reference_loader.ReferenceLoader') as mock_loader:
            mock_loader.return_value.load_reference.return_value = stage
            with mock.patch('amsdal.models.mixins.TimestampMixin.pre_update'):
                deal.pre_update()

    assert deal.closed_date == existing_closed_date


def test_deal_pre_update_sets_updated_at(unit_stage, unit_entity):
    """Test that pre_update sets updated_at timestamp."""
    deal = Deal(
        name='Test Deal',
        stage=unit_stage,
        entity=unit_entity,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    deal.updated_at = None

    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService'):
        with mock.patch('amsdal_models.classes.helpers.reference_loader.ReferenceLoader') as mock_loader:
            mock_loader.return_value.load_reference.return_value = unit_stage
            with mock.patch('amsdal.models.mixins.TimestampMixin.pre_update') as mock_super:
                # Simulate the parent setting updated_at
                def set_updated_at():
                    deal.updated_at = datetime.now(UTC)

                mock_super.side_effect = set_updated_at

                deal.pre_update()

    assert deal.updated_at is not None
    assert isinstance(deal.updated_at, datetime)
    assert deal.updated_at.tzinfo == UTC


def test_deal_post_update_executes_workflows(unit_deal_data):
    """Test that post_update executes workflow rules."""
    deal = Deal(**unit_deal_data)

    with mock.patch('amsdal_crm.services.workflow_service.WorkflowService') as mock_service:
        deal.post_update()

        mock_service.execute_rules.assert_called_once_with('Deal', 'update', deal)


def test_deal_custom_fields(unit_stage, unit_entity):
    """Test deal with custom fields."""
    deal = Deal(
        name='Test Deal',
        stage=unit_stage,
        entity=unit_entity,
        custom_fields={'deal_source': 'Referral', 'commission_rate': 10},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert deal.custom_fields['deal_source'] == 'Referral'
    assert deal.custom_fields['commission_rate'] == 10
