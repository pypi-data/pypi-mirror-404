# mlflow-cynex

Cynex trajectory viewer integration for MLflow. Adds a "View in Cynex" button to MLflow's artifact browser for trajectory JSON files.

## Installation

```bash
pip install mlflow-cynex
mlflow-cynex install
```

Then restart your MLflow server.

## Usage

### Logging Trajectories

The package provides a helper function to log trajectories to MLflow:

```python
from mlflow_cynex import log_trajectory
import mlflow

mlflow.set_tracking_uri("http://localhost:5000")

with mlflow.start_run():
    trajectory = {
        "blue_agent_name": "PPO",
        "red_agent_name": "Meander",
        "episode": 0,
        "blue_actions": [...],
        "red_actions": [...],
        "metric_scores": [...],
        "network_topology": {...}
    }
    log_trajectory(trajectory)
```

The trajectory is automatically:
- Validated against the expected schema
- Saved to `trajectories/<name>-trajectory.json` in MLflow artifacts

### Custom Naming

```python
log_trajectory(trajectory, name="my-custom-name")
# Saved as: trajectories/my-custom-name.json
```

### Validation Only

```python
from mlflow_cynex import validate_trajectory, TrajectoryValidationError

try:
    validate_trajectory(data)
except TrajectoryValidationError as e:
    print(f"Invalid trajectory: {e}")
```

## Trajectory Detection

The "View in Cynex" button appears for JSON files that:
- Are in a `trajectories/` folder, OR
- Match `*-trajectory.json` or `*_trajectory.json` pattern

## CLI Commands

```bash
mlflow-cynex install    # Install Cynex viewer into MLflow
mlflow-cynex uninstall  # Remove Cynex viewer from MLflow
mlflow-cynex status     # Check installation status
```

## Development

Build from source:

```bash
cd cynex/mlflow-integration
./scripts/build.sh
pip install dist/mlflow_cynex-*.whl
```

## License

MIT
