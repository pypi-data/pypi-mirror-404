"""
ML Pipeline Feature

Phase 2: High priority feature (depends on data pipeline)
Pattern: Minimum Viable Decoupling (2 points, 2 layers)
Complexity: 5 points total

Architecture:
- main.py: Entry point and facade (1 point, 1 layer)
- implementation.py: ML workflow logic (2 points, 1 layer)
- feature_builder.py: Feature engineering (2 points, 1 layer)
- models.py: ML models and results (0 points)

Call Chain: 
Public API → MLPipelineImpl → Infrastructure
"""

from .main import MLPipelineImpl, create_ml_pipeline
from .reporting.training_report import TrainingReportGenerator, create_report_generator
__all__ = [
    'MLPipelineImpl',
    'create_ml_pipeline',
    'TrainingReportGenerator',
    'create_report_generator'
]
