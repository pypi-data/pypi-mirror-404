import requests
import yaml
from pydantic import BaseModel
from typing import BinaryIO, Any
from e80.lib.project import CloudProjectConfig


class APIClient:
    def __init__(self, base_url: str, api_key: str):
        base_url = base_url.rstrip("/")

        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
            }
        )

    def upload_artifact(
        self, config: CloudProjectConfig, artifact: BinaryIO
    ) -> "UploadArtifactResponse":
        files: list[tuple[str, str | BinaryIO]] = [
            # Redump the config as YAML.
            # This essentially removes unknown fields
            ("", yaml.dump(config.model_dump(exclude_none=True, exclude_unset=True))),
            ("", artifact),
        ]

        resp = self.session.post(
            f"{self.base_url}/v1/jobs/{config.project_slug}/artifact",
            files=files,
        )
        resp.raise_for_status()

        return UploadArtifactResponse.model_validate(resp.json())

    def deploy_artifact(
        self, config: CloudProjectConfig, artifact_id: str
    ) -> "DeployArtifactResponse":
        resp = self.session.post(
            f"{self.base_url}/v1/jobs/{config.project_slug}/deploy",
            json={
                "artifact_id": artifact_id,
            },
        )
        resp.raise_for_status()

        return DeployArtifactResponse.model_validate(resp.json())


class UploadArtifactResponse(BaseModel):
    artifact_id: str


class DeployArtifactResponse(BaseModel):
    deployment_id: str
