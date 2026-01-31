"""Unit tests for Entity model."""

from datetime import UTC
from datetime import datetime
from unittest import mock

from amsdal_crm.models.entity import Entity


def test_entity_creation(unit_entity_data):
    """Test creating an entity."""
    entity = Entity(**unit_entity_data)

    assert entity.name == 'ACME Corp'
    assert entity.status == 'Active'


def test_entity_display_name(unit_entity_data):
    """Test entity display_name property."""
    entity = Entity(**unit_entity_data)

    assert entity.display_name == 'ACME Corp'


def test_entity_has_object_permission_owner(unit_user, unit_entity_data):
    """Test that assigned user has permission."""
    entity = Entity(**unit_entity_data)
    object.__setattr__(entity, 'assigned_to', unit_user)

    assert entity.has_object_permission(unit_user, 'read') is True
    assert entity.has_object_permission(unit_user, 'update') is True
    assert entity.has_object_permission(unit_user, 'delete') is True


def test_entity_has_object_permission_non_owner(unit_entity_data):
    """Test that non-assigned user doesn't have permission."""
    entity = Entity(**unit_entity_data)

    other_user = mock.Mock()
    other_user.email = 'other@example.com'
    other_user.permissions = []

    assert entity.has_object_permission(other_user, 'read') is False
    assert entity.has_object_permission(other_user, 'update') is False


def test_entity_has_object_permission_admin(unit_admin_user, unit_entity_data):
    """Test that admin has permission."""
    entity = Entity(**unit_entity_data)

    assert entity.has_object_permission(unit_admin_user, 'read') is True
    assert entity.has_object_permission(unit_admin_user, 'update') is True
    assert entity.has_object_permission(unit_admin_user, 'delete') is True


def test_entity_has_object_permission_specific_model_permission(unit_entity_data):
    """Test specific model permission."""
    entity = Entity(**unit_entity_data)

    user_with_perm = mock.Mock()
    user_with_perm.email = 'other@example.com'
    permission = mock.Mock()
    permission.model = 'Entity'
    permission.action = 'read'
    user_with_perm.permissions = [permission]

    assert entity.has_object_permission(user_with_perm, 'read') is True
    assert entity.has_object_permission(user_with_perm, 'update') is False


