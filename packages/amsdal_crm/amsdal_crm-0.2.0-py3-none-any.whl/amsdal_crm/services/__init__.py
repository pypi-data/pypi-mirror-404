"""CRM Services."""

from amsdal_crm.services.activity_service import ActivityService
from amsdal_crm.services.custom_field_service import CustomFieldService
from amsdal_crm.services.deal_service import DealService
from amsdal_crm.services.email_service import EmailService
from amsdal_crm.services.workflow_service import WorkflowService

__all__ = [
    'ActivityService',
    'CustomFieldService',
    'DealService',
    'EmailService',
    'WorkflowService',
]
