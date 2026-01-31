"""CRM Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class CRMSettings(BaseSettings):
    """Settings for the CRM module."""

    model_config = SettingsConfigDict(env_prefix='AMSDAL_CRM_')

    # Activity settings
    DEFAULT_ACTIVITY_TIMELINE_LIMIT: int = Field(100, title='Default Activity Timeline Limit')

    # Custom field settings
    MAX_CUSTOM_FIELDS_PER_ENTITY: int = Field(50, title='Max Custom Fields Per Entity')

    # Workflow settings
    MAX_WORKFLOW_RULES_PER_ENTITY: int = Field(100, title='Max Workflow Rules Per Entity')

    # Deal settings
    DEFAULT_CURRENCY: str = Field('USD', title='Default Currency')


crm_settings = CRMSettings()
