"""Account Model."""

from typing import Any
from typing import ClassVar
from typing import Literal

from amsdal.contrib.auth.models.user import User
from amsdal.models.mixins import TimestampMixin
from amsdal_models.classes.data_models.constraints import UniqueConstraint
from amsdal_models.classes.data_models.indexes import IndexInfo
from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class Entity(TimestampMixin, Model):
    """Entity (Person/Organization/Trust) model.

    Represents a company or organization in the CRM system.
    Owned by individual users with permission controls.
    """

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    __constraints__: ClassVar[list[UniqueConstraint]] = [UniqueConstraint(name='unq_entity_name', fields=['name'])]
    __indexes__: ClassVar[list[IndexInfo]] = [
        IndexInfo(name='idx_entity_created_at', field='created_at'),
    ]

    # Core fields
    name: str = Field(title='Entity Name')
    legal_name: str | None = Field(default=None, title='Legal Name')
    status: Literal['Active', 'Inactive'] = Field(default='Active', title='Status')
    note: str | None = Field(default=None, title='Note')

    assigned_to: User | None = Field(default=None, title='Assigned To')

    # Custom fields (JSON)
    custom_fields: dict[str, Any] | None = Field(default=None, title='Custom Fields')

    @property
    def display_name(self) -> str:
        """Return display name for the account."""
        return self.name

    def has_object_permission(self, user: 'User', action: str) -> bool:
        """Check if user has permission to perform action on this account.

        Args:
            user: The user attempting the action
            action: The action being attempted (read, create, update, delete)

        Returns:
            True if user has permission, False otherwise
        """
        if self.assigned_to and self.assigned_to.email == user.email:
            return True

        # Check admin permissions
        if user.permissions:
            for permission in user.permissions:
                if permission.model == '*' and permission.action in ('*', action):
                    return True
                if permission.model == 'Entity' and permission.action in ('*', action):
                    return True

        return False

    def pre_create(self) -> None:
        """Hook called before creating account."""
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = CustomFieldService.validate_custom_fields('Entity', self.custom_fields)
        super().pre_create()

    async def apre_create(self) -> None:
        """Async hook called before creating account."""
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = await CustomFieldService.avalidate_custom_fields('Entity', self.custom_fields)
        await super().apre_create()

    def pre_update(self) -> None:
        """Hook called before updating account."""
        # Validate custom fields first
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = CustomFieldService.validate_custom_fields('Entity', self.custom_fields)

        # Call parent to handle timestamps
        super().pre_update()

    async def apre_update(self) -> None:
        """Async hook called before updating account."""
        # Validate custom fields first
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = await CustomFieldService.avalidate_custom_fields('Entity', self.custom_fields)

        # Call parent to handle timestamps
        await super().apre_update()

    def post_update(self) -> None:
        """Hook called after updating account."""
        from amsdal_crm.services.workflow_service import WorkflowService

        WorkflowService.execute_rules('Entity', 'update', self)

    async def apost_update(self) -> None:
        """Async hook called after updating account."""
        from amsdal_crm.services.workflow_service import WorkflowService

        await WorkflowService.aexecute_rules('Entity', 'update', self)


class EntityRelationship(TimestampMixin, Model):
    from_entity: Entity = Field(title='From Entity')
    to_entity: Entity = Field(title='To Entity')
    start_date: str | None = Field(default=None, title='Start Date')
    end_date: str | None = Field(default=None, title='End Date')
    relationship_group_name: str | None = Field(default=None, title='Relationship Group Name')

    def pre_create(self) -> None:
        """Hook called before creating account."""
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = CustomFieldService.validate_custom_fields('EntityRelationship', self.custom_fields)
        super().pre_create()

    async def apre_create(self) -> None:
        """Async hook called before creating account."""
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = await CustomFieldService.avalidate_custom_fields(
                'EntityRelationship', self.custom_fields
            )
        await super().apre_create()

    def pre_update(self) -> None:
        """Hook called before updating account."""
        # Validate custom fields first
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = CustomFieldService.validate_custom_fields('EntityRelationship', self.custom_fields)

        # Call parent to handle timestamps
        super().pre_update()

    async def apre_update(self) -> None:
        """Async hook called before updating account."""
        # Validate custom fields first
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = await CustomFieldService.avalidate_custom_fields(
                'EntityRelationship', self.custom_fields
            )

            # Call parent to handle timestamps
            await super().apre_update()


