"""CRM permission fixtures."""

# CRM permissions for each entity type
CRM_PERMISSIONS = [
    # Entity permissions
    {'model': 'Entity', 'action': 'read'},
    {'model': 'Entity', 'action': 'create'},
    {'model': 'Entity', 'action': 'update'},
    {'model': 'Entity', 'action': 'delete'},
    # Deal permissions
    {'model': 'Deal', 'action': 'read'},
    {'model': 'Deal', 'action': 'create'},
    {'model': 'Deal', 'action': 'update'},
    {'model': 'Deal', 'action': 'delete'},
    # Activity permissions
    {'model': 'Activity', 'action': 'read'},
    {'model': 'Activity', 'action': 'create'},
    {'model': 'Activity', 'action': 'update'},
    {'model': 'Activity', 'action': 'delete'},
    # Pipeline permissions (read-only for non-admins)
    {'model': 'Pipeline', 'action': 'read'},
    # Stage permissions (read-only for non-admins)
    {'model': 'Stage', 'action': 'read'},
]
