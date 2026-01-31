"""Unit tests for CRM Custom Exceptions."""

import pytest

from amsdal_crm.errors import CRMError
from amsdal_crm.errors import CustomFieldValidationError
from amsdal_crm.errors import InvalidStageTransitionError
from amsdal_crm.errors import PermissionDeniedError
from amsdal_crm.errors import WorkflowExecutionError


class TestCRMError:
    """Tests for CRMError base exception."""

    def test_crm_error_is_exception(self):
        """Test that CRMError is a subclass of Exception."""
        assert issubclass(CRMError, Exception)

    def test_crm_error_can_be_raised(self):
        """Test that CRMError can be raised."""
        with pytest.raises(CRMError):
            raise CRMError()

    def test_crm_error_with_message(self):
        """Test that CRMError can have a custom message."""
        message = 'This is a CRM error'
        error = CRMError(message)
        assert str(error) == message

    def test_crm_error_can_be_caught(self):
        """Test that CRMError can be caught."""
        msg = 'Test error'
        try:
            raise CRMError(msg)
        except CRMError as e:
            assert str(e) == msg
        except Exception:
            pytest.fail('CRMError should be caught as CRMError')

    def test_crm_error_can_be_caught_as_exception(self):
        """Test that CRMError can be caught as generic Exception."""
        msg = 'Test error'
        try:
            raise CRMError(msg)
        except Exception as e:
            assert isinstance(e, CRMError)
            assert str(e) == msg


class TestCustomFieldValidationError:
    """Tests for CustomFieldValidationError."""

    def test_inherits_from_crm_error(self):
        """Test that CustomFieldValidationError inherits from CRMError."""
        assert issubclass(CustomFieldValidationError, CRMError)

    def test_inherits_from_exception(self):
        """Test that CustomFieldValidationError inherits from Exception."""
        assert issubclass(CustomFieldValidationError, Exception)

    def test_can_be_raised(self):
        """Test that CustomFieldValidationError can be raised."""
        with pytest.raises(CustomFieldValidationError):
            raise CustomFieldValidationError()

    def test_with_message(self):
        """Test that CustomFieldValidationError can have a message."""
        message = 'Invalid custom field value'
        error = CustomFieldValidationError(message)
        assert str(error) == message

    def test_can_be_caught_as_crm_error(self):
        """Test that CustomFieldValidationError can be caught as CRMError."""
        msg = 'Validation failed'
        try:
            raise CustomFieldValidationError(msg)
        except CRMError as e:
            assert isinstance(e, CustomFieldValidationError)
            assert str(e) == msg

    def test_can_be_caught_specifically(self):
        """Test that CustomFieldValidationError can be caught specifically."""
        msg = 'Field required'
        try:
            raise CustomFieldValidationError(msg)
        except CustomFieldValidationError as e:
            assert str(e) == msg
        except CRMError:
            pytest.fail('Should be caught as CustomFieldValidationError first')


class TestWorkflowExecutionError:
    """Tests for WorkflowExecutionError."""

    def test_inherits_from_crm_error(self):
        """Test that WorkflowExecutionError inherits from CRMError."""
        assert issubclass(WorkflowExecutionError, CRMError)

    def test_inherits_from_exception(self):
        """Test that WorkflowExecutionError inherits from Exception."""
        assert issubclass(WorkflowExecutionError, Exception)

    def test_can_be_raised(self):
        """Test that WorkflowExecutionError can be raised."""
        with pytest.raises(WorkflowExecutionError):
            raise WorkflowExecutionError()

    def test_with_message(self):
        """Test that WorkflowExecutionError can have a message."""
        message = 'Workflow execution failed'
        error = WorkflowExecutionError(message)
        assert str(error) == message

    def test_can_be_caught_as_crm_error(self):
        """Test that WorkflowExecutionError can be caught as CRMError."""
        msg = 'Action failed'
        try:
            raise WorkflowExecutionError(msg)
        except CRMError as e:
            assert isinstance(e, WorkflowExecutionError)
            assert str(e) == msg

    def test_can_be_caught_specifically(self):
        """Test that WorkflowExecutionError can be caught specifically."""
        msg = 'Rule execution error'
        try:
            raise WorkflowExecutionError(msg)
        except WorkflowExecutionError as e:
            assert str(e) == msg
        except CRMError:
            pytest.fail('Should be caught as WorkflowExecutionError first')


