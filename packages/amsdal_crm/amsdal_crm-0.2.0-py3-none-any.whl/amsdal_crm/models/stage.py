"""Stage Model."""

from typing import ClassVar
from typing import Literal

from amsdal_models.classes.data_models.indexes import IndexInfo
from amsdal_models.classes.model import Model
from amsdal_models.managers.model_manager import Manager
from amsdal_utils.models.enums import ModuleType
from pydantic import ConfigDict
from pydantic.fields import Field


class StageManager(Manager):
    def get_queryset(self) -> 'StageManager':
        return super().get_queryset().select_related('pipeline')


class Stage(Model):
    """Pipeline stage model.

    Represents a stage within a sales pipeline with win probability
    and closed status indicators.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    objects = StageManager()

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    __indexes__: ClassVar[list[IndexInfo]] = [
        IndexInfo(name='idx_stage_order', field='order'),
    ]

    pipeline: 'Pipeline' = Field(title='Pipeline')
    name: str = Field(title='Stage Name')
    description: str | None = Field(default=None, title='Description')
    order: int = Field(title='Order')
    probability: float = Field(default=0.0, title='Win Probability (%)', ge=0, le=100)

    status: Literal['open', 'closed_won', 'closed_lost'] = Field(default='open', title='Status')

    @property
    def display_name(self) -> str:
        """Return display name for the stage."""
        if isinstance(self.pipeline, str):
            return f'{self.pipeline} - {self.name}'
        return f'{self.pipeline.display_name} - {self.name}'


from amsdal_crm.models.pipeline import Pipeline

Stage.model_rebuild()
