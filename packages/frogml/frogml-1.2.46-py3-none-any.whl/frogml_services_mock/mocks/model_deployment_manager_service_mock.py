import uuid
from datetime import datetime, timezone
from typing import Callable, Optional

import grpc
from frogml._proto.com.jfrog.ml.model.deployment.v1.deployment_pb2 import (
    Deployment,
    DeploymentMetadata,
    ModelDeploymentInformation,
    ModelDeploymentStatus,
    ModelDeploymentStatusSuccessful,
    MultipleEnvironmentDeployment,
)
from frogml._proto.com.jfrog.ml.model.deployment.v1.deployment_service_pb2 import (
    DeployModelRequest,
    DeployModelResponse,
    EditModelDeploymentRequest,
    EditModelDeploymentResponse,
    GetModelDeploymentRequest,
    GetModelDeploymentResponse,
    ListModelDeploymentsRequest,
    ListModelDeploymentsResponse,
    UndeployModelRequest,
    UndeployModelResponse,
)
from frogml._proto.com.jfrog.ml.model.deployment.v1.deployment_service_pb2_grpc import (
    ModelDeploymentServiceServicer,
)
from frogml._proto.com.jfrog.ml.model.deployment.v1.model_artifact_identifier_pb2 import (
    ModelArtifactIdentifier,
    ModelBasedArtifactIdentifier,
)
from frogml._proto.com.jfrog.ml.model.deployment.v1.model_deployment_brief_pb2 import (
    ModelDeploymentBrief,
)
from google.protobuf.timestamp_pb2 import Timestamp
from pydantic import BaseModel, ConfigDict


