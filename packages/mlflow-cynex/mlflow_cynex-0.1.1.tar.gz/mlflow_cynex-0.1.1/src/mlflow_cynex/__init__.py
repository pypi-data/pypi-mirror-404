"""MLflow integration for Cynex trajectory viewer."""

from mlflow_cynex.logging import (
    TrajectoryValidationError,
    log_trajectory,
    validate_trajectory,
)

try:
    from importlib.metadata import version
    __version__ = version("mlflow-cynex")
except Exception:
    __version__ = "0.0.0"
__all__ = ["log_trajectory", "validate_trajectory", "TrajectoryValidationError"]
