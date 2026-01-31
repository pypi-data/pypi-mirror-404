"""CustomFieldDefinition Model."""

from typing import Any
from typing import ClassVar
from typing import Literal

from amsdal_models.classes.data_models.constraints import UniqueConstraint
from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class CustomFieldDefinition(Model):
    """Metadata about custom fields available for CRM entities.

    Defines custom fields that users can add to Contacts, Accounts, or Deals.
    Field values are stored in the entity's custom_fields JSON dict.
    """

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    __constraints__: ClassVar[list[UniqueConstraint]] = [
        UniqueConstraint(name='unq_custom_field_entity_name', fields=['entity_type', 'field_name'])
    ]

    entity_type: Literal[
        'Entity', 'EntityRelationship', 'Deal', 'EntityIdentifier', 'EntityContactPoint', 'EntityAddress'
    ] = Field(title='Entity Type')
    field_name: str = Field(title='Field Name')
    field_label: str = Field(title='Field Label')
    field_type: Literal['text', 'number', 'date', 'choice'] = Field(title='Field Type')

    # For choice fields
    choices: list[str] | None = Field(default=None, title='Choices (for choice type)')

    # Validation
    is_required: bool = Field(default=False, title='Is Required')
    default_value: Any | None = Field(default=None, title='Default Value')

    # Display
    help_text: str | None = Field(default=None, title='Help Text')
    display_order: int = Field(default=0, title='Display Order')

    @property
    def display_name(self) -> str:
        """Return display name for the custom field definition."""
        return f'{self.entity_type}.{self.field_name}'
