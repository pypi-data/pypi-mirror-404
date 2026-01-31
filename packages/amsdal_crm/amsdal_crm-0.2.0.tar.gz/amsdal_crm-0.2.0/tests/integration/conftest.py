"""Fixtures for CRM integration tests."""

from collections.abc import Iterator
from contextlib import ExitStack
from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest
from amsdal.manager import AmsdalManager
from amsdal.utils.tests.enums import DbExecutionType
from amsdal.utils.tests.enums import LakehouseOption
from amsdal.utils.tests.enums import StateOption
from amsdal.utils.tests.helpers import init_manager_and_migrate
from amsdal_data.services.table_schema_manager import TableSchemasManager

# Import all CRM models at module level so they're discovered by init_manager_and_migrate
from amsdal_crm.models.activity import Activity  # noqa: F401
from amsdal_crm.models.activity import ActivityRelatedTo  # noqa: F401
from amsdal_crm.models.activity import Call  # noqa: F401
from amsdal_crm.models.activity import EmailActivity
from amsdal_crm.models.activity import Event  # noqa: F401
from amsdal_crm.models.activity import Note
from amsdal_crm.models.activity import Task  # noqa: F401
from amsdal_crm.models.attachment import Attachment  # noqa: F401
from amsdal_crm.models.custom_field_definition import CustomFieldDefinition  # noqa: F401
from amsdal_crm.models.deal import Deal
from amsdal_crm.models.entity import Entity  # noqa: F401
from amsdal_crm.models.entity import EntityAddress  # noqa: F401
from amsdal_crm.models.entity import EntityContactPoint  # noqa: F401
from amsdal_crm.models.entity import EntityIdentifier  # noqa: F401
from amsdal_crm.models.entity import EntityRelationship  # noqa: F401
from amsdal_crm.models.pipeline import Pipeline
from amsdal_crm.models.stage import Stage
from amsdal_crm.models.workflow_rule import WorkflowRule  # noqa: F401

TESTS_DIR = Path(__file__).parent.parent
PROJECT_DIR = TESTS_DIR.parent
CRM_MODELS_PATH = PROJECT_DIR / 'amsdal_crm' / 'models'
EXPIRATION_VALID_TOKEN = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODQ2MzA3OTF9.FhNV6yegtll-pUgr2ClrB-NwlrVJeU0R8c8RYQu7oBGHf5T2lO_gleghOseko6y6jOZuPLgLunG6K04BNfAbEDYWyG59YGm5ShoQ2I-GVBUShoKrqpwFwOvC5wn8d1c_i7INC_oU6gKvgsbkSZ0E4cx4zGQyafYDtNbQfj6S9BuocrjyFzSrk997wR6UlfwmpM5-G80Q_dv9Ka2gNKICM4LLnePQYwdbmBG1dlmhH5tZPibU9D7R4IxqTJOAXCiZYajt7H28nWZ_UbnC7mjVQcbHwpt9fqwkt01JGbkl7uNskGtXAR6RCUxRyzp3PIytTrpN8VnAC_7Ngql7k3KyGFMtrrCVXRYpztpa7VUddR0Iz-rm4AUrsqgRJbUz9SEDPMzs29I14sTMhkOu0ae8KPuiik1q01Ma_P02e3fe_496CAF5gviIc1umIj5KmBmxM5bG5e4EbkIC6AxXkEg8DZM3l_Pu7MhI1jSLKDAB-cWRd2nmdjmIzYfcKMj35XzHNLrj6jJy0PBdAhF9CA_ORsu6H5sm1wc7cGHIjD3vjv-VtREaWa4sGpGWKqIwUdF68Zrw5cUwuw_6PDOzlOHfLD2kYywkT0LsIc7U8jKtR9FjeRGk4Uve9JAYudO4liUWiDui6TbgiY5AbE45e00XvCpwhbEjtsOKEuiwEenPMCE'  # noqa: E501


@pytest.fixture()
def crm_manager(database_backend) -> Iterator[AmsdalManager]:
    """Initialize AmsdalManager with CRM models for integration tests."""
    lakehouse_option = LakehouseOption.postgres if 'postgres' in database_backend.value else LakehouseOption.sqlite
    state_option = StateOption.postgres if 'postgres' == database_backend.value else StateOption.sqlite

    with ExitStack() as stack:
        # Mock auth settings (required for CRM operations)
        auth_settings_mocked = stack.enter_context(
            mock.patch('amsdal.contrib.auth.settings.auth_settings'),
        )
        auth_settings_mocked.AUTH_JWT_KEY = 'secret'
        auth_settings_mocked.AUTH_TOKEN_EXPIRATION = 3600
        auth_settings_mocked.ADMIN_USER_EMAIL = None
        auth_settings_mocked.ADMIN_USER_PASSWORD = None
        auth_settings_mocked.REQUIRE_DEFAULT_AUTHORIZATION = False
        auth_settings_mocked.REQUIRE_MFA_BY_DEFAULT = False
        auth_settings_mocked.MFA_TOTP_ISSUER = 'AMSDAL'
        auth_settings_mocked.MFA_BACKUP_CODES_COUNT = 10
        auth_settings_mocked.MFA_EMAIL_CODE_EXPIRATION = 300

        # Initialize manager with CRM models
        manager = stack.enter_context(
            init_manager_and_migrate(
                src_dir_path=PROJECT_DIR,
                db_execution_type=DbExecutionType.include_state_db,
                lakehouse_option=lakehouse_option,
                state_option=state_option,
                app_models_path=CRM_MODELS_PATH,
                app_transactions_path=None,
                app_fixtures_path=None,
                ACCESS_TOKEN=EXPIRATION_VALID_TOKEN,
                CONTRIBS=[
                    'amsdal.contrib.auth.app.AuthAppConfig',
                    'amsdal.contrib.frontend_configs.app.FrontendConfigAppConfig',
                    'amsdal_crm.app.CRMAppConfig',
                ],
            ),
        )

        # Invalidate schema manager to ensure clean state
        TableSchemasManager.invalidate()

        # Rebuild CRM models to ensure they're properly registered
        Pipeline.model_rebuild()
        Stage.model_rebuild()
        Deal.model_rebuild()
        EmailActivity.model_rebuild()
        Note.model_rebuild()
        Entity.model_rebuild()

        yield manager


