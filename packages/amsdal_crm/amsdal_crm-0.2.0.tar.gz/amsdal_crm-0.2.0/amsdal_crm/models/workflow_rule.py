"""WorkflowRule Model."""

from typing import Any
from typing import ClassVar
from typing import Literal

from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class WorkflowRule(Model):
    """Configuration for workflow automation rules.

    Defines rules that trigger actions when certain conditions are met
    on CRM entities (create, update, delete events).
    """

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB

    name: str = Field(title='Rule Name')
    entity_type: Literal['Entity', 'Deal', 'Activity'] = Field(title='Entity Type')

    # Trigger
    trigger_event: Literal['create', 'update', 'delete'] = Field(title='Trigger Event')

    # Condition (simplified - single field condition)
    condition_field: str | None = Field(None, title='Condition Field')
    condition_operator: Literal['equals', 'not_equals', 'contains', 'greater_than', 'less_than'] | None = Field(
        default=None, title='Condition Operator'
    )
    condition_value: Any | None = Field(None, title='Condition Value')

    # Action
    action_type: Literal['update_field', 'create_activity', 'send_notification'] = Field(title='Action Type')
    action_config: dict[str, Any] = Field(title='Action Configuration')

    # Status
    is_active: bool = Field(default=True, title='Is Active')

    @property
    def display_name(self) -> str:
        """Return display name for the workflow rule."""
        return f'{self.entity_type}: {self.name}'
