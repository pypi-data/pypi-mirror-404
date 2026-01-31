"""Unit tests for CRM App Configuration."""

from unittest import mock

import pytest

from amsdal_crm.app import CRMAppConfig
from amsdal_crm.constants import CRMLifecycleEvent


class TestCRMAppConfig:
    """Tests for CRMAppConfig."""

    def test_app_config_instantiation(self):
        """Test that CRMAppConfig can be instantiated."""
        config = CRMAppConfig()
        assert config is not None
        assert hasattr(config, 'on_ready')

    @mock.patch('amsdal_crm.app.LifecycleProducer')
    def test_on_ready_registers_load_fixtures_consumer(self, mock_producer):
        """Test that on_ready registers LoadCRMFixturesConsumer."""
        from amsdal_utils.lifecycle.enum import LifecycleEvent

        from amsdal_crm.lifecycle.consumer import LoadCRMFixturesConsumer

        config = CRMAppConfig()
        config.on_ready()

        # Verify LoadCRMFixturesConsumer was registered with ON_SERVER_STARTUP event
        calls = mock_producer.add_listener.call_args_list
        assert any(
            call[0][0] == LifecycleEvent.ON_SERVER_STARTUP and call[0][1] == LoadCRMFixturesConsumer for call in calls
        ), 'LoadCRMFixturesConsumer should be registered for ON_SERVER_STARTUP'

    @mock.patch('amsdal_crm.app.LifecycleProducer')
    def test_on_ready_registers_deal_won_notification_consumer(self, mock_producer):
        """Test that on_ready registers DealWonNotificationConsumer."""
        from amsdal_crm.lifecycle.consumer import DealWonNotificationConsumer

        config = CRMAppConfig()
        config.on_ready()

        # Verify DealWonNotificationConsumer was registered with ON_DEAL_WON event
        calls = mock_producer.add_listener.call_args_list
        assert any(
            call[0][0] == CRMLifecycleEvent.ON_DEAL_WON and call[0][1] == DealWonNotificationConsumer for call in calls
        ), 'DealWonNotificationConsumer should be registered for ON_DEAL_WON'

    @mock.patch('amsdal_crm.app.LifecycleProducer')
    def test_on_ready_registers_both_consumers(self, mock_producer):
        """Test that on_ready registers both lifecycle consumers."""
        config = CRMAppConfig()
        config.on_ready()

        # Should have at least 2 add_listener calls (one for each consumer)
        assert mock_producer.add_listener.call_count >= 2

    @mock.patch('amsdal_crm.app.LifecycleProducer')
    def test_on_ready_uses_correct_lifecycle_events(self, mock_producer):
        """Test that on_ready uses correct lifecycle event types."""
        from amsdal_utils.lifecycle.enum import LifecycleEvent

        config = CRMAppConfig()
        config.on_ready()

        # Get all event types passed to add_listener
        event_types = [call[0][0] for call in mock_producer.add_listener.call_args_list]

        # Should include ON_SERVER_STARTUP from standard lifecycle events
        assert LifecycleEvent.ON_SERVER_STARTUP in event_types

        # Should include ON_DEAL_WON from CRM custom lifecycle events
        assert CRMLifecycleEvent.ON_DEAL_WON in event_types

    @mock.patch('amsdal_crm.app.LifecycleProducer')
    def test_on_ready_can_be_called_multiple_times(self, mock_producer):
        """Test that on_ready can be called multiple times without errors."""
        config = CRMAppConfig()

        # Should not raise exceptions when called multiple times
        try:
            config.on_ready()
            config.on_ready()
        except Exception as e:
            pytest.fail(f'on_ready raised {type(e).__name__}: {e}')

        # Should have registered listeners multiple times
        assert mock_producer.add_listener.call_count >= 4  # 2 calls * 2 invocations

    def test_app_config_inherits_from_base(self):
        """Test that CRMAppConfig inherits from AppConfig."""
        from amsdal.contrib.app_config import AppConfig

        config = CRMAppConfig()
        assert isinstance(config, AppConfig)

    @mock.patch('amsdal_crm.app.LifecycleProducer')
    def test_on_ready_executes_without_errors(self, mock_producer):
        """Test that on_ready executes without raising exceptions."""
        config = CRMAppConfig()

        try:
            config.on_ready()
        except Exception as e:
            pytest.fail(f'on_ready raised {type(e).__name__}: {e}')

    @mock.patch('amsdal_crm.app.LifecycleProducer')
    def test_on_ready_imports_consumers_correctly(self, mock_producer):
        """Test that on_ready imports consumer classes without errors."""
        config = CRMAppConfig()

        # Should not raise ImportError
        try:
            config.on_ready()
        except ImportError as e:
            pytest.fail(f'Failed to import consumer: {e}')

        # Verify both consumers were imported and used
        assert mock_producer.add_listener.called
