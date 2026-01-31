"""ActivityService for managing activities and timelines."""

from amsdal_utils.models.enums import Versions

from amsdal_crm.models.activity import Activity
from amsdal_crm.models.activity import ActivityRelatedTo


class ActivityService:
    """Service for querying and managing activities."""

    @classmethod
    def get_timeline(cls, related_to_type: ActivityRelatedTo, related_to_id: str, limit: int = 100) -> list[Activity]:
        """Get chronological activity timeline for a record.

        Args:
            related_to_type: Type of record (Contact, Account, Deal)
            related_to_id: ID of the record
            limit: Maximum number of activities to return

        Returns:
            List of activities sorted by created_at desc (newest first)
        """
        activities = (
            Activity.objects.filter(
                related_to_type=related_to_type, related_to_id=related_to_id, _address__object_version=Versions.LATEST
            )
            .order_by('-created_at')
            .execute()
        )

        return activities[:limit]

    @classmethod
    async def aget_timeline(
        cls, related_to_type: ActivityRelatedTo, related_to_id: str, limit: int = 100
    ) -> list[Activity]:
        """Async version of get_timeline.

        Args:
            related_to_type: Type of record (Contact, Account, Deal)
            related_to_id: ID of the record
            limit: Maximum number of activities to return

        Returns:
            List of activities sorted by created_at desc (newest first)
        """
        activities = await (
            Activity.objects.filter(
                related_to_type=related_to_type, related_to_id=related_to_id, _address__object_version=Versions.LATEST
            )
            .order_by('-created_at')
            .aexecute()
        )

        return activities[:limit]
