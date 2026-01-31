"""Unit tests for Pipeline model."""

from amsdal_crm.models.pipeline import Pipeline


def test_pipeline_creation(sample_pipeline_data):
    """Test creating a pipeline."""
    pipeline = Pipeline(**sample_pipeline_data)

    assert pipeline.name == 'Test Pipeline'
    assert pipeline.description == 'A test sales pipeline'
    assert pipeline.is_active is True


def test_pipeline_display_name(sample_pipeline_data):
    """Test pipeline display_name property."""
    pipeline = Pipeline(**sample_pipeline_data)

    assert pipeline.display_name == 'Test Pipeline'


def test_pipeline_default_is_active():
    """Test pipeline has is_active=True by default."""
    pipeline = Pipeline(name='Test Pipeline')

    assert pipeline.is_active is True


def test_pipeline_optional_description():
    """Test pipeline can be created without description."""
    pipeline = Pipeline(name='Test Pipeline')

    assert pipeline.description is None
