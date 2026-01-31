"""CRM Constants and Enums."""

from enum import Enum


class CRMLifecycleEvent(str, Enum):
    """Custom lifecycle events for CRM operations."""

    ON_DEAL_STAGE_CHANGE = 'on_deal_stage_change'
    ON_DEAL_WON = 'on_deal_won'
    ON_DEAL_LOST = 'on_deal_lost'
    ON_CONTACT_MERGE = 'on_contact_merge'
    ON_ACCOUNT_MERGE = 'on_account_merge'
