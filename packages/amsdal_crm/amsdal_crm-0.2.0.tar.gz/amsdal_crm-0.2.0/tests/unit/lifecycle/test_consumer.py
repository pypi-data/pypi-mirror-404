"""Unit tests for CRM Lifecycle Consumers."""

from unittest import mock

import pytest
from amsdal_utils.lifecycle.enum import LifecycleEvent

from amsdal_crm.lifecycle.consumer import DealWonNotificationConsumer
from amsdal_crm.lifecycle.consumer import LoadCRMFixturesConsumer


class TestLoadCRMFixturesConsumer:
    """Tests for LoadCRMFixturesConsumer."""

    def test_on_event_executes_without_error(self):
        """Test that on_event can be called without errors."""
        # Create consumer with mock event
        mock_event = mock.Mock(spec=LifecycleEvent)
        consumer = LoadCRMFixturesConsumer(mock_event)

        # Should not raise any exceptions
        try:
            consumer.on_event()
        except Exception as e:
            pytest.fail(f'on_event raised {type(e).__name__}: {e}')

    @pytest.mark.asyncio
    async def test_on_event_async_executes_without_error(self):
        """Test that on_event_async can be called without errors."""
        # Create consumer with mock event
        mock_event = mock.Mock(spec=LifecycleEvent)
        consumer = LoadCRMFixturesConsumer(mock_event)

        # Should not raise any exceptions
        try:
            await consumer.on_event_async()
        except Exception as e:
            pytest.fail(f'on_event_async raised {type(e).__name__}: {e}')

    def test_consumer_can_be_instantiated(self):
        """Test that LoadCRMFixturesConsumer can be instantiated with event."""
        mock_event = mock.Mock(spec=LifecycleEvent)
        consumer = LoadCRMFixturesConsumer(mock_event)
        assert consumer is not None
        assert hasattr(consumer, 'on_event')
        assert hasattr(consumer, 'on_event_async')

    def test_consumer_inherits_from_lifecycle_consumer(self):
        """Test that LoadCRMFixturesConsumer inherits from LifecycleConsumer."""
        from amsdal_utils.lifecycle.consumer import LifecycleConsumer

        assert issubclass(LoadCRMFixturesConsumer, LifecycleConsumer)


class TestDealWonNotificationConsumer:
    """Tests for DealWonNotificationConsumer."""

    def test_on_event_with_deal_and_user_email(self):
        """Test that on_event can be called with deal and user_email."""
        from amsdal_crm.constants import CRMLifecycleEvent

        mock_event = CRMLifecycleEvent.ON_DEAL_WON
        consumer = DealWonNotificationConsumer(mock_event)

        mock_deal = mock.Mock()
        mock_deal.name = 'Test Deal'
        user_email = 'test@example.com'

        # Should not raise any exceptions
        try:
            consumer.on_event(deal=mock_deal, user_email=user_email)
        except Exception as e:
            pytest.fail(f'on_event raised {type(e).__name__}: {e}')

    @pytest.mark.asyncio
    async def test_on_event_async_with_deal_and_user_email(self):
        """Test that on_event_async can be called with deal and user_email."""
        from amsdal_crm.constants import CRMLifecycleEvent

        mock_event = CRMLifecycleEvent.ON_DEAL_WON
        consumer = DealWonNotificationConsumer(mock_event)

        mock_deal = mock.Mock()
        mock_deal.name = 'Test Deal'
        user_email = 'test@example.com'

        # Should not raise any exceptions
        try:
            await consumer.on_event_async(deal=mock_deal, user_email=user_email)
        except Exception as e:
            pytest.fail(f'on_event_async raised {type(e).__name__}: {e}')

    def test_on_event_without_parameters(self):
        """Test that on_event can be called without parameters (defaults to None)."""
        from amsdal_crm.constants import CRMLifecycleEvent

        mock_event = CRMLifecycleEvent.ON_DEAL_WON
        consumer = DealWonNotificationConsumer(mock_event)

        # Should not raise any exceptions even without parameters
        try:
            consumer.on_event(deal=None, user_email=None)
        except Exception as e:
            pytest.fail(f'on_event raised {type(e).__name__}: {e}')

    @pytest.mark.asyncio
    async def test_on_event_async_without_parameters(self):
        """Test that on_event_async can be called without parameters."""
        from amsdal_crm.constants import CRMLifecycleEvent

        mock_event = CRMLifecycleEvent.ON_DEAL_WON
        consumer = DealWonNotificationConsumer(mock_event)

        # Should not raise any exceptions even without parameters
        try:
            await consumer.on_event_async(deal=None, user_email=None)
        except Exception as e:
            pytest.fail(f'on_event_async raised {type(e).__name__}: {e}')

    def test_consumer_can_be_instantiated(self):
        """Test that DealWonNotificationConsumer can be instantiated with event."""
        from amsdal_crm.constants import CRMLifecycleEvent

        mock_event = CRMLifecycleEvent.ON_DEAL_WON
        consumer = DealWonNotificationConsumer(mock_event)
        assert consumer is not None
        assert hasattr(consumer, 'on_event')
        assert hasattr(consumer, 'on_event_async')

    def test_consumer_inherits_from_lifecycle_consumer(self):
        """Test that DealWonNotificationConsumer inherits from LifecycleConsumer."""
        from amsdal_utils.lifecycle.consumer import LifecycleConsumer

        assert issubclass(DealWonNotificationConsumer, LifecycleConsumer)

    def test_on_event_with_full_deal_object(self, unit_deal_data):
        """Test on_event with a realistic deal object."""
        from decimal import Decimal

        from amsdal_crm.constants import CRMLifecycleEvent
        from amsdal_crm.models.deal import Deal

        mock_event = CRMLifecycleEvent.ON_DEAL_WON
        consumer = DealWonNotificationConsumer(mock_event)

        deal = Deal(**unit_deal_data)
        deal.name = 'Won Deal'
        deal.amount = Decimal('100000.00')

        # Should not raise any exceptions
        try:
            consumer.on_event(deal=deal, user_email='winner@example.com')
        except Exception as e:
            pytest.fail(f'on_event raised {type(e).__name__}: {e}')

    @pytest.mark.asyncio
    async def test_on_event_async_with_full_deal_object(self, unit_deal_data):
        """Test on_event_async with a realistic deal object."""
        from decimal import Decimal

        from amsdal_crm.constants import CRMLifecycleEvent
        from amsdal_crm.models.deal import Deal

        mock_event = CRMLifecycleEvent.ON_DEAL_WON
        consumer = DealWonNotificationConsumer(mock_event)

        deal = Deal(**unit_deal_data)
        deal.name = 'Won Deal'
        deal.amount = Decimal('100000.00')

        # Should not raise any exceptions
        try:
            await consumer.on_event_async(deal=deal, user_email='winner@example.com')
        except Exception as e:
            pytest.fail(f'on_event_async raised {type(e).__name__}: {e}')
