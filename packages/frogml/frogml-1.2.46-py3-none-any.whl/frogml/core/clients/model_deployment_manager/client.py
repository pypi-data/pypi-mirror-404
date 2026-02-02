from dependency_injector.wiring import Provide
from frogml._proto.com.jfrog.ml.model.deployment.v1.deployment_pb2 import (
    Deployment,
    ModelDeploymentInformation,
    MultipleEnvironmentDeployment,
)
from frogml._proto.com.jfrog.ml.model.deployment.v1.deployment_service_pb2 import (
    DeploymentIds,
    DeploymentIdToDeploymentSpecMap,
    DeployModelRequest,
    EditModelDeploymentRequest,
    GetModelDeploymentResponse,
    ListModelDeploymentsRequest,
    ListModelDeploymentsResponse,
    UndeployModelRequest,
)
from frogml._proto.com.jfrog.ml.model.deployment.v1.deployment_service_pb2_grpc import (
    ModelDeploymentServiceStub,
)
from frogml._proto.com.jfrog.ml.model.deployment.v1.model_artifact_identifier_pb2 import (
    ModelArtifactIdentifier,
    ModelBasedArtifactIdentifier,
)
from frogml._proto.com.jfrog.ml.model.deployment.v1.model_deployment_brief_pb2 import (
    ModelDeploymentBrief,
)
from frogml._proto.com.jfrog.ml.model.deployment.v1.model_deployment_filter_pb2 import (
    ModelDeploymentFilter,
)
from frogml._proto.qwak.deployment.deployment_service_pb2 import GetDeploymentRequest
from frogml.core.inner.di_configuration import FrogmlContainer
from frogml.core.inner.tool.grpc.grpc_try_wrapping import grpc_try_catch_wrapper


class ModelDeploymentManagerClient:
    def __init__(self, grpc_channel=Provide[FrogmlContainer.core_grpc_channel]):
        self.__client = ModelDeploymentServiceStub(grpc_channel)

    @grpc_try_catch_wrapper("Failed to deploy LLM for model {model_id}")
    def deploy_llm(
        self,
        model_id: str,
        model_group_id: str,
        image_path: str,
        environment_deployment_configuration: dict[str, Deployment],
    ) -> None:
        llm_model_identifier = ModelBasedArtifactIdentifier(
            model_group_id=model_group_id,
            model_id=model_id,
            image_path=image_path,
        )
        model_artifact_identifier = ModelArtifactIdentifier(
            model_based_artifact_id=llm_model_identifier
        )
        multiple_environment_deployment = MultipleEnvironmentDeployment(
            model_artifact_identifier=model_artifact_identifier,
            deployments=environment_deployment_configuration,
        )
        request = DeployModelRequest(
            multiple_environment_deployment=multiple_environment_deployment
        )

        self.__client.DeployModel(request)

    @grpc_try_catch_wrapper("Failed to undeploy")
    def undeploy(self, deployment_ids: list[str]) -> None:
        deployment_ids_proto = DeploymentIds(deployment_id=deployment_ids)
        request = UndeployModelRequest(deployment_ids=deployment_ids_proto)
        self.__client.UndeployModel(request)

    @grpc_try_catch_wrapper("Failed to edit deployments")
    def edit_deployments(
        self, deployment_id_to_spec_map: dict[str, Deployment]
    ) -> None:
        deployments_map = DeploymentIdToDeploymentSpecMap(
            deployments=deployment_id_to_spec_map
        )
        request = EditModelDeploymentRequest(
            deployment_id_to_deployment_spec_map=deployments_map
        )
        self.__client.EditModelDeployment(request)

    @grpc_try_catch_wrapper("Failed to list deployments")
    def list_deployments(
        self,
        model_deployment_filter: ModelDeploymentFilter = None,
    ) -> list[ModelDeploymentBrief]:
        if model_deployment_filter is None:
            model_deployment_filter = ModelDeploymentFilter()

        request = ListModelDeploymentsRequest(
            model_deployment_filter=model_deployment_filter
        )
        response: ListModelDeploymentsResponse = self.__client.ListModelDeployments(
            request
        )
        return list(response.model_deployment_brief)

    @grpc_try_catch_wrapper("Failed to get deployment with ID {deployment_id}")
    def get_deployment(self, deployment_id: str) -> ModelDeploymentInformation:
        request = GetDeploymentRequest(deployment_id=deployment_id)
        response: GetModelDeploymentResponse = self.__client.GetModelDeployment(request)
        return response.model_deployment_information
