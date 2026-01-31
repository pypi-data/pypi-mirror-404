"""CRM App Configuration."""

from amsdal.contrib.app_config import AppConfig
from amsdal.contrib.frontend_configs.constants import ON_RESPONSE_EVENT
from amsdal_utils.lifecycle.enum import LifecycleEvent
from amsdal_utils.lifecycle.producer import LifecycleProducer

from amsdal_crm.constants import CRMLifecycleEvent


class CRMAppConfig(AppConfig):
    """Configuration for the CRM application."""

    def on_ready(self) -> None:
        """Set up CRM lifecycle listeners and initialize module."""
        from amsdal_crm.lifecycle.consumer import CustomAttributesFrontendConfigConsumer
        from amsdal_crm.lifecycle.consumer import DealWonNotificationConsumer
        from amsdal_crm.lifecycle.consumer import LoadCRMFixturesConsumer

        # Load fixtures on startup
        LifecycleProducer.add_listener(LifecycleEvent.ON_SERVER_STARTUP, LoadCRMFixturesConsumer)

        # Custom CRM events
        LifecycleProducer.add_listener(CRMLifecycleEvent.ON_DEAL_WON, DealWonNotificationConsumer)  # type: ignore[arg-type]

        # Propagate custom attributes to frontend configs
        LifecycleProducer.add_listener(ON_RESPONSE_EVENT, CustomAttributesFrontendConfigConsumer)  # type: ignore[arg-type]

        # Additional event listeners can be added here
        # LifecycleProducer.add_listener(CRMLifecycleEvent.ON_DEAL_LOST, DealLostNotificationConsumer)
