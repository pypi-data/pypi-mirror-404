"""Attachment Model."""

import datetime as _dt
from typing import ClassVar
from typing import Literal

from amsdal.models.core.file import File
from amsdal_models.classes.data_models.indexes import IndexInfo
from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class Attachment(Model):
    """Explicit attachment model for tracking file relationships.

    Uses polymorphic relationship to link files to Contacts, Accounts,
    Deals, or Activities.
    """

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    __indexes__: ClassVar[list[IndexInfo]] = [
        IndexInfo(name='idx_attachment_related_to', field='related_to_id'),
        IndexInfo(name='idx_attachment_uploaded_at', field='uploaded_at'),
    ]

    file: File = Field(title='File')

    # Polymorphic relationship
    related_to_type: Literal['Entity', 'Deal', 'Activity'] = Field(title='Related To Type')
    related_to_id: str = Field(title='Related To ID')

    # Metadata
    uploaded_by: str = Field(title='Uploaded By (User Email)')
    uploaded_at: _dt.datetime = Field(default_factory=lambda: _dt.datetime.now(_dt.UTC), title='Uploaded At')
    description: str | None = Field(default=None, title='Description')

    @property
    def display_name(self) -> str:
        """Return display name for the attachment."""
        if hasattr(self.file, 'filename'):
            return self.file.filename
        return f'Attachment {self._object_id}'
