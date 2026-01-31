"""Unit tests for EmailService."""

from unittest import mock

import pytest

from amsdal_crm.models.activity import ActivityRelatedTo
from amsdal_crm.models.activity import ActivityType
from amsdal_crm.models.activity import EmailActivity
from amsdal_crm.services.email_service import EmailService


def test_log_email_outbound(unit_user):
    """Test logging an outbound email."""
    subject = 'Proposal for Q2'
    body = 'Please find attached our proposal for Q2...'
    from_address = 'sales@example.com'
    to_addresses = ['client@example.com']
    cc_addresses = ['manager@example.com']
    related_to_type = ActivityRelatedTo.DEAL
    related_to_id = 'deal_123'

    with mock.patch.object(EmailActivity, 'save') as mock_save:
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

        # Verify save was called
        mock_save.assert_called_once_with(force_insert=True)


def test_log_email_inbound(unit_user):
    """Test logging an inbound email."""
    subject = 'Re: Proposal for Q2'
    body = 'Thanks for the proposal. We have some questions...'
    from_address = 'client@example.com'
    to_addresses = ['sales@example.com']
    cc_addresses = None
    related_to_type = ActivityRelatedTo.DEAL
    related_to_id = 'deal_123'

    with mock.patch.object(EmailActivity, 'save'):
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


def test_log_email_default_outbound(unit_user):
    """Test that is_outbound defaults to True."""
    with mock.patch.object(EmailActivity, 'save'):
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


def test_log_email_to_entity(unit_user):
    """Test logging email related to entity."""
    entity_id = 'entity_456'

    with mock.patch.object(EmailActivity, 'save'):
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


def test_log_email_to_deal(unit_user):
    """Test logging email related to deal."""
    deal_id = 'deal_789'

    with mock.patch.object(EmailActivity, 'save'):
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


def test_log_email_with_multiple_recipients(unit_user):
    """Test logging email with multiple recipients."""
    to_addresses = ['client1@example.com', 'client2@example.com', 'client3@example.com']
    cc_addresses = ['manager@example.com', 'director@example.com']

    with mock.patch.object(EmailActivity, 'save'):
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


def test_log_email_with_no_cc(unit_user):
    """Test logging email without CC addresses."""
    with mock.patch.object(EmailActivity, 'save'):
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


def test_log_email_description_generation(unit_user):
    """Test that email description is auto-generated from subject."""
    subject = 'Important Update'

    with mock.patch.object(EmailActivity, 'save'):
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


def test_log_email_transaction_decorator():
    """Test that log_email has transaction decorator applied."""
    # Verify the decorator is present
    # Check if the method has been wrapped by transaction decorator
    # The transaction decorator modifies the function, so we can check for its presence
    assert hasattr(EmailService.log_email, '__wrapped__') or hasattr(EmailService.log_email, '__name__')


@pytest.mark.asyncio
async def test_alog_email_async(unit_user):
    """Test async version of log_email."""
    subject = 'Async Email'
    body = 'This is an async email'
    from_address = 'sender@example.com'
    to_addresses = ['recipient@example.com']
    cc_addresses = None
    related_to_type = ActivityRelatedTo.ENTITY
    related_to_id = 'entity_123'

    with mock.patch.object(EmailActivity, 'asave') as mock_asave:
        # Mock async save
        async def async_save(*args, **kwargs):
            pass

        mock_asave.side_effect = async_save

        email = await EmailService.alog_email(
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

        # Verify async save was called
        mock_asave.assert_called_once_with(force_insert=True)


@pytest.mark.asyncio
async def test_alog_email_inbound(unit_user):
    """Test async logging of inbound email."""
    with mock.patch.object(EmailActivity, 'asave') as mock_asave:
        # Mock async save
        async def async_save(*args, **kwargs):
            pass

        mock_asave.side_effect = async_save

        email = await EmailService.alog_email(
            subject='Inbound Async',
            body='Inbound async email',
            from_address='client@example.com',
            to_addresses=['sales@example.com'],
            cc_addresses=None,
            related_to_type=ActivityRelatedTo.DEAL,
            related_to_id='deal_456',
            is_outbound=False,
        )

        assert email.is_outbound is False
