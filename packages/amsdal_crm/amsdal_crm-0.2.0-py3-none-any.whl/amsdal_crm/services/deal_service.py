"""DealService for deal management and pipeline operations."""

from amsdal_data.transactions.decorators import async_transaction
from amsdal_data.transactions.decorators import transaction
from amsdal_utils.lifecycle.producer import LifecycleProducer
from amsdal_utils.models.enums import Versions

from amsdal_crm.constants import CRMLifecycleEvent
from amsdal_crm.models.activity import ActivityRelatedTo
from amsdal_crm.models.activity import ActivityType
from amsdal_crm.models.activity import Note
from amsdal_crm.models.deal import Deal
from amsdal_crm.models.stage import Stage


class DealService:
    """Business logic for deal management."""

    @classmethod
    @transaction
    def move_deal_to_stage(cls, deal: Deal, new_stage_id: str, note: str | None, user_email: str) -> Deal:
        """Move a deal to a new stage with optional note.

        Creates an activity log entry for stage change and emits lifecycle events.

        Args:
            deal: The deal to move
            new_stage_id: ID of the new stage
            note: Optional note about the stage change
            user_email: Email of user performing the action

        Returns:
            The updated deal
        """
        # Load new stage
        new_stage = (
            Stage.objects.filter(_object_id=new_stage_id, _address__object_version=Versions.LATEST).get().execute()
        )

        old_stage_name = deal.stage_name

        # Update deal stage (lifecycle hook will handle closed status)
        deal.stage = new_stage
        deal.save()

        # Create activity log
        activity_note = Note(
            activity_type=ActivityType.NOTE,
            subject=f'Deal moved: {old_stage_name} → {new_stage.name}',
            description=note or f'Deal stage changed from {old_stage_name} to {new_stage.name}',
            related_to_type=ActivityRelatedTo.DEAL,
            related_to_id=deal._object_id,
            due_date=None,
            completed_at=None,
            is_completed=False,
        )
        activity_note.save(force_insert=True)

        # Emit lifecycle events
        LifecycleProducer.publish(
            CRMLifecycleEvent.ON_DEAL_STAGE_CHANGE,  # type: ignore[arg-type]
            deal=deal,
            old_stage=old_stage_name,
            new_stage=new_stage.name,
            user_email=user_email,
        )

        if new_stage.status == 'closed_won':
            LifecycleProducer.publish(CRMLifecycleEvent.ON_DEAL_WON, deal=deal, user_email=user_email)  # type: ignore[arg-type]
        elif new_stage.status == 'closed_lost':
            LifecycleProducer.publish(CRMLifecycleEvent.ON_DEAL_LOST, deal=deal, user_email=user_email)  # type: ignore[arg-type]

        return deal

    @classmethod
    @async_transaction
    async def amove_deal_to_stage(cls, deal: Deal, new_stage_id: str, note: str | None, user_email: str) -> Deal:
        """Async version of move_deal_to_stage.

        Args:
            deal: The deal to move
            new_stage_id: ID of the new stage
            note: Optional note about the stage change
            user_email: Email of user performing the action

        Returns:
            The updated deal
        """
        # Load new stage
        new_stage = (
            await Stage.objects.filter(_object_id=new_stage_id, _address__object_version=Versions.LATEST)
            .get()
            .aexecute()
        )

        old_stage_name = deal.stage_name

        # Update deal stage (lifecycle hook will handle closed status)
        deal.stage = new_stage
        await deal.asave()

        # Create activity log
        activity_note = Note(
            activity_type=ActivityType.NOTE,
            subject=f'Deal moved: {old_stage_name} → {new_stage.name}',
            description=note or f'Deal stage changed from {old_stage_name} to {new_stage.name}',
            related_to_type=ActivityRelatedTo.DEAL,
            related_to_id=deal._object_id,
            due_date=None,
            completed_at=None,
            is_completed=False,
        )
        await activity_note.asave(force_insert=True)

        # Emit lifecycle events
        await LifecycleProducer.publish_async(
            CRMLifecycleEvent.ON_DEAL_STAGE_CHANGE,  # type: ignore[arg-type]
            deal=deal,
            old_stage=old_stage_name,
            new_stage=new_stage.name,
            user_email=user_email,
        )

        if new_stage.status == 'closed_won':
            await LifecycleProducer.publish_async(CRMLifecycleEvent.ON_DEAL_WON, deal=deal, user_email=user_email)  # type: ignore[arg-type]
        elif new_stage.status == 'closed_lost':
            await LifecycleProducer.publish_async(CRMLifecycleEvent.ON_DEAL_LOST, deal=deal, user_email=user_email)  # type: ignore[arg-type]

        return deal
