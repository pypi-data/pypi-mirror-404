"""Unit tests for CRM Constants."""

from enum import Enum

import pytest

from amsdal_crm.constants import CRMLifecycleEvent


class TestCRMLifecycleEvent:
    """Tests for CRMLifecycleEvent enum."""

    def test_is_enum(self):
        """Test that CRMLifecycleEvent is an Enum."""
        assert issubclass(CRMLifecycleEvent, Enum)

    def test_is_string_enum(self):
        """Test that CRMLifecycleEvent values are strings."""
        for event in CRMLifecycleEvent:
            assert isinstance(event.value, str)

    def test_all_event_values_exist(self):
        """Test that all expected lifecycle events exist."""
        expected_events = [
            'ON_DEAL_STAGE_CHANGE',
            'ON_DEAL_WON',
            'ON_DEAL_LOST',
            'ON_CONTACT_MERGE',
            'ON_ACCOUNT_MERGE',
        ]

        for event_name in expected_events:
            assert hasattr(CRMLifecycleEvent, event_name), f'{event_name} should exist in CRMLifecycleEvent'

    def test_on_deal_stage_change_value(self):
        """Test ON_DEAL_STAGE_CHANGE has correct value."""
        assert CRMLifecycleEvent.ON_DEAL_STAGE_CHANGE.value == 'on_deal_stage_change'

    def test_on_deal_won_value(self):
        """Test ON_DEAL_WON has correct value."""
        assert CRMLifecycleEvent.ON_DEAL_WON.value == 'on_deal_won'

    def test_on_deal_lost_value(self):
        """Test ON_DEAL_LOST has correct value."""
        assert CRMLifecycleEvent.ON_DEAL_LOST.value == 'on_deal_lost'

    def test_on_contact_merge_value(self):
        """Test ON_CONTACT_MERGE has correct value."""
        assert CRMLifecycleEvent.ON_CONTACT_MERGE.value == 'on_contact_merge'

    def test_on_account_merge_value(self):
        """Test ON_ACCOUNT_MERGE has correct value."""
        assert CRMLifecycleEvent.ON_ACCOUNT_MERGE.value == 'on_account_merge'

    def test_enum_equality_comparison(self):
        """Test that enum members can be compared for equality."""
        event1 = CRMLifecycleEvent.ON_DEAL_WON
        event2 = CRMLifecycleEvent.ON_DEAL_WON
        event3 = CRMLifecycleEvent.ON_DEAL_LOST

        assert event1 == event2
        assert event1 != event3

    def test_enum_can_be_used_as_dict_key(self):
        """Test that enum members can be used as dictionary keys."""
        event_handlers = {
            CRMLifecycleEvent.ON_DEAL_WON: 'handle_deal_won',
            CRMLifecycleEvent.ON_DEAL_LOST: 'handle_deal_lost',
        }

        assert event_handlers[CRMLifecycleEvent.ON_DEAL_WON] == 'handle_deal_won'
        assert event_handlers[CRMLifecycleEvent.ON_DEAL_LOST] == 'handle_deal_lost'

    def test_enum_iteration(self):
        """Test that all enum members can be iterated."""
        events = list(CRMLifecycleEvent)

        # Should have exactly 5 events
        assert len(events) == 5

        # All should be CRMLifecycleEvent instances
        for event in events:
            assert isinstance(event, CRMLifecycleEvent)

    def test_enum_membership(self):
        """Test checking if value is in enum."""
        assert CRMLifecycleEvent.ON_DEAL_WON in CRMLifecycleEvent
        assert CRMLifecycleEvent.ON_DEAL_STAGE_CHANGE in CRMLifecycleEvent

    def test_enum_value_lookup(self):
        """Test looking up enum by value."""
        event = CRMLifecycleEvent('on_deal_won')
        assert event == CRMLifecycleEvent.ON_DEAL_WON

    def test_enum_invalid_value_raises_error(self):
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            CRMLifecycleEvent('invalid_event')

    def test_enum_string_representation(self):
        """Test string representation of enum members."""
        event = CRMLifecycleEvent.ON_DEAL_WON
        str_repr = str(event)

        # String representation should contain the event name
        assert 'ON_DEAL_WON' in str_repr or 'on_deal_won' in str_repr

    def test_enum_value_is_string_type(self):
        """Test that enum values are of type str."""
        for event in CRMLifecycleEvent:
            assert type(event.value) is str

    def test_enum_names(self):
        """Test that enum names are correct."""
        expected_names = {
            'ON_DEAL_STAGE_CHANGE',
            'ON_DEAL_WON',
            'ON_DEAL_LOST',
            'ON_CONTACT_MERGE',
            'ON_ACCOUNT_MERGE',
        }

        actual_names = {event.name for event in CRMLifecycleEvent}
        assert actual_names == expected_names

    def test_enum_values(self):
        """Test that enum values are correct."""
        expected_values = {
            'on_deal_stage_change',
            'on_deal_won',
            'on_deal_lost',
            'on_contact_merge',
            'on_account_merge',
        }

        actual_values = {event.value for event in CRMLifecycleEvent}
        assert actual_values == expected_values

    def test_enum_can_be_compared_to_string(self):
        """Test that enum values can be compared to strings."""
        event = CRMLifecycleEvent.ON_DEAL_WON

        # Enum value (not the enum itself) should equal the string
        assert event.value == 'on_deal_won'
        assert event == CRMLifecycleEvent('on_deal_won')

    def test_enum_count(self):
        """Test that there are exactly 5 lifecycle events."""
        assert len(CRMLifecycleEvent) == 5

    def test_enum_hashable(self):
        """Test that enum members are hashable and can be used in sets."""
        event_set = {
            CRMLifecycleEvent.ON_DEAL_WON,
            CRMLifecycleEvent.ON_DEAL_LOST,
            CRMLifecycleEvent.ON_DEAL_WON,  # Duplicate
        }

        # Set should contain only 2 unique items
        assert len(event_set) == 2
        assert CRMLifecycleEvent.ON_DEAL_WON in event_set
        assert CRMLifecycleEvent.ON_DEAL_LOST in event_set

    def test_enum_access_by_attribute(self):
        """Test accessing enum members by attribute name."""
        assert hasattr(CRMLifecycleEvent, 'ON_DEAL_WON')
        assert CRMLifecycleEvent.ON_DEAL_WON is not None

    def test_enum_access_by_item(self):
        """Test accessing enum members by item notation."""
        event = CRMLifecycleEvent['ON_DEAL_WON']
        assert event == CRMLifecycleEvent.ON_DEAL_WON
