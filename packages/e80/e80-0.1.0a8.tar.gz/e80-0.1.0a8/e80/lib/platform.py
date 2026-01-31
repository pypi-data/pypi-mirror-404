from e80.lib.context import E80ContextObject
import requests
from pydantic import BaseModel
from typing import BinaryIO, Any
from e80.lib.project import CloudProjectConfig


class PlatformClient:
    def __init__(self, ctx_obj: E80ContextObject, api_key: str):
        self.api_key = api_key
        self.base_url = ctx_obj.platform_host
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
            }
        )

    def list_organization_memberships(self) -> "ListOrganizationMembershipsResponse":
        resp = self.session.get(f"{self.base_url}/api/org")
        resp.raise_for_status()
        return ListOrganizationMembershipsResponse.model_validate(resp.json())

    def create_project(self, config: CloudProjectConfig) -> "CreateProjectResponse":
        resp = self.session.put(
            f"{self.base_url}/api/project/{config.organization_slug}",
            json={"project_name": config.project},
        )
        resp.raise_for_status()

        return CreateProjectResponse.model_validate(resp.json())

    def start_upload_artifact_part(
        self, config: CloudProjectConfig
    ) -> "StartUploadPartArtifactResponse":
        config.require_project()

        resp = self.session.post(
            f"{self.base_url}/api/endpoint/{config.organization_slug}/{config.project_slug}/artifact/multipart",
            json=config.model_dump(),
        )
        resp.raise_for_status()

        return StartUploadPartArtifactResponse.model_validate(resp.json())

    def upload_artifact_part(
        self, config: CloudProjectConfig, artifact_id: str, part_num: int, part: bytes
    ):
        config.require_project()

        resp = self.session.post(
            f"{self.base_url}/api/endpoint/{config.organization_slug}/{config.project_slug}/artifact/multipart/{artifact_id}/{part_num}",
            files={"artifact_part": part},
        )
        resp.raise_for_status()

    def finish_upload_artifact_part(self, config: CloudProjectConfig, artifact_id: str):
        config.require_project()

        resp = self.session.post(
            f"{self.base_url}/api/endpoint/{config.organization_slug}/{config.project_slug}/artifact/multipart/{artifact_id}"
        )
        resp.raise_for_status()

    def upload_artifact(
        self, config: CloudProjectConfig, artifact: BinaryIO
    ) -> "UploadArtifactResponse":
        config.require_project()

        files: dict[str, BinaryIO | str] = {
            "artifact.zip": artifact,
            "config.json": config.model_dump_json(),
        }
        resp = self.session.post(
            f"{self.base_url}/api/endpoint/{config.organization_slug}/{config.project_slug}/artifact",
            files=files,
        )
        resp.raise_for_status()

        return UploadArtifactResponse.model_validate(resp.json())

    def deploy_artifact(
        self, config: CloudProjectConfig, artifact_id: str
    ) -> "DeployArtifactResponse":
        config.require_project()

        resp = self.session.post(
            f"{self.base_url}/api/endpoint/{config.organization_slug}/{config.project_slug}/deploy",
            json={"artifact_id": artifact_id},
        )
        resp.raise_for_status()

        return DeployArtifactResponse.model_validate(resp.json())

    def list_secrets_for_local(
        self, config: CloudProjectConfig
    ) -> "ListSecretsResponse":
        config.require_project()

        resp = self.session.get(
            f"{self.base_url}/api/secrets/{config.project_slug}?local=1"
        )
        resp.raise_for_status()
        return ListSecretsResponse.model_validate(resp.json())


class CreateProjectResponse(BaseModel):
    project_id: str
    project_slug: str


class OrganizationMembership(BaseModel):
    organization_id: str
    organization_name: str
    organization_slug: str
    membership: int


class UploadArtifactResponse(BaseModel):
    artifact_id: str


class StartUploadPartArtifactResponse(BaseModel):
    artifact_id: str


class DeployArtifactResponse(BaseModel):
    deployment_id: str


class ListOrganizationMembershipsResponse(BaseModel):
    memberships: list[OrganizationMembership]


class Secret(BaseModel):
    name: str
    type: str
    value: Any


class ListSecretsResponse(BaseModel):
    secrets: list[Secret]
