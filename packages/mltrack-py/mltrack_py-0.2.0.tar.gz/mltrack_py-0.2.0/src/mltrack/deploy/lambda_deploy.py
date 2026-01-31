"""AWS Lambda packaging for MLTrack models."""

from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from mlflow.tracking import MlflowClient

from mltrack.config import MLTrackConfig
from mltrack.model_registry import ModelRegistry


LAMBDA_HANDLER = '''import json
import os
import mlflow.pyfunc

_MODEL = None


def _load_model():
    global _MODEL
    if _MODEL is None:
        model_path = os.path.join(os.path.dirname(__file__), "model")
        _MODEL = mlflow.pyfunc.load_model(model_path)
    return _MODEL


def handler(event, context):
    model = _load_model()

    payload = event.get("body", event)
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON body"})}

    data = payload.get("data", payload)
    try:
        predictions = model.predict(data)
    except Exception as exc:
        return {"statusCode": 500, "body": json.dumps({"error": str(exc)})}

    if hasattr(predictions, "tolist"):
        predictions = predictions.tolist()

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"predictions": predictions}),
    }
'''


class LambdaPackageBuilder:
    """Build an AWS Lambda-compatible package for an MLflow model."""

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        mlflow_client: Optional[MlflowClient] = None,
        config: Optional[MLTrackConfig] = None,
    ) -> None:
        self.config = config or MLTrackConfig.find_config()
        self.registry = registry or ModelRegistry(self.config)
        self.client = mlflow_client or MlflowClient(self.config.tracking_uri)

    def build_package(
        self,
        model_name: str,
        run_id: Optional[str] = None,
        model_path: str = "model",
        output_dir: Optional[str] = None,
        zip_path: Optional[str] = None,
        include_requirements: bool = True,
        requirements: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Build a Lambda zip package for a model."""
        if not model_name:
            raise ValueError("model_name is required for Lambda packaging")

        if run_id:
            try:
                self.registry.get_model(model_name)
            except Exception:
                self.registry.register_model(run_id, model_name, model_path)
        else:
            model_info = self.registry.get_model(model_name)
            run_id = model_info["run_id"]

        build_dir = Path(output_dir or tempfile.mkdtemp(prefix=f"mltrack-lambda-{model_name}-"))
        build_dir.mkdir(parents=True, exist_ok=True)

        model_dir = build_dir / "model"
        model_dir.mkdir(parents=True, exist_ok=True)
        self.client.download_artifacts(run_id, model_path, str(model_dir))

        handler_path = build_dir / "lambda_function.py"
        handler_path.write_text(LAMBDA_HANDLER)

        requirements_path = None
        if include_requirements:
            requirements_path = build_dir / "requirements.txt"
            if requirements:
                requirements_path.write_text("\n".join(requirements) + "\n")
            else:
                model_requirements = model_dir / "requirements.txt"
                if model_requirements.exists():
                    shutil.copyfile(model_requirements, requirements_path)
                else:
                    requirements_path.write_text("mlflow\ncloudpickle\n")

        if zip_path is None:
            zip_path = str(Path.cwd() / f"{model_name}-lambda.zip")
        zip_path = Path(zip_path)
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for path in build_dir.rglob("*"):
                if path.is_file():
                    bundle.write(path, path.relative_to(build_dir))

        return {
            "model_name": model_name,
            "run_id": run_id,
            "output_dir": str(build_dir),
            "package_path": str(zip_path),
            "requirements_path": str(requirements_path) if requirements_path else None,
        }


def build_lambda_package(
    model_name: str,
    run_id: Optional[str] = None,
    model_path: str = "model",
    output_dir: Optional[str] = None,
    zip_path: Optional[str] = None,
    include_requirements: bool = True,
    requirements: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Convenience wrapper for building Lambda packages."""
    builder = LambdaPackageBuilder()
    return builder.build_package(
        model_name=model_name,
        run_id=run_id,
        model_path=model_path,
        output_dir=output_dir,
        zip_path=zip_path,
        include_requirements=include_requirements,
        requirements=requirements,
    )


__all__ = ["LambdaPackageBuilder", "build_lambda_package"]
