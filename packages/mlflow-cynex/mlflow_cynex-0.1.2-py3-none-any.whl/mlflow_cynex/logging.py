"""Helpers for logging trajectories to MLflow."""

import json
import tempfile
from pathlib import Path
from typing import Any

import mlflow


class TrajectoryValidationError(Exception):
    """Raised when trajectory data fails validation."""

    pass


REQUIRED_FIELDS = [
    "blue_agent_name",
    "red_agent_name",
    "episode",
    "blue_actions",
    "red_actions",
    "metric_scores",
    "network_topology",
]


def validate_trajectory(data: dict[str, Any]) -> None:
    """Validate trajectory data structure.

    Args:
        data: Trajectory dictionary to validate.

    Raises:
        TrajectoryValidationError: If validation fails.
    """
    if not isinstance(data, dict):
        raise TrajectoryValidationError("Trajectory must be a dictionary")

    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        raise TrajectoryValidationError(f"Missing required fields: {', '.join(missing)}")

    if not isinstance(data["blue_actions"], list):
        raise TrajectoryValidationError("blue_actions must be a list")

    if not isinstance(data["red_actions"], list):
        raise TrajectoryValidationError("red_actions must be a list")

    if not isinstance(data["metric_scores"], list):
        raise TrajectoryValidationError("metric_scores must be a list")

    if not isinstance(data["network_topology"], dict):
        raise TrajectoryValidationError("network_topology must be a dictionary")


def log_trajectory(
    trajectory: dict[str, Any],
    name: str | None = None,
    artifact_path: str = "trajectories",
    validate: bool = True,
) -> str:
    """Log a trajectory to MLflow as an artifact.

    Args:
        trajectory: Trajectory dictionary containing episode data.
        name: Optional filename (without .json extension). Defaults to
            "{blue_agent_name}-vs-{red_agent_name}-ep{episode}-trajectory.json".
        artifact_path: MLflow artifact subdirectory. Defaults to "trajectories".
        validate: Whether to validate trajectory structure. Defaults to True.

    Returns:
        The artifact path where the trajectory was logged.

    Raises:
        TrajectoryValidationError: If validation is enabled and fails.
        mlflow.exceptions.MlflowException: If no active run exists.
    """
    if validate:
        validate_trajectory(trajectory)

    if name is None:
        blue = trajectory.get("blue_agent_name", "blue")
        red = trajectory.get("red_agent_name", "red")
        episode = trajectory.get("episode", 0)
        name = f"{blue}-vs-{red}-ep{episode}-trajectory"

    if not name.endswith(".json"):
        filename = f"{name}.json"
    else:
        filename = name

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / filename
        filepath.write_text(json.dumps(trajectory, indent=2))
        mlflow.log_artifact(str(filepath), artifact_path)

    return f"{artifact_path}/{filename}"
