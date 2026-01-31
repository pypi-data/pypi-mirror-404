"""CustomFieldService for validating custom field values."""

from datetime import datetime
from decimal import Decimal
from decimal import InvalidOperation
from typing import Any

from amsdal_utils.models.enums import Versions

from amsdal_crm.errors import CustomFieldValidationError
from amsdal_crm.models.custom_field_definition import CustomFieldDefinition


class CustomFieldService:
    """Service for validating custom field values against their definitions."""

    @classmethod
    def validate_custom_fields(cls, entity_type: str, custom_fields: dict[str, Any] | None) -> dict[str, Any]:
        """Validate custom field values against their definitions.

        Args:
            entity_type: The entity type (Contact, Account, Deal)
            custom_fields: Dictionary of custom field values

        Returns:
            Validated custom_fields dict

        Raises:
            CustomFieldValidationError: If validation fails
        """
        if not custom_fields:
            return {}

        # Load field definitions for this entity type
        definitions = CustomFieldDefinition.objects.filter(
            entity_type=entity_type, _address__object_version=Versions.LATEST
        ).execute()

        definitions_by_name = {d.field_name: d for d in definitions}
        validated = {}

        for field_name, value in custom_fields.items():
            if field_name not in definitions_by_name:
                msg = f'Unknown custom field: {field_name} for {entity_type}'
                raise CustomFieldValidationError(msg)

            definition = definitions_by_name[field_name]

            # Required check
            if definition.is_required and value is None:
                msg = f'Required custom field {field_name} is missing'
                raise CustomFieldValidationError(msg)

            # Type validation
            if value is not None:
                validated[field_name] = cls._validate_field_value(definition, value)

        return validated

    @classmethod
    async def avalidate_custom_fields(cls, entity_type: str, custom_fields: dict[str, Any] | None) -> dict[str, Any]:
        """Validate custom field values against their definitions.

        Args:
            entity_type: The entity type (Contact, Account, Deal)
            custom_fields: Dictionary of custom field values

        Returns:
            Validated custom_fields dict

        Raises:
            CustomFieldValidationError: If validation fails
        """
        if not custom_fields:
            return {}

        # Load field definitions for this entity type
        definitions = await CustomFieldDefinition.objects.filter(
            entity_type=entity_type, _address__object_version=Versions.LATEST
        ).aexecute()

        definitions_by_name = {d.field_name: d for d in definitions}
        validated = {}

        for field_name, value in custom_fields.items():
            if field_name not in definitions_by_name:
                msg = f'Unknown custom field: {field_name} for {entity_type}'
                raise CustomFieldValidationError(msg)

            definition = definitions_by_name[field_name]

            # Required check
            if definition.is_required and value is None:
                msg = f'Required custom field {field_name} is missing'
                raise CustomFieldValidationError(msg)

            # Type validation
            if value is not None:
                validated[field_name] = cls._validate_field_value(definition, value)

        return validated

    @classmethod
    def _validate_field_value(cls, definition: CustomFieldDefinition, value: Any) -> Any:
        """Validate a single field value against its definition.

        Args:
            definition: The field definition
            value: The value to validate

        Returns:
            The validated (and potentially converted) value

        Raises:
            CustomFieldValidationError: If validation fails
        """
        if definition.field_type == 'text':
            return str(value)

        elif definition.field_type == 'number':
            try:
                return Decimal(str(value))
            except (InvalidOperation, ValueError) as exc:
                msg = f'Invalid number for field {definition.field_name}: {value}'
                raise CustomFieldValidationError(msg) from exc

        elif definition.field_type == 'date':
            if isinstance(value, datetime):
                return value.isoformat()
            # Try parsing ISO format
            try:
                return datetime.fromisoformat(value).isoformat()
            except (ValueError, AttributeError) as exc:
                msg = f'Invalid date for field {definition.field_name}: {value}'
                raise CustomFieldValidationError(msg) from exc

        elif definition.field_type == 'choice':
            if definition.choices and value not in definition.choices:
                msg = f'Invalid choice for field {definition.field_name}: {value}. Must be one of {definition.choices}'
                raise CustomFieldValidationError(msg)
            return value

        return value
