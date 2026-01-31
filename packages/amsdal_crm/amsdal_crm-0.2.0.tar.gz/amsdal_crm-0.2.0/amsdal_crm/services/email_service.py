"""EmailService for email integration."""

from amsdal_data.transactions.decorators import async_transaction
from amsdal_data.transactions.decorators import transaction

from amsdal_crm.models.activity import ActivityRelatedTo
from amsdal_crm.models.activity import ActivityType
from amsdal_crm.models.activity import EmailActivity


class EmailService:
    """Service for email integration and logging."""

    @classmethod
    @transaction
    def log_email(
        cls,
        subject: str,
        body: str,
        from_address: str,
        to_addresses: list[str],
        cc_addresses: list[str] | None,
        related_to_type: ActivityRelatedTo,
        related_to_id: str,
        *,
        is_outbound: bool = True,
    ) -> EmailActivity:
        """Log an email as an activity.

        This can be called when:
        - User sends email from CRM
        - Incoming email is parsed and associated with CRM record

        Args:
            subject: Email subject
            body: Email body
            from_address: Sender email address
            to_addresses: List of recipient email addresses
            cc_addresses: List of CC email addresses
            related_to_type: Type of related record (Entity, Deal)
            related_to_id: ID of related record
            is_outbound: True if sent from CRM, False if received

        Returns:
            The created EmailActivity
        """
        email_activity = EmailActivity(
            activity_type=ActivityType.EMAIL,
            subject=subject,
            body=body,
            from_address=from_address,
            to_addresses=to_addresses,
            cc_addresses=cc_addresses,
            related_to_type=related_to_type,
            related_to_id=related_to_id,
            is_outbound=is_outbound,
            description=f'Email: {subject}',
            due_date=None,
            completed_at=None,
            is_completed=False,
        )
        email_activity.save(force_insert=True)

        return email_activity

    @classmethod
    @async_transaction
    async def alog_email(
        cls,
        subject: str,
        body: str,
        from_address: str,
        to_addresses: list[str],
        cc_addresses: list[str] | None,
        related_to_type: ActivityRelatedTo,
        related_to_id: str,
        *,
        is_outbound: bool = True,
    ) -> EmailActivity:
        """Async version of log_email.

        Args:
            subject: Email subject
            body: Email body
            from_address: Sender email address
            to_addresses: List of recipient email addresses
            cc_addresses: List of CC email addresses
            related_to_type: Type of related record (Entity, Deal)
            related_to_id: ID of related record
            is_outbound: True if sent from CRM, False if received

        Returns:
            The created EmailActivity
        """
        email_activity = EmailActivity(
            activity_type=ActivityType.EMAIL,
            subject=subject,
            body=body,
            from_address=from_address,
            to_addresses=to_addresses,
            cc_addresses=cc_addresses,
            related_to_type=related_to_type,
            related_to_id=related_to_id,
            is_outbound=is_outbound,
            description=f'Email: {subject}',
            due_date=None,
            completed_at=None,
            is_completed=False,
        )
        await email_activity.asave(force_insert=True)

        return email_activity