class DeploymentInformation(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    deployment_id: uuid.UUID
    model_id: str
    model_group_id: str
    path: str
    environment_id: uuid.UUID
    deployment_config: Deployment
    created_at: datetime


class ModelDeploymentManagerMock(ModelDeploymentServiceServicer):
    def __init__(self):
        self.__deployment_id_to_spec: dict[str, DeploymentInformation] = {}

    @staticmethod
    def __get_model_identifier_details(
        model_artifact_identifier: ModelArtifactIdentifier,
    ) -> tuple[str, str, str]:
        identifier_type = model_artifact_identifier.WhichOneof("identifier_type")

        if identifier_type == "model_based_artifact_id":
            artifact = model_artifact_identifier.model_based_artifact_id
            return (
                artifact.model_id,
                artifact.model_group_id,
                artifact.image_path,
            )
        elif identifier_type == "custom_model_artifact_id":
            artifact = model_artifact_identifier.custom_model_artifact_id
            return (
                artifact.model_id,
                artifact.model_group_id,
                artifact.build_id,
            )

        raise Exception("No Model Artifact Identifier found")

    def DeployModel(
        self, request: DeployModelRequest, context: grpc.ServicerContext
    ) -> DeployModelResponse:
        multiple_environment_deployment: MultipleEnvironmentDeployment = (
            request.multiple_environment_deployment
        )
        model_artifact_identifier: ModelArtifactIdentifier = (
            multiple_environment_deployment.model_artifact_identifier
        )
        model_id, model_group_id, path = self.__get_model_identifier_details(
            model_artifact_identifier
        )

        self.__deployment_id_to_spec.update(
            {
                (deployment_id := str(uuid.uuid4())): DeploymentInformation(
                    deployment_id=uuid.UUID(deployment_id),
                    model_id=model_id,
                    model_group_id=model_group_id,
                    path=path,
                    environment_id=uuid.UUID(env_id),
                    deployment_config=deployment,
                    created_at=datetime.now(tz=timezone.utc),
                )
                for env_id, deployment in multiple_environment_deployment.deployments.items()
            }
        )

        return DeployModelResponse()

    def UndeployModel(
        self, request: UndeployModelRequest, context: grpc.ServicerContext
    ) -> UndeployModelResponse:
        deployment_ids = list(request.deployment_ids.deployment_id)
        for deployment_id in deployment_ids:
            self.__deployment_id_to_spec.pop(deployment_id)

        return UndeployModelResponse()

    def EditModelDeployment(
        self, request: EditModelDeploymentRequest, context: grpc.ServicerContext
    ) -> EditModelDeploymentResponse:
        deployment_map = dict(request.deployment_id_to_deployment_spec_map.deployments)
        for deployment_id, new_spec in deployment_map.items():
            if deployment_id not in self.__deployment_id_to_spec:
                raise Exception("Deployment id does not exist")
            self.__deployment_id_to_spec[deployment_id].deployment_config = new_spec

        return EditModelDeploymentResponse()

    @staticmethod
    def __build_filter_predicates(
        request: ListModelDeploymentsRequest,
    ) -> list[Callable[[DeploymentInformation], bool]]:
        """Build a list of filter predicates from the request."""
        predicates: list[Callable[[DeploymentInformation], bool]] = []

        if not request.model_deployment_filter.HasField(
            "simple_model_deployment_filter"
        ):
            return predicates

        simple_filter = request.model_deployment_filter.simple_model_deployment_filter

        if simple_filter.HasField("model_identifier_filter"):
            model_group_id = simple_filter.model_identifier_filter.model_group_id
            model_id = simple_filter.model_identifier_filter.model_id
            predicates.append(
                lambda d, model_group_id=model_group_id, model_id=model_id: d.model_group_id
                == model_group_id
                and d.model_id == model_id
            )

        if simple_filter.HasField("model_group_ids"):
            allowed_model_group_ids = set(simple_filter.model_group_ids.model_group_id)
            predicates.append(
                lambda d, allowed=allowed_model_group_ids: d.model_group_id in allowed
            )

        if simple_filter.HasField("model_ids"):
            allowed_model_ids = set(simple_filter.model_ids.model_id)
            predicates.append(
                lambda d, allowed=allowed_model_ids: d.model_id in allowed
            )

        if simple_filter.HasField("environment_ids"):
            allowed_environment_ids = set(simple_filter.environment_ids.environment_id)
            predicates.append(
                lambda d, allowed=allowed_environment_ids: str(d.environment_id)
                in allowed
            )

        return predicates

    @staticmethod
    def _deployment_to_brief(
        deployment_info: DeploymentInformation,
    ) -> ModelDeploymentBrief:
        """Convert a DeploymentInformation to a ModelDeploymentBrief."""
        timestamp = Timestamp()
        timestamp.FromDatetime(deployment_info.created_at)

        return ModelDeploymentBrief(
            status=ModelDeploymentStatus(
                model_deployment_status_successful=ModelDeploymentStatusSuccessful()
            ),
            environment=str(deployment_info.environment_id),
            created_at=timestamp,
            deployment_id=str(deployment_info.deployment_id),
            model_artifact_identifier=ModelArtifactIdentifier(
                model_based_artifact_id=ModelBasedArtifactIdentifier(
                    model_id=deployment_info.model_id,
                    model_group_id=deployment_info.model_group_id,
                    image_path=deployment_info.path,
                )
            ),
        )

    def ListModelDeployments(
        self, request: ListModelDeploymentsRequest, context: grpc.ServicerContext
    ) -> ListModelDeploymentsResponse:
        predicates: list[Callable[[DeploymentInformation], bool]] = (
            self.__build_filter_predicates(request)
        )

        result = [
            self._deployment_to_brief(deployment)
            for deployment in self.__deployment_id_to_spec.values()
            if all(predicate(deployment) for predicate in predicates)
        ]

        return ListModelDeploymentsResponse(model_deployment_brief=result)

    def GetModelDeployment(
        self, request: GetModelDeploymentRequest, context: grpc.ServicerContext
    ) -> GetModelDeploymentResponse:
        deployment_id = request.deployment_id
        deployment_info = self.__deployment_id_to_spec.get(deployment_id)

        if deployment_info is None:
            return GetModelDeploymentResponse()

        timestamp = Timestamp()
        timestamp.FromDatetime(deployment_info.created_at)

        model_artifact_identifier = ModelArtifactIdentifier(
            model_based_artifact_id=ModelBasedArtifactIdentifier(
                model_id=deployment_info.model_id,
                model_group_id=deployment_info.model_group_id,
                image_path=deployment_info.path,
            )
        )

        model_deployment_info = ModelDeploymentInformation(
            model_artifact_identifier=model_artifact_identifier,
            model_deployment_spec=deployment_info.deployment_config,
            model_deployment_metadata=DeploymentMetadata(
                deployment_id=str(deployment_info.deployment_id),
                status=ModelDeploymentStatus(
                    model_deployment_status_successful=ModelDeploymentStatusSuccessful()
                ),
                environment=str(deployment_info.environment_id),
                created_at=timestamp,
            ),
        )

        return GetModelDeploymentResponse(
            model_deployment_information=model_deployment_info
        )

    def get_deployment_by_id(
        self, deployment_id: str
    ) -> Optional[DeploymentInformation]:
        return self.__deployment_id_to_spec.get(deployment_id)

    def get_all_deployments(self) -> list[DeploymentInformation]:
        return list(self.__deployment_id_to_spec.values())