def test_entity_custom_fields():
    """Test entity with custom fields."""
    entity = Entity(
        name='Test Corp',
        custom_fields={'industry_vertical': 'SaaS', 'employee_count': 250},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert entity.custom_fields['industry_vertical'] == 'SaaS'
    assert entity.custom_fields['employee_count'] == 250


def test_entity_pre_update_sets_updated_at(unit_entity_data):
    """Test that pre_update sets updated_at timestamp."""
    entity = Entity(**unit_entity_data)
    entity.updated_at = None

    # Mock the CustomFieldService to avoid database calls
    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService'):
        entity.pre_update()

    assert entity.updated_at is not None
    assert isinstance(entity.updated_at, datetime)
    assert entity.updated_at.tzinfo == UTC


def test_entity_pre_create_validates_custom_fields():
    """Test that pre_create validates custom fields."""
    entity = Entity(name='Test Corp', custom_fields={'test': 'value'})

    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService') as mock_service:
        mock_service.validate_custom_fields.return_value = {'test': 'validated_value'}

        entity.pre_create()

        mock_service.validate_custom_fields.assert_called_once_with('Entity', {'test': 'value'})
        assert entity.custom_fields == {'test': 'validated_value'}


def test_entity_post_update_executes_workflows(unit_entity_data):
    """Test that post_update executes workflow rules."""
    entity = Entity(**unit_entity_data)

    with mock.patch('amsdal_crm.services.workflow_service.WorkflowService') as mock_service:
        entity.post_update()

        mock_service.execute_rules.assert_called_once_with('Entity', 'update', entity)


# Edge Case Tests


def test_entity_with_minimal_required_fields():
    """Test entity creation with only required fields."""
    entity = Entity(
        name='Minimal Corp',
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert entity.name == 'Minimal Corp'
    assert entity.legal_name is None
    assert entity.status == 'Active'
    assert entity.note is None
    assert entity.custom_fields is None


def test_entity_with_all_optional_fields_none():
    """Test entity with all optional fields explicitly set to None."""
    entity = Entity(
        name='Optional None Corp',
        legal_name=None,
        note=None,
        custom_fields=None,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert entity.name == 'Optional None Corp'
    assert entity.legal_name is None
    assert entity.custom_fields is None


def test_entity_with_very_long_name():
    """Test entity with very long name (boundary testing)."""
    long_name = 'A' * 500
    entity = Entity(
        name=long_name,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert entity.name == long_name
    assert len(entity.name) == 500


def test_entity_with_special_characters_in_name():
    """Test entity with special characters in name."""
    special_name = "O'Reilly & Associates, Inc. <test@example.com> - #1"
    entity = Entity(
        name=special_name,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert entity.name == special_name


def test_entity_with_unicode_characters():
    """Test entity with Unicode characters in fields."""
    entity = Entity(
        name='株式会社テスト',
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert entity.name == '株式会社テスト'


def test_entity_with_empty_custom_fields():
    """Test entity with empty custom_fields dict."""
    entity = Entity(
        name='Empty Custom Fields Corp',
        custom_fields={},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert entity.custom_fields == {}


def test_entity_with_large_custom_fields():
    """Test entity with large custom_fields dict."""
    large_custom_fields = {f'field_{i}': f'value_{i}' for i in range(100)}

    entity = Entity(
        name='Large Custom Fields Corp',
        custom_fields=large_custom_fields,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert len(entity.custom_fields) == 100
    assert entity.custom_fields['field_0'] == 'value_0'
    assert entity.custom_fields['field_99'] == 'value_99'


def test_entity_with_nested_custom_fields():
    """Test entity with nested structures in custom_fields."""
    nested_custom_fields = {
        'address': {'street': '123 Main St', 'city': 'San Francisco', 'zip': '94105'},
        'contacts': [{'name': 'John', 'role': 'CEO'}, {'name': 'Jane', 'role': 'CTO'}],
        'metadata': {'source': 'import', 'confidence': 0.95},
    }

    entity = Entity(
        name='Nested Custom Fields Corp',
        custom_fields=nested_custom_fields,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert entity.custom_fields['address']['city'] == 'San Francisco'
    assert len(entity.custom_fields['contacts']) == 2
    assert entity.custom_fields['metadata']['confidence'] == 0.95


def test_entity_with_various_custom_field_types():
    """Test entity with various data types in custom_fields."""
    entity = Entity(
        name='Various Types Corp',
        custom_fields={
            'string_field': 'text',
            'int_field': 42,
            'float_field': 3.14,
            'bool_field': True,
            'list_field': [1, 2, 3],
            'none_field': None,
        },
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert entity.custom_fields['string_field'] == 'text'
    assert entity.custom_fields['int_field'] == 42
    assert entity.custom_fields['float_field'] == 3.14
    assert entity.custom_fields['bool_field'] is True
    assert entity.custom_fields['list_field'] == [1, 2, 3]
    assert entity.custom_fields['none_field'] is None


def test_entity_with_empty_string_name():
    """Test entity with empty string name (should be allowed by model, may fail at DB level)."""
    entity = Entity(
        name='',
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert entity.name == ''


def test_entity_with_whitespace_name():
    """Test entity with whitespace-only name."""
    entity = Entity(
        name='   ',
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert entity.name == '   '


def test_entity_display_name_with_special_characters():
    """Test display_name with special characters."""
    special_name = 'Test & Co. <Special>'
    entity = Entity(
        name=special_name,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert entity.display_name == special_name


def test_entity_permission_check_with_empty_permissions_list(unit_entity_data):
    """Test permission check when user has empty permissions list."""
    entity = Entity(**unit_entity_data)

    user = mock.Mock()
    user.email = 'other@example.com'
    user.permissions = []

    assert entity.has_object_permission(user, 'read') is False


def test_entity_permission_check_with_none_permissions(unit_entity_data):
    """Test permission check when user.permissions is None."""
    entity = Entity(**unit_entity_data)

    user = mock.Mock()
    user.email = 'other@example.com'
    user.permissions = None

    assert entity.has_object_permission(user, 'read') is False


def test_entity_pre_create_with_none_custom_fields():
    """Test pre_create with None custom_fields (should not call validation)."""
    entity = Entity(name='Test Corp', custom_fields=None)

    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService') as mock_service:
        entity.pre_create()

        # Should not call validate_custom_fields when custom_fields is None
        mock_service.validate_custom_fields.assert_not_called()


def test_entity_pre_update_with_empty_custom_fields():
    """Test pre_update with empty custom_fields dict."""
    entity = Entity(name='Test Corp', custom_fields={})

    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService') as mock_service:
        mock_service.validate_custom_fields.return_value = {}

        with mock.patch('amsdal.models.mixins.TimestampMixin.pre_update'):
            entity.pre_update()

        # Should not call validate_custom_fields with empty dict (falsy value)
        mock_service.validate_custom_fields.assert_not_called()


def test_entity_with_legal_name():
    """Test entity with legal_name field."""
    entity = Entity(
        name='ACME',
        legal_name='ACME Corporation Ltd.',
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert entity.legal_name == 'ACME Corporation Ltd.'


def test_entity_status_active_by_default():
    """Test entity status defaults to Active."""
    entity = Entity(name='Test Corp')

    assert entity.status == 'Active'


def test_entity_status_inactive():
    """Test entity with Inactive status."""
    entity = Entity(name='Old Corp', status='Inactive')

    assert entity.status == 'Inactive'


def test_entity_with_note():
    """Test entity with note field."""
    entity = Entity(
        name='Test Corp',
        note='Important client - handle with care',
    )

    assert entity.note == 'Important client - handle with care'
