import grpc
from dependency_injector.wiring import Provide

from frogml._proto.qwak.administration.v0.environments.environment_pb2 import (
    QwakEnvironmentStatus,
)
from frogml._proto.qwak.administration.v0.environments.configuration_pb2 import (
    QwakEnvironmentConfiguration,
)
from frogml._proto.qwak.administration.v0.environments.environment_service_pb2 import (
    GetEnvironmentApplicationUserCredentialsRequest,
    GetEnvironmentApplicationUserCredentialsResponse,
    ListEnvironmentsRequest,
    ListEnvironmentsResponse,
    UpdateEnvironmentConfigurationRequest,
    UpdateEnvironmentConfigurationResponse,
)
from frogml._proto.qwak.administration.v0.environments.environment_service_pb2_grpc import (
    EnvironmentServiceStub,
)
from frogml.core.exceptions import FrogmlException
from frogml.core.inner.di_configuration import FrogmlContainer
from frogml.core.inner.tool.grpc.grpc_try_wrapping import grpc_try_catch_wrapper


class EnvironmentClient:
    """
    Used for interacting with Frogml's Environemt
    """

    def __init__(self, grpc_channel=Provide[FrogmlContainer.core_grpc_channel]):
        self._environment_service = EnvironmentServiceStub(grpc_channel)

    def list_environments(self) -> ListEnvironmentsResponse:
        """
        List of all environment without filter
        Return ListEnvironmentsResponse
        """
        request = ListEnvironmentsRequest()
        try:
            return self._environment_service.ListEnvironments(request)
        except grpc.RpcError as e:
            raise FrogmlException(
                f"Failed to get List of environments, error is {e.details()}"
            )

    def list_environments_by_status(
        self, status: QwakEnvironmentStatus
    ) -> ListEnvironmentsResponse:
        """
        List of all environment without filter
        Args: status which filter environment by
        Return: ListEnvironmentsResponse

        """
        try:
            request = ListEnvironmentsRequest(
                filter=ListEnvironmentsRequest.Filter(environment_status=status)
            )
            return self._environment_service.ListEnvironments(request)
        except grpc.RpcError as e:
            raise FrogmlException(
                f"Failed to get List of environments with status, error is {e.details()}"
            )

    def get_environment_application_user(
        self, environment_id: str
    ) -> GetEnvironmentApplicationUserCredentialsResponse:
        """
        Get application user by environment id
        Return: GetEnvironmentApplicationUserCredentialsResponse
        """
        request = GetEnvironmentApplicationUserCredentialsRequest(
            environment_id=environment_id
        )
        try:
            return self._environment_service.GetEnvironmentApplicationUserCredentials(
                request
            )
        except grpc.RpcError as e:
            raise FrogmlException(
                f"Failed to get application user, error is {e.details()}"
            )

    @grpc_try_catch_wrapper(
        "Failed to update environment configuration for {environment_id}"
    )
    def update_environment_configuration(
        self, environment_id: str, configuration: QwakEnvironmentConfiguration
    ) -> UpdateEnvironmentConfigurationResponse:
        """
        Update environment configuration.

        Args:
            environment_id: The environment ID to update.
            configuration: The new environment configuration.

        Returns:
            UpdateEnvironmentConfigurationResponse
        """
        request = UpdateEnvironmentConfigurationRequest(
            environment_id=environment_id,
            configuration=configuration,
        )
        return self._environment_service.UpdateEnvironmentConfiguration(request)
