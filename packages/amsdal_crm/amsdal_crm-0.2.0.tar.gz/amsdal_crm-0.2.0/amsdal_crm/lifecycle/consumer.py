"""CRM Lifecycle Consumers."""

from typing import TYPE_CHECKING
from typing import Any

from amsdal_utils.lifecycle.consumer import LifecycleConsumer
from amsdal_utils.models.data_models.address import Address
from amsdal_utils.models.enums import Versions

if TYPE_CHECKING:
    from amsdal_crm.models.deal import Deal

# Entity types that support custom fields
CRM_ENTITY_TYPES = {'Entity', 'EntityRelationship', 'Deal', 'EntityIdentifier', 'EntityContactPoint', 'EntityAddress'}


class LoadCRMFixturesConsumer(LifecycleConsumer):
    """Consumer that loads CRM fixtures on server startup."""

    def on_event(self) -> None:
        """Load CRM fixtures (pipelines, stages, permissions)."""
        # Note: Fixtures are typically loaded via the FixturesManager
        # This consumer can be used for additional setup if needed
        pass

    async def on_event_async(self) -> None:
        """Async version of on_event."""
        pass


class DealWonNotificationConsumer(LifecycleConsumer):
    """Consumer that handles deal won events.

    Placeholder for future notification system integration.
    """

    def on_event(self, deal: 'Deal', user_email: str) -> None:
        """Handle deal won event.

        Args:
            deal: The deal that was won
            user_email: Email of user who closed the deal
        """
        # TODO: Implement notification logic
        # Could integrate with email service, Slack, etc.
        pass

    async def on_event_async(self, deal: 'Deal', user_email: str) -> None:
        """Async version of on_event."""
        pass


def _custom_field_def_to_control(field_def: Any, values: dict[str, Any]) -> dict[str, Any]:
    """Convert a CustomFieldDefinition to a frontend control config.

    Args:
        field_def: A CustomFieldDefinition instance with metadata about a custom field

    Returns:
        A dictionary representing the frontend control configuration
    """
    control: dict[str, Any] = {
        'name': f'{field_def.field_name}',
        'label': field_def.field_label,
        'required': field_def.is_required,
    }

    if field_def.help_text:
        control['description'] = field_def.help_text

    if field_def.default_value is not None:
        control['value'] = field_def.default_value

    if field_def.field_type == 'text':
        control['type'] = 'text'
    elif field_def.field_type == 'number':
        control['type'] = 'number'
    elif field_def.field_type == 'date':
        control['type'] = 'date'
    elif field_def.field_type == 'choice':
        control['type'] = 'select'
        if field_def.choices:
            control['options'] = [{'label': choice, 'value': choice} for choice in field_def.choices]

    if values and field_def.field_name in values:
        control['value'] = values[field_def.field_name]

    return control


def _add_custom_fields_to_control(control: dict[str, Any], custom_field_controls: list[dict[str, Any]]) -> None:
    """Add custom field controls to the main control configuration.

    Args:
        control: The main frontend control configuration
        custom_field_controls: List of custom field control configurations
    """
    if not custom_field_controls:
        return

    if 'controls' not in control:
        control['controls'] = []

    # Find the custom_fields control and update it, or append custom fields at the end
    custom_fields_control = None
    for ctrl in control.get('controls', []):
        if ctrl.get('name') == 'custom_fields':
            custom_fields_control = ctrl
            break

    if custom_fields_control:
        # Update the custom_fields control to be a group with nested controls
        custom_fields_control['type'] = 'group'
        custom_fields_control['controls'] = custom_field_controls
        if 'control' in custom_fields_control:
            custom_fields_control.pop('control', None)
    else:
        # Add custom fields as a new group at the end
        control['controls'].append(
            {
                'type': 'group',
                'name': 'custom_fields',
                'label': 'Custom Fields',
                'controls': custom_field_controls,
            }
        )


def _get_values_from_response(response: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]:
    """
    Extracts values from a response dictionary or list of dictionaries.

    This function processes a response to extract the relevant values. It checks if the response
    is a dictionary containing a 'rows' key and processes the rows to find the appropriate values.
    If the response is not in the expected format, it returns an empty dictionary.

    Args:
        response (dict[str, Any] | list[dict[str, Any]]): The response to extract values from.

    Returns:
        dict[str, Any]: A dictionary containing the extracted values.
    """
    if not isinstance(response, dict) or 'rows' not in response or not response['rows']:
        return {}

    for row in response['rows']:
        if '_metadata' in row and row['_metadata'].get('next_version') is None:
            return row

    return response['rows'][0]


def get_values_from_response(response: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]:
    _values = _get_values_from_response(response)
    if 'custom_fields' in _values:
        return _values['custom_fields']
    return {}


class CustomAttributesFrontendConfigConsumer(LifecycleConsumer):
    """Consumer that propagates custom attributes into frontend config.

    This consumer listens to response events and adds custom field definitions
    as frontend controls for CRM entities (Contact, Account, Deal).
    """

    def on_event(
        self,
        request: Any,
        response: dict[str, Any],
    ) -> None:
        """Handle response event by adding custom field controls.

        Args:
            request: The request object containing query and path parameters.
            response: The response dictionary to be processed.
        """
        from amsdal_crm.models.custom_field_definition import CustomFieldDefinition

        class_name = self._extract_class_name(request)

        if class_name not in CRM_ENTITY_TYPES:
            return

        if not isinstance(response, dict) or 'control' not in response:
            return

        values = get_values_from_response(response)

        custom_field_defs = list(
            CustomFieldDefinition.objects.filter(
                entity_type=class_name,
                _metadata__is_deleted=False,
                _address__object_version=Versions.LATEST,
            ).execute()
        )

        if not custom_field_defs:
            return

        # Sort by display_order
        custom_field_defs.sort(key=lambda x: x.display_order)

        custom_field_controls = [
            _custom_field_def_to_control(field_def, values=values) for field_def in custom_field_defs
        ]

        _add_custom_fields_to_control(response['control'], custom_field_controls)

    async def on_event_async(
        self,
        request: Any,
        response: dict[str, Any],
    ) -> None:
        """Async version of on_event.

        Args:
            request: The request object containing query and path parameters.
            response: The response dictionary to be processed.
        """
        from amsdal_crm.models.custom_field_definition import CustomFieldDefinition

        class_name = self._extract_class_name(request)

        if class_name not in CRM_ENTITY_TYPES:
            return

        if not isinstance(response, dict) or 'control' not in response:
            return

        values = get_values_from_response(response)

        custom_field_defs = list(
            await CustomFieldDefinition.objects.filter(
                entity_type=class_name,
                _metadata__is_deleted=False,
                _address__object_version=Versions.LATEST,
            ).aexecute()
        )

        if not custom_field_defs:
            return

        # Sort by display_order
        custom_field_defs.sort(key=lambda x: x.display_order)

        custom_field_controls = [
            _custom_field_def_to_control(field_def, values=values) for field_def in custom_field_defs
        ]

        _add_custom_fields_to_control(response['control'], custom_field_controls)

    @staticmethod
    def _extract_class_name(request: Any) -> str | None:
        """Extract class name from request.

        Args:
            request: The request object

        Returns:
            The class name or None if not found
        """
        if hasattr(request, 'query_params') and 'class_name' in request.query_params:
            return request.query_params['class_name']

        if hasattr(request, 'path_params') and 'address' in request.path_params:
            return Address.from_string(request.path_params['address']).class_name

        return None