@pytest.fixture()
def async_crm_manager(database_backend) -> Iterator[AmsdalManager]:
    """Initialize AmsdalManager with CRM models for async integration tests."""
    from amsdal_utils.config.manager import AmsdalConfigManager

    lakehouse_option = LakehouseOption.postgres if 'postgres' == database_backend.value else LakehouseOption.sqlite
    state_option = StateOption.postgres if 'postgres' == database_backend.value else StateOption.sqlite

    with ExitStack() as stack:
        # Mock auth settings (required for CRM operations)
        auth_settings_mocked = stack.enter_context(
            mock.patch('amsdal.contrib.auth.settings.auth_settings'),
        )
        auth_settings_mocked.AUTH_JWT_KEY = 'secret'
        auth_settings_mocked.AUTH_TOKEN_EXPIRATION = 3600
        auth_settings_mocked.ADMIN_USER_EMAIL = None
        auth_settings_mocked.ADMIN_USER_PASSWORD = None
        auth_settings_mocked.REQUIRE_DEFAULT_AUTHORIZATION = False
        auth_settings_mocked.REQUIRE_MFA_BY_DEFAULT = False
        auth_settings_mocked.MFA_TOTP_ISSUER = 'AMSDAL'
        auth_settings_mocked.MFA_BACKUP_CODES_COUNT = 10
        auth_settings_mocked.MFA_EMAIL_CODE_EXPIRATION = 300

        # Initialize manager with CRM models
        manager = stack.enter_context(
            init_manager_and_migrate(
                src_dir_path=PROJECT_DIR,
                db_execution_type=DbExecutionType.include_state_db,
                lakehouse_option=lakehouse_option,
                state_option=state_option,
                app_models_path=CRM_MODELS_PATH,
                app_transactions_path=None,
                app_fixtures_path=None,
                ACCESS_TOKEN=EXPIRATION_VALID_TOKEN,
                CONTRIBS=[
                    'amsdal.contrib.auth.app.AuthAppConfig',
                    'amsdal.contrib.frontend_configs.app.FrontendConfigAppConfig',
                    'amsdal_crm.app.CRMAppConfig',
                ],
            ),
        )

        # Enable async mode for this manager
        config = AmsdalConfigManager().get_config()
        original_async_mode = config.async_mode
        config.async_mode = True

        # Invalidate schema manager to ensure clean state
        TableSchemasManager.invalidate()

        # Rebuild CRM models to ensure they're properly registered
        Pipeline.model_rebuild()
        Stage.model_rebuild()
        Deal.model_rebuild()
        EmailActivity.model_rebuild()
        Note.model_rebuild()
        Entity.model_rebuild()

        yield manager

        # Restore original async mode
        config.async_mode = original_async_mode


@pytest.fixture
def mock_user():
    """Create a mock user for testing permissions."""
    user = mock.Mock()
    user.email = 'test@example.com'
    user.permissions = []
    return user


@pytest.fixture
def sample_pipeline(crm_manager):
    """Create a sample pipeline for testing."""
    from amsdal_crm.models.pipeline import Pipeline

    pipeline = Pipeline(
        name='Test Pipeline',
        description='A test sales pipeline',
        is_active=True,
    )
    pipeline.save(force_insert=True)
    return pipeline


@pytest.fixture
def sample_stage(crm_manager, sample_pipeline):
    """Create a sample stage for testing."""
    from amsdal_crm.models.stage import Stage

    stage = Stage(
        pipeline=sample_pipeline,
        name='Qualified',
        order=2,
        probability=25.0,
    )
    stage.save(force_insert=True)
    return stage


@pytest.fixture
def sample_entity(crm_manager):
    """Create a sample entity for testing."""
    from amsdal_crm.models.entity import Entity

    entity = Entity(
        name='Test Entity',
    )
    entity.save(force_insert=True)
    return entity


@pytest.fixture
def sample_deal_data(mock_user, sample_stage, sample_entity):
    """Sample deal data for testing."""
    return {
        'name': 'Enterprise Deal',
        'amount': 50000.00,
        'currency': 'USD',
        'entity': sample_entity,
        'stage': sample_stage,
        'expected_close_date': datetime(2026, 6, 1, tzinfo=UTC),
        'created_at': datetime(2026, 1, 1, tzinfo=UTC),
    }
