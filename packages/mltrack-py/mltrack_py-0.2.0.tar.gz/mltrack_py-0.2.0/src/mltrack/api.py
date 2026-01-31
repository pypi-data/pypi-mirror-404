"""Public helper API for MLTrack."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from mlflow.tracking import MlflowClient

from mltrack.config import MLTrackConfig
from mltrack.deploy import DeploymentConfig, LambdaPackageBuilder, deploy_to_modal
from mltrack.deployment.docker.uv_builder import DockerBuilder
from mltrack.model_registry import ModelRegistry


def get_last_run(
    experiment_name: Optional[str] = None,
    tracking_uri: Optional[str] = None,
) -> str:
    """Return the most recent MLflow run ID."""
    config = MLTrackConfig.find_config()
    client = MlflowClient(tracking_uri or config.tracking_uri)

    if experiment_name:
        experiment = client.get_experiment_by_name(experiment_name)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_name}")
        experiment_ids = [experiment.experiment_id]
    else:
        experiments = client.search_experiments()
        if not experiments:
            raise ValueError("No experiments found")
        experiment_ids = [exp.experiment_id for exp in experiments]

    runs = client.search_runs(
        experiment_ids,
        order_by=["start_time DESC"],
        max_results=1,
    )
    if not runs:
        raise ValueError("No runs found")
    return runs[0].info.run_id


def deploy(
    run_id: Optional[str] = None,
    *,
    platform: str = "modal",
    name: Optional[str] = None,
    model_version: str = "latest",
    cpu: float = 1.0,
    memory: int = 512,
    gpu: Optional[str] = None,
    min_replicas: int = 1,
    max_replicas: int = 5,
    python_version: str = "3.11",
    env_vars: Optional[Dict[str, str]] = None,
    requirements: Optional[List[str]] = None,
    tracking_uri: Optional[str] = None,
    artifact_path: str = "model",
    docker_push: bool = False,
    docker_registry_url: Optional[str] = None,
    docker_platforms: Optional[List[str]] = None,
    docker_optimize: bool = True,
    docker_use_gpu: bool = False,
    lambda_output_dir: Optional[str] = None,
    lambda_zip_path: Optional[str] = None,
    lambda_requirements: Optional[List[str]] = None,
    lambda_include_requirements: bool = True,
) -> Dict[str, Any]:
    """Deploy a run to a supported platform."""
    normalized_platform = platform.lower()
    config = MLTrackConfig.find_config()

    if not run_id and normalized_platform != "docker":
        run_id = get_last_run(tracking_uri=tracking_uri)

    model_name = name or (f"run-{run_id[:8]}" if run_id else None)
    if normalized_platform == "modal":
        app_name = f"mltrack-{model_name}".lower().replace(" ", "-").replace("_", "-")
        config = DeploymentConfig(
            app_name=app_name,
            model_name=model_name,
            model_version=model_version,
            cpu=cpu,
            memory=memory,
            gpu=gpu,
            min_replicas=min_replicas,
            max_replicas=max_replicas,
            environment_vars=env_vars,
            requirements=requirements,
            python_version=python_version,
        )
        return deploy_to_modal(run_id, config, artifact_path=artifact_path)

    if normalized_platform == "docker":
        registry = ModelRegistry(config)
        if not run_id:
            if not model_name:
                raise ValueError("Provide run_id or name for docker deployment")
            model_info = registry.get_model(model_name)
            run_id = model_info["run_id"]
        else:
            if not model_name:
                model_name = f"run-{run_id[:8]}"
            try:
                registry.get_model(model_name)
            except Exception:
                registry.register_model(run_id, model_name, artifact_path)

        docker_version = None if model_version == "latest" else model_version
        builder = DockerBuilder(registry)
        return builder.build_container(
            model_name=model_name,
            version=docker_version,
            use_gpu=docker_use_gpu,
            optimize=docker_optimize,
            push=docker_push,
            registry_url=docker_registry_url,
            platform=docker_platforms,
        )

    if normalized_platform == "lambda":
        if not model_name:
            raise ValueError("Provide run_id or name for lambda deployment")
        builder = LambdaPackageBuilder(config=config)
        return builder.build_package(
            model_name=model_name,
            run_id=run_id,
            model_path=artifact_path,
            output_dir=lambda_output_dir,
            zip_path=lambda_zip_path,
            include_requirements=lambda_include_requirements,
            requirements=lambda_requirements or requirements,
        )

    raise ValueError(f"Unsupported platform: {platform}")


__all__ = ["get_last_run", "deploy"]
