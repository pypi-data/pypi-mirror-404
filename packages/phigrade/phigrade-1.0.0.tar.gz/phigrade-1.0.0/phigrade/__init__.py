# Import all functions from phigrade module
from .phigrade import (
    weight,
    phigrade_allclose,
    phigrade_isequal,
    PhiGradeConfig,
    load_phigrade_config,
)

# Make everything available at package level
__all__ = [
    'weight',
    'phigrade_allclose',
    'phigrade_isequal',
    'PhiGradeConfig',
    'load_phigrade_config',
]