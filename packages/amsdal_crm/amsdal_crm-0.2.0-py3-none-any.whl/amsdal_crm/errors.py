"""CRM Custom Exceptions."""


class CRMError(ValueError):
    """Base exception for CRM errors."""


class CustomFieldValidationError(CRMError):
    """Raised when custom field validation fails."""


class WorkflowExecutionError(CRMError):
    """Raised when workflow rule execution fails."""


class InvalidStageTransitionError(CRMError):
    """Raised when an invalid stage transition is attempted."""


class PermissionDeniedError(CRMError):
    """Raised when user doesn't have permission for an operation."""
