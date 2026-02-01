"""
Training Report Module

Backward-compatible facade for refactored training report generation.

**Refactoring Note**: Original 852-line TrainingReportGenerator split into:
- generator.py (Main orchestrator, ~200 lines)
- sections/summary.py (Header & metadata, ~270 lines)
- sections/metrics.py (Performance metrics, ~280 lines)
- sections/features.py (Feature analysis, ~120 lines)
- sections/diagnostics.py (Market analysis, ~550 lines)

Total: ~1,420 lines distributed across focused modules (no duplication, enhanced functionality)
Original: 852 lines (monolithic)

**Backward Compatibility**: Maintains exact same public API
```python
from nflfastRv3.features.ml_pipeline.reporting import create_report_generator

# Old API still works
reporter = create_report_generator(logger=None)
report_path = reporter.generate_report(
    model=model,
    X_train=X_train,
    X_test=X_test,
    # ... all original parameters
)
```
"""

from .generator import TrainingReportGenerator, create_report_generator

__all__ = ['TrainingReportGenerator', 'create_report_generator']
