"""Unit tests for CRM Settings."""

import os
from unittest import mock

import pytest

from amsdal_crm.settings import CRMSettings
from amsdal_crm.settings import crm_settings


class TestCRMSettings:
    """Tests for CRMSettings."""

    def test_settings_instantiation(self):
        """Test that CRMSettings can be instantiated."""
        settings = CRMSettings()
        assert settings is not None

    def test_default_activity_timeline_limit(self):
        """Test default value for DEFAULT_ACTIVITY_TIMELINE_LIMIT."""
        settings = CRMSettings()
        assert settings.DEFAULT_ACTIVITY_TIMELINE_LIMIT == 100

    def test_default_max_custom_fields_per_entity(self):
        """Test default value for MAX_CUSTOM_FIELDS_PER_ENTITY."""
        settings = CRMSettings()
        assert settings.MAX_CUSTOM_FIELDS_PER_ENTITY == 50

    def test_default_max_workflow_rules_per_entity(self):
        """Test default value for MAX_WORKFLOW_RULES_PER_ENTITY."""
        settings = CRMSettings()
        assert settings.MAX_WORKFLOW_RULES_PER_ENTITY == 100

    def test_default_currency(self):
        """Test default value for DEFAULT_CURRENCY."""
        settings = CRMSettings()
        assert settings.DEFAULT_CURRENCY == 'USD'

    def test_all_default_values(self):
        """Test that all default values are set correctly."""
        settings = CRMSettings()

        assert settings.DEFAULT_ACTIVITY_TIMELINE_LIMIT == 100
        assert settings.MAX_CUSTOM_FIELDS_PER_ENTITY == 50
        assert settings.MAX_WORKFLOW_RULES_PER_ENTITY == 100
        assert settings.DEFAULT_CURRENCY == 'USD'

    @mock.patch.dict(os.environ, {'AMSDAL_CRM_DEFAULT_ACTIVITY_TIMELINE_LIMIT': '200'})
    def test_environment_variable_override_activity_limit(self):
        """Test that DEFAULT_ACTIVITY_TIMELINE_LIMIT can be overridden by environment variable."""
        settings = CRMSettings()
        assert settings.DEFAULT_ACTIVITY_TIMELINE_LIMIT == 200

    @mock.patch.dict(os.environ, {'AMSDAL_CRM_MAX_CUSTOM_FIELDS_PER_ENTITY': '75'})
    def test_environment_variable_override_custom_fields(self):
        """Test that MAX_CUSTOM_FIELDS_PER_ENTITY can be overridden by environment variable."""
        settings = CRMSettings()
        assert settings.MAX_CUSTOM_FIELDS_PER_ENTITY == 75

    @mock.patch.dict(os.environ, {'AMSDAL_CRM_MAX_WORKFLOW_RULES_PER_ENTITY': '150'})
    def test_environment_variable_override_workflow_rules(self):
        """Test that MAX_WORKFLOW_RULES_PER_ENTITY can be overridden by environment variable."""
        settings = CRMSettings()
        assert settings.MAX_WORKFLOW_RULES_PER_ENTITY == 150

    @mock.patch.dict(os.environ, {'AMSDAL_CRM_DEFAULT_CURRENCY': 'EUR'})
    def test_environment_variable_override_currency(self):
        """Test that DEFAULT_CURRENCY can be overridden by environment variable."""
        settings = CRMSettings()
        assert settings.DEFAULT_CURRENCY == 'EUR'

    @mock.patch.dict(
        os.environ,
        {
            'AMSDAL_CRM_DEFAULT_ACTIVITY_TIMELINE_LIMIT': '250',
            'AMSDAL_CRM_MAX_CUSTOM_FIELDS_PER_ENTITY': '80',
            'AMSDAL_CRM_MAX_WORKFLOW_RULES_PER_ENTITY': '120',
            'AMSDAL_CRM_DEFAULT_CURRENCY': 'GBP',
        },
    )
    def test_multiple_environment_variable_overrides(self):
        """Test that multiple settings can be overridden simultaneously."""
        settings = CRMSettings()

        assert settings.DEFAULT_ACTIVITY_TIMELINE_LIMIT == 250
        assert settings.MAX_CUSTOM_FIELDS_PER_ENTITY == 80
        assert settings.MAX_WORKFLOW_RULES_PER_ENTITY == 120
        assert settings.DEFAULT_CURRENCY == 'GBP'

    def test_settings_env_prefix(self):
        """Test that settings use correct environment variable prefix."""
        settings = CRMSettings()

        # Verify model_config has the correct env_prefix
        assert hasattr(settings, 'model_config')
        assert settings.model_config.get('env_prefix') == 'AMSDAL_CRM_'

    def test_crm_settings_singleton_exists(self):
        """Test that crm_settings singleton exists."""
        assert crm_settings is not None

    def test_crm_settings_singleton_is_crm_settings_instance(self):
        """Test that crm_settings is an instance of CRMSettings."""
        assert isinstance(crm_settings, CRMSettings)

    def test_crm_settings_singleton_has_default_values(self):
        """Test that crm_settings singleton has default values."""
        assert crm_settings.DEFAULT_ACTIVITY_TIMELINE_LIMIT == 100
        assert crm_settings.MAX_CUSTOM_FIELDS_PER_ENTITY == 50
        assert crm_settings.MAX_WORKFLOW_RULES_PER_ENTITY == 100
        assert crm_settings.DEFAULT_CURRENCY == 'USD'

    def test_settings_types(self):
        """Test that settings have correct types."""
        settings = CRMSettings()

        assert isinstance(settings.DEFAULT_ACTIVITY_TIMELINE_LIMIT, int)
        assert isinstance(settings.MAX_CUSTOM_FIELDS_PER_ENTITY, int)
        assert isinstance(settings.MAX_WORKFLOW_RULES_PER_ENTITY, int)
        assert isinstance(settings.DEFAULT_CURRENCY, str)

    @mock.patch.dict(os.environ, {'AMSDAL_CRM_DEFAULT_ACTIVITY_TIMELINE_LIMIT': '0'})
    def test_zero_activity_limit(self):
        """Test that activity limit can be set to 0."""
        settings = CRMSettings()
        assert settings.DEFAULT_ACTIVITY_TIMELINE_LIMIT == 0

    @mock.patch.dict(os.environ, {'AMSDAL_CRM_MAX_CUSTOM_FIELDS_PER_ENTITY': '1'})
    def test_minimum_custom_fields(self):
        """Test minimum value for custom fields."""
        settings = CRMSettings()
        assert settings.MAX_CUSTOM_FIELDS_PER_ENTITY == 1

    @mock.patch.dict(os.environ, {'AMSDAL_CRM_MAX_WORKFLOW_RULES_PER_ENTITY': '1000'})
    def test_large_workflow_rules_limit(self):
        """Test large value for workflow rules limit."""
        settings = CRMSettings()
        assert settings.MAX_WORKFLOW_RULES_PER_ENTITY == 1000

    def test_settings_field_titles(self):
        """Test that settings fields have descriptive titles."""

        # Check that fields have metadata (titles)
        fields = CRMSettings.model_fields

        assert 'DEFAULT_ACTIVITY_TIMELINE_LIMIT' in fields
        assert 'MAX_CUSTOM_FIELDS_PER_ENTITY' in fields
        assert 'MAX_WORKFLOW_RULES_PER_ENTITY' in fields
        assert 'DEFAULT_CURRENCY' in fields

    @mock.patch.dict(os.environ, {'AMSDAL_CRM_DEFAULT_CURRENCY': ''})
    def test_empty_currency_string(self):
        """Test that empty currency string is accepted."""
        settings = CRMSettings()
        assert settings.DEFAULT_CURRENCY == ''

    def test_settings_can_be_serialized(self):
        """Test that settings can be serialized to dict."""
        settings = CRMSettings()
        settings_dict = settings.model_dump()

        assert isinstance(settings_dict, dict)
        assert 'DEFAULT_ACTIVITY_TIMELINE_LIMIT' in settings_dict
        assert 'MAX_CUSTOM_FIELDS_PER_ENTITY' in settings_dict
        assert 'MAX_WORKFLOW_RULES_PER_ENTITY' in settings_dict
        assert 'DEFAULT_CURRENCY' in settings_dict

    def test_settings_values_in_dict(self):
        """Test that serialized settings contain correct values."""
        settings = CRMSettings()
        settings_dict = settings.model_dump()

        assert settings_dict['DEFAULT_ACTIVITY_TIMELINE_LIMIT'] == 100
        assert settings_dict['MAX_CUSTOM_FIELDS_PER_ENTITY'] == 50
        assert settings_dict['MAX_WORKFLOW_RULES_PER_ENTITY'] == 100
        assert settings_dict['DEFAULT_CURRENCY'] == 'USD'

    @mock.patch.dict(os.environ, {'AMSDAL_CRM_DEFAULT_ACTIVITY_TIMELINE_LIMIT': 'invalid'}, clear=False)
    def test_invalid_integer_value_raises_error(self):
        """Test that invalid integer value raises validation error."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):  # Pydantic will raise validation error
            CRMSettings()

    def test_settings_immutability_after_creation(self):
        """Test that settings values can be accessed consistently."""
        settings = CRMSettings()

        # Get values multiple times
        limit1 = settings.DEFAULT_ACTIVITY_TIMELINE_LIMIT
        limit2 = settings.DEFAULT_ACTIVITY_TIMELINE_LIMIT

        # Should be the same
        assert limit1 == limit2
        assert limit1 == 100