class TestInvalidStageTransitionError:
    """Tests for InvalidStageTransitionError."""

    def test_inherits_from_crm_error(self):
        """Test that InvalidStageTransitionError inherits from CRMError."""
        assert issubclass(InvalidStageTransitionError, CRMError)

    def test_inherits_from_exception(self):
        """Test that InvalidStageTransitionError inherits from Exception."""
        assert issubclass(InvalidStageTransitionError, Exception)

    def test_can_be_raised(self):
        """Test that InvalidStageTransitionError can be raised."""
        with pytest.raises(InvalidStageTransitionError):
            raise InvalidStageTransitionError()

    def test_with_message(self):
        """Test that InvalidStageTransitionError can have a message."""
        message = 'Cannot transition from stage A to stage B'
        error = InvalidStageTransitionError(message)
        assert str(error) == message

    def test_can_be_caught_as_crm_error(self):
        """Test that InvalidStageTransitionError can be caught as CRMError."""
        msg = 'Invalid transition'
        try:
            raise InvalidStageTransitionError(msg)
        except CRMError as e:
            assert isinstance(e, InvalidStageTransitionError)
            assert str(e) == msg

    def test_can_be_caught_specifically(self):
        """Test that InvalidStageTransitionError can be caught specifically."""
        msg = 'Transition not allowed'
        try:
            raise InvalidStageTransitionError(msg)
        except InvalidStageTransitionError as e:
            assert str(e) == msg
        except CRMError:
            pytest.fail('Should be caught as InvalidStageTransitionError first')


class TestPermissionDeniedError:
    """Tests for PermissionDeniedError."""

    def test_inherits_from_crm_error(self):
        """Test that PermissionDeniedError inherits from CRMError."""
        assert issubclass(PermissionDeniedError, CRMError)

    def test_inherits_from_exception(self):
        """Test that PermissionDeniedError inherits from Exception."""
        assert issubclass(PermissionDeniedError, Exception)

    def test_can_be_raised(self):
        """Test that PermissionDeniedError can be raised."""
        with pytest.raises(PermissionDeniedError):
            raise PermissionDeniedError()

    def test_with_message(self):
        """Test that PermissionDeniedError can have a message."""
        message = 'User does not have permission'
        error = PermissionDeniedError(message)
        assert str(error) == message

    def test_can_be_caught_as_crm_error(self):
        """Test that PermissionDeniedError can be caught as CRMError."""
        msg = 'Access denied'
        try:
            raise PermissionDeniedError(msg)
        except CRMError as e:
            assert isinstance(e, PermissionDeniedError)
            assert str(e) == msg

    def test_can_be_caught_specifically(self):
        """Test that PermissionDeniedError can be caught specifically."""
        msg = 'No write permission'
        try:
            raise PermissionDeniedError(msg)
        except PermissionDeniedError as e:
            assert str(e) == msg
        except CRMError:
            pytest.fail('Should be caught as PermissionDeniedError first')


class TestExceptionHierarchy:
    """Tests for exception hierarchy and interaction."""

    def test_all_exceptions_inherit_from_crm_error(self):
        """Test that all custom exceptions inherit from CRMError."""
        exceptions = [
            CustomFieldValidationError,
            WorkflowExecutionError,
            InvalidStageTransitionError,
            PermissionDeniedError,
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, CRMError), f'{exc_class.__name__} should inherit from CRMError'

    def test_catching_crm_error_catches_all_custom_exceptions(self):
        """Test that catching CRMError catches all custom exceptions."""
        exceptions = [
            CustomFieldValidationError('test1'),
            WorkflowExecutionError('test2'),
            InvalidStageTransitionError('test3'),
            PermissionDeniedError('test4'),
        ]

        for exception in exceptions:
            try:
                raise exception
            except CRMError as e:
                assert isinstance(e, type(exception))
            except Exception:
                pytest.fail(f'{type(exception).__name__} should be caught as CRMError')

    def test_specific_exception_caught_before_crm_error(self):
        """Test that specific exceptions are caught before generic CRMError."""
        caught_type = None
        msg = 'Specific error'

        try:
            raise CustomFieldValidationError(msg)
        except CustomFieldValidationError:
            caught_type = 'specific'
        except CRMError:
            caught_type = 'generic'

        assert caught_type == 'specific', 'Specific exception should be caught first'

    def test_exception_with_multiple_arguments(self):
        """Test exceptions with multiple arguments."""
        error = CustomFieldValidationError('Field error', 'field_name', 'invalid_value')
        assert 'Field error' in str(error)

    def test_exception_repr(self):
        """Test exception representation."""
        error = CRMError('Test error')
        repr_str = repr(error)
        assert 'CRMError' in repr_str
        assert 'Test error' in repr_str
