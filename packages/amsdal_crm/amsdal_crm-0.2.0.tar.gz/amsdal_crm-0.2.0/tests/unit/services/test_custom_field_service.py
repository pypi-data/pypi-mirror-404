"""Unit tests for CustomFieldService."""

from datetime import UTC
from datetime import datetime
from decimal import Decimal
from unittest import mock

import pytest

from amsdal_crm.errors import CustomFieldValidationError
from amsdal_crm.models.custom_field_definition import CustomFieldDefinition
from amsdal_crm.services.custom_field_service import CustomFieldService


@pytest.fixture
def mock_field_definitions():
    """Mock custom field definitions."""
    text_field = CustomFieldDefinition(
        entity_type='Entity',
        field_name='nickname',
        field_label='Nickname',
        field_type='text',
        is_required=False,
    )

    number_field = CustomFieldDefinition(
        entity_type='Entity',
        field_name='age',
        field_label='Age',
        field_type='number',
        is_required=False,
    )

    date_field = CustomFieldDefinition(
        entity_type='Entity',
        field_name='last_contact_date',
        field_label='Last Contact Date',
        field_type='date',
        is_required=False,
    )

    choice_field = CustomFieldDefinition(
        entity_type='Entity',
        field_name='customer_tier',
        field_label='Customer Tier',
        field_type='choice',
        choices=['bronze', 'silver', 'gold'],
        is_required=False,
    )

    required_field = CustomFieldDefinition(
        entity_type='Entity',
        field_name='required_field',
        field_label='Required Field',
        field_type='text',
        is_required=True,
    )

    return [text_field, number_field, date_field, choice_field, required_field]


def test_validate_custom_fields_success(mock_field_definitions):
    """Test successful custom field validation."""
    custom_fields = {
        'nickname': 'Johnny',
        'age': 30,
        'customer_tier': 'gold',
    }

    with mock.patch.object(CustomFieldDefinition.objects, 'filter') as mock_filter:
        mock_filter.return_value.execute.return_value = mock_field_definitions

        result = CustomFieldService.validate_custom_fields('Entity', custom_fields)

        assert result['nickname'] == 'Johnny'
        assert result['age'] == Decimal('30')
        assert result['customer_tier'] == 'gold'


def test_validate_custom_fields_empty():
    """Test validation with no custom fields."""
    result = CustomFieldService.validate_custom_fields('Entity', None)

    assert result == {}

    result = CustomFieldService.validate_custom_fields('Entity', {})

    assert result == {}


def test_validate_custom_fields_unknown_field(mock_field_definitions):
    """Test validation fails for unknown field."""
    custom_fields = {'unknown_field': 'value'}

    with mock.patch.object(CustomFieldDefinition.objects, 'filter') as mock_filter:
        mock_filter.return_value.execute.return_value = mock_field_definitions

        with pytest.raises(CustomFieldValidationError, match='Unknown custom field'):
            CustomFieldService.validate_custom_fields('Entity', custom_fields)


def test_validate_custom_fields_required_field_missing(mock_field_definitions):
    """Test validation fails when required field is missing."""
    with mock.patch.object(CustomFieldDefinition.objects, 'filter') as mock_filter:
        mock_filter.return_value.execute.return_value = mock_field_definitions

        # Include required_field but with None value
        custom_fields_with_none = {'nickname': 'Johnny', 'required_field': None}

        with pytest.raises(CustomFieldValidationError, match='Required custom field'):
            CustomFieldService.validate_custom_fields('Entity', custom_fields_with_none)


def test_validate_text_field():
    """Test text field validation."""
    field_def = CustomFieldDefinition(
        entity_type='Entity',
        field_name='nickname',
        field_label='Nickname',
        field_type='text',
    )

    result = CustomFieldService._validate_field_value(field_def, 'Johnny')
    assert result == 'Johnny'

    # Non-string values should be converted
    result = CustomFieldService._validate_field_value(field_def, 123)
    assert result == '123'


def test_validate_number_field():
    """Test number field validation."""
    field_def = CustomFieldDefinition(
        entity_type='Entity',
        field_name='age',
        field_label='Age',
        field_type='number',
    )

    result = CustomFieldService._validate_field_value(field_def, 30)
    assert result == Decimal('30')

    result = CustomFieldService._validate_field_value(field_def, '42.5')
    assert result == Decimal('42.5')


def test_validate_number_field_invalid():
    """Test number field validation fails for invalid numbers."""
    field_def = CustomFieldDefinition(
        entity_type='Entity',
        field_name='age',
        field_label='Age',
        field_type='number',
    )

    with pytest.raises(CustomFieldValidationError, match='Invalid number'):
        CustomFieldService._validate_field_value(field_def, 'not_a_number')


def test_validate_date_field():
    """Test date field validation."""
    field_def = CustomFieldDefinition(
        entity_type='Entity',
        field_name='last_contact_date',
        field_label='Last Contact Date',
        field_type='date',
    )

    # datetime object
    dt = datetime(2026, 1, 15, tzinfo=UTC)
    result = CustomFieldService._validate_field_value(field_def, dt)
    assert result == dt.isoformat()

    # ISO format string
    result = CustomFieldService._validate_field_value(field_def, '2026-01-15T10:30:00')
    assert isinstance(result, str)


def test_validate_date_field_invalid():
    """Test date field validation fails for invalid dates."""
    field_def = CustomFieldDefinition(
        entity_type='Entity',
        field_name='last_contact_date',
        field_label='Last Contact Date',
        field_type='date',
    )

    with pytest.raises(CustomFieldValidationError, match='Invalid date'):
        CustomFieldService._validate_field_value(field_def, 'not_a_date')


def test_validate_choice_field():
    """Test choice field validation."""
    field_def = CustomFieldDefinition(
        entity_type='Entity',
        field_name='customer_tier',
        field_label='Customer Tier',
        field_type='choice',
        choices=['bronze', 'silver', 'gold'],
    )

    result = CustomFieldService._validate_field_value(field_def, 'gold')
    assert result == 'gold'


def test_validate_choice_field_invalid():
    """Test choice field validation fails for invalid choice."""
    field_def = CustomFieldDefinition(
        entity_type='Entity',
        field_name='customer_tier',
        field_label='Customer Tier',
        field_type='choice',
        choices=['bronze', 'silver', 'gold'],
    )

    with pytest.raises(CustomFieldValidationError, match='Invalid choice'):
        CustomFieldService._validate_field_value(field_def, 'platinum')


def test_validate_choice_field_without_choices():
    """Test choice field without choices list defined."""
    field_def = CustomFieldDefinition(
        entity_type='Entity',
        field_name='customer_tier',
        field_label='Customer Tier',
        field_type='choice',
        choices=None,
    )

    # Should pass validation when choices is None
    result = CustomFieldService._validate_field_value(field_def, 'anything')
    assert result == 'anything'
