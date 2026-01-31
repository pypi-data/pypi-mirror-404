"""Integration tests for EmailService."""

from amsdal.manager import AmsdalManager

from amsdal_crm.models.activity import ActivityRelatedTo
from amsdal_crm.models.activity import ActivityType
from amsdal_crm.models.activity import EmailActivity
from amsdal_crm.services.email_service import EmailService


def test_log_email_outbound(crm_manager: AmsdalManager, mock_user):
    """Test logging an outbound email."""
    subject = 'Proposal for Q2'
    body = 'Please find attached our proposal for Q2...'
    from_address = 'sales@example.com'
    to_addresses = ['client@example.com']
    cc_addresses = ['manager@example.com']
    related_to_type = ActivityRelatedTo.DEAL
    related_to_id = 'deal_123'

    email = EmailService.log_email(
        subject=subject,
        body=body,
        from_address=from_address,
        to_addresses=to_addresses,
        cc_addresses=cc_addresses,
        related_to_type=related_to_type,
        related_to_id=related_to_id,
        is_outbound=True,
    )

    # Verify EmailActivity was created correctly
    assert email.activity_type == ActivityType.EMAIL
    assert email.subject == subject
    assert email.body == body
    assert email.from_address == from_address
    assert email.to_addresses == to_addresses
    assert email.cc_addresses == cc_addresses
    assert email.related_to_type == related_to_type
    assert email.related_to_id == related_to_id
    assert email.is_outbound is True
    assert email.description == f'Email: {subject}'

    # Verify it was saved to database
    saved_emails = EmailActivity.objects.filter(subject=subject).execute()
    assert len(saved_emails) == 1
    assert saved_emails[0].subject == subject


def test_log_email_inbound(crm_manager: AmsdalManager, mock_user):
    """Test logging an inbound email."""
    subject = 'Re: Proposal for Q2'
    body = 'Thanks for the proposal. We have some questions...'
    from_address = 'client@example.com'
    to_addresses = ['sales@example.com']
    cc_addresses = None
    related_to_type = ActivityRelatedTo.DEAL
    related_to_id = 'deal_123'

    email = EmailService.log_email(
        subject=subject,
        body=body,
        from_address=from_address,
        to_addresses=to_addresses,
        cc_addresses=cc_addresses,
        related_to_type=related_to_type,
        related_to_id=related_to_id,
        is_outbound=False,
    )

    # Verify inbound email
    assert email.is_outbound is False
    assert email.from_address == from_address
    assert email.cc_addresses is None


def test_log_email_default_outbound(crm_manager: AmsdalManager, mock_user):
    """Test that is_outbound defaults to True."""
    email = EmailService.log_email(
        subject='Test',
        body='Test body',
        from_address='sender@example.com',
        to_addresses=['recipient@example.com'],
        cc_addresses=None,
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id='entity_123',
    )

    # Default should be outbound
    assert email.is_outbound is True


def test_log_email_to_entity(crm_manager: AmsdalManager, mock_user):
    """Test logging email related to entity."""
    entity_id = 'entity_456'

    email = EmailService.log_email(
        subject='Welcome!',
        body='Welcome to our service',
        from_address='onboarding@example.com',
        to_addresses=['contact@example.com'],
        cc_addresses=None,
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id=entity_id,
    )

    assert email.related_to_type == ActivityRelatedTo.ENTITY
    assert email.related_to_id == entity_id


def test_log_email_to_deal(crm_manager: AmsdalManager, mock_user):
    """Test logging email related to deal."""
    deal_id = 'deal_789'

    email = EmailService.log_email(
        subject='Quarterly Review',
        body='Time for our quarterly business review',
        from_address='account-manager@example.com',
        to_addresses=['client@example.com'],
        cc_addresses=None,
        related_to_type=ActivityRelatedTo.DEAL,
        related_to_id=deal_id,
    )

    assert email.related_to_type == ActivityRelatedTo.DEAL
    assert email.related_to_id == deal_id


def test_log_email_with_multiple_recipients(crm_manager: AmsdalManager, mock_user):
    """Test logging email with multiple recipients."""
    to_addresses = ['client1@example.com', 'client2@example.com', 'client3@example.com']
    cc_addresses = ['manager@example.com', 'director@example.com']

    email = EmailService.log_email(
        subject='Team Introduction',
        body='Introducing our team',
        from_address='sales@example.com',
        to_addresses=to_addresses,
        cc_addresses=cc_addresses,
        related_to_type=ActivityRelatedTo.DEAL,
        related_to_id='deal_123',
    )

    assert email.to_addresses == to_addresses
    assert len(email.to_addresses) == 3
    assert email.cc_addresses == cc_addresses
    assert len(email.cc_addresses) == 2


def test_log_email_with_no_cc(crm_manager: AmsdalManager, mock_user):
    """Test logging email without CC addresses."""
    email = EmailService.log_email(
        subject='Direct Message',
        body='This is a direct message',
        from_address='sender@example.com',
        to_addresses=['recipient@example.com'],
        cc_addresses=None,
        related_to_type=ActivityRelatedTo.ENTITY,
        related_to_id='entity_123',
    )

    assert email.cc_addresses is None


def test_log_email_description_generation(crm_manager: AmsdalManager, mock_user):
    """Test that email description is auto-generated from subject."""
    subject = 'Important Update'

    email = EmailService.log_email(
        subject=subject,
        body='Some important update content',
        from_address='sender@example.com',
        to_addresses=['recipient@example.com'],
        cc_addresses=None,
        related_to_type=ActivityRelatedTo.DEAL,
        related_to_id='deal_123',
    )

    assert email.description == f'Email: {subject}'


def test_log_email_integration(crm_manager: AmsdalManager, mock_user):
    """Test logging an email (integration test variant)."""
    subject = 'Integration Test Email'
    body = 'This is an integration test email'
    from_address = 'sender@example.com'
    to_addresses = ['recipient@example.com']
    cc_addresses = None
    related_to_type = ActivityRelatedTo.ENTITY
    related_to_id = 'entity_123'

    email = EmailService.log_email(
        subject=subject,
        body=body,
        from_address=from_address,
        to_addresses=to_addresses,
        cc_addresses=cc_addresses,
        related_to_type=related_to_type,
        related_to_id=related_to_id,
    )

    # Verify EmailActivity was created correctly
    assert email.activity_type == ActivityType.EMAIL
    assert email.subject == subject
    assert email.body == body
    assert email.from_address == from_address
    assert email.is_outbound is True


def test_log_email_inbound_integration(crm_manager: AmsdalManager, mock_user):
    """Test logging of inbound email (integration test variant)."""
    email = EmailService.log_email(
        subject='Inbound Integration Test',
        body='Inbound integration test email',
        from_address='client@example.com',
        to_addresses=['sales@example.com'],
        cc_addresses=None,
        related_to_type=ActivityRelatedTo.DEAL,
        related_to_id='deal_456',
        is_outbound=False,
    )

    assert email.is_outbound is False


# Note: Async integration tests are not included because the integration test environment
# does not have async connection pools and async database infrastructure configured.
# Async functionality is tested in unit tests where transactions are mocked.