class EntityIdentifier(TimestampMixin, Model):
    entity: Entity = Field(title='Entity')
    value: str = Field(title='Identifier Value')
    country: str | None = Field(default=None, title='Country')

    # TODO: validate one per entity
    is_primary: bool = Field(default=False, title='Is Primary')

    def pre_create(self) -> None:
        """Hook called before creating account."""
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = CustomFieldService.validate_custom_fields('EntityIdentifier', self.custom_fields)
        super().pre_create()

    async def apre_create(self) -> None:
        """Async hook called before creating account."""
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = await CustomFieldService.avalidate_custom_fields(
                'EntityIdentifier', self.custom_fields
            )
        await super().apre_create()

    def pre_update(self) -> None:
        """Hook called before updating account."""
        # Validate custom fields first
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = CustomFieldService.validate_custom_fields('EntityIdentifier', self.custom_fields)

        # Call parent to handle timestamps
        super().pre_update()

    async def apre_update(self) -> None:
        """Async hook called before updating account."""
        # Validate custom fields first
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = await CustomFieldService.avalidate_custom_fields(
                'EntityIdentifier', self.custom_fields
            )

            # Call parent to handle timestamps
            await super().apre_update()


class EntityContactPoint(TimestampMixin, Model):
    entity: Entity = Field(title='Entity')
    value: str = Field(title='Contact Point Value')

    # TODO: validate one per entity
    is_primary: bool = Field(default=False, title='Is Primary')
    can_contact: bool = Field(default=True, title='Can Contact')

    def pre_create(self) -> None:
        """Hook called before creating account."""
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = CustomFieldService.validate_custom_fields('EntityContactPoint', self.custom_fields)
        super().pre_create()

    async def apre_create(self) -> None:
        """Async hook called before creating account."""
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = await CustomFieldService.avalidate_custom_fields(
                'EntityContactPoint', self.custom_fields
            )
        await super().apre_create()

    def pre_update(self) -> None:
        """Hook called before updating account."""
        # Validate custom fields first
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = CustomFieldService.validate_custom_fields('EntityContactPoint', self.custom_fields)

        # Call parent to handle timestamps
        super().pre_update()

    async def apre_update(self) -> None:
        """Async hook called before updating account."""
        # Validate custom fields first
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = await CustomFieldService.avalidate_custom_fields(
                'EntityContactPoint', self.custom_fields
            )

            # Call parent to handle timestamps
            await super().apre_update()


class EntityAddress(TimestampMixin, Model):
    line1: str | None = Field(title='Address Line 1')
    line2: str | None = Field(default=None, title='Address Line 2')
    city: str | None = Field(title='City')
    region: str | None = Field(default=None, title='Region/State')
    postal_code: str | None = Field(default=None, title='Postal Code')
    country: str | None = Field(title='Country')

    # TODO: validate one per entity
    is_primary: bool = Field(default=False, title='Is Primary')

    def pre_create(self) -> None:
        """Hook called before creating account."""
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = CustomFieldService.validate_custom_fields('EntityAddress', self.custom_fields)
        super().pre_create()

    async def apre_create(self) -> None:
        """Async hook called before creating account."""
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = await CustomFieldService.avalidate_custom_fields('EntityAddress', self.custom_fields)
        await super().apre_create()

    def pre_update(self) -> None:
        """Hook called before updating account."""
        # Validate custom fields first
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = CustomFieldService.validate_custom_fields('EntityAddress', self.custom_fields)

        # Call parent to handle timestamps
        super().pre_update()

    async def apre_update(self) -> None:
        """Async hook called before updating account."""
        # Validate custom fields first
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = await CustomFieldService.avalidate_custom_fields('EntityAddress', self.custom_fields)

            # Call parent to handle timestamps
            await super().apre_update()
