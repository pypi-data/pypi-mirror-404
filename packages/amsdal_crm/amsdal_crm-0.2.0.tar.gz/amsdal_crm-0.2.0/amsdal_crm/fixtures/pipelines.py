"""Default pipeline and stage fixtures."""

# Default sales pipeline with stages
DEFAULT_PIPELINES = [
    {
        '_external_id': 'crm_default_pipeline_sales',
        'name': 'Sales Pipeline',
        'description': 'Default sales pipeline',
        'is_active': True,
    },
]

DEFAULT_STAGES = [
    {
        '_external_id': 'crm_stage_lead',
        '_order': 1.0,
        'pipeline': {'_external_id': 'crm_default_pipeline_sales'},
        'name': 'Lead',
        'order': 1,
        'probability': 10.0,
        'is_closed_won': False,
        'is_closed_lost': False,
    },
    {
        '_external_id': 'crm_stage_qualified',
        '_order': 2.0,
        'pipeline': {'_external_id': 'crm_default_pipeline_sales'},
        'name': 'Qualified',
        'order': 2,
        'probability': 25.0,
        'is_closed_won': False,
        'is_closed_lost': False,
    },
    {
        '_external_id': 'crm_stage_proposal',
        '_order': 3.0,
        'pipeline': {'_external_id': 'crm_default_pipeline_sales'},
        'name': 'Proposal',
        'order': 3,
        'probability': 50.0,
        'is_closed_won': False,
        'is_closed_lost': False,
    },
    {
        '_external_id': 'crm_stage_negotiation',
        '_order': 4.0,
        'pipeline': {'_external_id': 'crm_default_pipeline_sales'},
        'name': 'Negotiation',
        'order': 4,
        'probability': 75.0,
        'is_closed_won': False,
        'is_closed_lost': False,
    },
    {
        '_external_id': 'crm_stage_closed_won',
        '_order': 5.0,
        'pipeline': {'_external_id': 'crm_default_pipeline_sales'},
        'name': 'Closed Won',
        'order': 5,
        'probability': 100.0,
        'is_closed_won': True,
        'is_closed_lost': False,
    },
    {
        '_external_id': 'crm_stage_closed_lost',
        '_order': 6.0,
        'pipeline': {'_external_id': 'crm_default_pipeline_sales'},
        'name': 'Closed Lost',
        'order': 6,
        'probability': 0.0,
        'is_closed_won': False,
        'is_closed_lost': True,
    },
]
