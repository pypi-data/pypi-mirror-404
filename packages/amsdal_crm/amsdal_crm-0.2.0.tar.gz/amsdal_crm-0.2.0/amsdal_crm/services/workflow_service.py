"""WorkflowService for executing workflow automation rules."""

from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import Versions

from amsdal_crm.errors import WorkflowExecutionError
from amsdal_crm.models.activity import ActivityRelatedTo
from amsdal_crm.models.activity import ActivityType
from amsdal_crm.models.activity import Note
from amsdal_crm.models.workflow_rule import WorkflowRule


class WorkflowService:
    """Execute workflow rules for automation."""

    @classmethod
    def execute_rules(cls, entity_type: str, trigger_event: str, entity: Model) -> None:
        """Execute workflow rules for an entity event.

        Called from lifecycle hooks (post_create, post_update, post_delete).

        Args:
            entity_type: Type of entity (Entity, Deal, Activity)
            trigger_event: Event that triggered the rule (create, update, delete)
            entity: The entity instance
        """
        # Load active rules for this entity and trigger
        rules = WorkflowRule.objects.filter(
            entity_type=entity_type,
            trigger_event=trigger_event,
            is_active=True,
            _address__object_version=Versions.LATEST,
        ).execute()

        for rule in rules:
            try:
                if cls._evaluate_condition(rule, entity):
                    cls._execute_action(rule, entity)
            except Exception as exc:
                # Log error but don't fail the entire operation
                error_msg = f'Failed to execute workflow rule {rule.name}: {exc}'
                raise WorkflowExecutionError(error_msg) from exc

    @classmethod
    async def aexecute_rules(cls, entity_type: str, trigger_event: str, entity: Model) -> None:
        """Execute workflow rules for an entity event.

        Called from lifecycle hooks (post_create, post_update, post_delete).

        Args:
            entity_type: Type of entity (Entity, Deal, Activity)
            trigger_event: Event that triggered the rule (create, update, delete)
            entity: The entity instance
        """
        # Load active rules for this entity and trigger
        rules = await WorkflowRule.objects.filter(
            entity_type=entity_type,
            trigger_event=trigger_event,
            is_active=True,
            _address__object_version=Versions.LATEST,
        ).aexecute()

        for rule in rules:
            try:
                if cls._evaluate_condition(rule, entity):
                    await cls._aexecute_action(rule, entity)
            except Exception as exc:
                # Log error but don't fail the entire operation
                error_msg = f'Failed to execute workflow rule {rule.name}: {exc}'
                raise WorkflowExecutionError(error_msg) from exc

    @classmethod
    def _evaluate_condition(cls, rule: WorkflowRule, entity: Model) -> bool:
        """Evaluate if rule condition matches.

        Args:
            rule: The workflow rule
            entity: The entity to evaluate

        Returns:
            True if condition matches, False otherwise
        """
        if not rule.condition_field:
            return True  # No condition = always match

        entity_value = getattr(entity, rule.condition_field, None)

        if rule.condition_operator == 'equals':
            return entity_value == rule.condition_value
        elif rule.condition_operator == 'not_equals':
            return entity_value != rule.condition_value
        elif rule.condition_operator == 'contains':
            if rule.condition_value is None or entity_value is None:
                return False
            return str(rule.condition_value) in str(entity_value)
        elif rule.condition_operator == 'greater_than':
            if entity_value is None or rule.condition_value is None:
                return False
            return entity_value > rule.condition_value
        elif rule.condition_operator == 'less_than':
            if entity_value is None or rule.condition_value is None:
                return False
            return entity_value < rule.condition_value

        return False

    @classmethod
    def _execute_action(cls, rule: WorkflowRule, entity: Model) -> None:
        """Execute rule action.

        Args:
            rule: The workflow rule
            entity: The entity to act upon
        """
        if rule.action_type == 'update_field':
            # Update field on entity
            field_name = rule.action_config.get('field_name')
            new_value = rule.action_config.get('value')
            if field_name:
                setattr(entity, str(field_name), new_value)
                entity.save()

        elif rule.action_type == 'create_activity':
            # Create a Note activity
            note = Note(
                activity_type=ActivityType.NOTE,
                subject=rule.action_config.get('subject', f'Workflow: {rule.name}'),
                description=rule.action_config.get('description', ''),
                related_to_type=ActivityRelatedTo[rule.entity_type.upper()],
                related_to_id=entity._object_id,
                assigned_to=entity.assigned_to if hasattr(entity, 'assigned_to') else None,
                due_date=None,
                completed_at=None,
                is_completed=False,
            )
            note.save(force_insert=True)

        elif rule.action_type == 'send_notification':
            # TODO: Implement notification system
            # Placeholder for future notification integration
            pass

    @classmethod
    async def _aexecute_action(cls, rule: WorkflowRule, entity: Model) -> None:
        """Execute rule action.

        Args:
            rule: The workflow rule
            entity: The entity to act upon
        """
        if rule.action_type == 'update_field':
            # Update field on entity
            field_name = rule.action_config.get('field_name')
            new_value = rule.action_config.get('value')
            if field_name:
                setattr(entity, str(field_name), new_value)
                await entity.asave()

        elif rule.action_type == 'create_activity':
            # Create a Note activity
            note = Note(
                activity_type=ActivityType.NOTE,
                subject=rule.action_config.get('subject', f'Workflow: {rule.name}'),
                description=rule.action_config.get('description', ''),
                related_to_type=ActivityRelatedTo[rule.entity_type.upper()],
                related_to_id=entity._object_id,
                assigned_to=entity.assigned_to if hasattr(entity, 'assigned_to') else None,
                due_date=None,
                completed_at=None,
                is_completed=False,
            )
            await note.asave(force_insert=True)

        elif rule.action_type == 'send_notification':
            # TODO: Implement notification system
            # Placeholder for future notification integration
            pass
