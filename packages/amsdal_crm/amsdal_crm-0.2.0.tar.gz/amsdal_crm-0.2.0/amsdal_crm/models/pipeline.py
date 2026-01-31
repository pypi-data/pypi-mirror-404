"""Pipeline Model."""

from typing import ClassVar

from amsdal_models.classes.data_models.constraints import UniqueConstraint
from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class Pipeline(Model):
    """Sales pipeline model.

    Represents a sales pipeline with multiple stages.
    Pipelines are system-wide and not owned by individual users.
    """

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    __constraints__: ClassVar[list[UniqueConstraint]] = [UniqueConstraint(name='unq_pipeline_name', fields=['name'])]

    name: str = Field(title='Pipeline Name')
    description: str | None = Field(default=None, title='Description')
    is_active: bool = Field(default=True, title='Is Active')

    @property
    def display_name(self) -> str:
        """Return display name for the pipeline."""
        return self.name
