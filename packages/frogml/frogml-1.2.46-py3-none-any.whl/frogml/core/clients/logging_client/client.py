from typing import Optional

from frogml._proto.qwak.logging.log_filter_pb2 import LogText, SearchFilter
from frogml._proto.qwak.logging.log_reader_service_pb2 import (
    ReadLogsRequest,
    ReadLogsResponse,
)
from frogml._proto.qwak.logging.log_reader_service_pb2_grpc import LogReaderServiceStub
from frogml._proto.qwak.logging.log_source_pb2 import (
    InferenceExecutionSource,
    LogSource,
    ModelRuntimeSource,
    RemoteBuildSource,
)
from frogml.core.clients.administration.eco_system.client import EcosystemClient
from frogml.core.exceptions import FrogmlException
from frogml.core.inner.tool.grpc.grpc_tools import create_grpc_channel
from frogml.core.inner.tool.grpc.grpc_try_wrapping import grpc_try_catch_wrapper


class LoggingClient:
    """
    Used for interacting with Logging endpoint
    """

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        enable_ssl: bool = True,
        environment_id: Optional[str] = None,
    ):
        if endpoint_url is None:
            user_context = EcosystemClient().get_authenticated_user_context().user
            if environment_id is None:
                environment_id = user_context.account_details.default_environment_id

            if environment_id not in user_context.account_details.environment_by_id:
                raise FrogmlException(
                    f"Configuration for environment [{environment_id}] was not found"
                )

            endpoint_url = user_context.account_details.environment_by_id[
                environment_id
            ].configuration.edge_services_url

        self._channel = create_grpc_channel(url=endpoint_url, enable_ssl=enable_ssl)

        self._logging_service = LogReaderServiceStub(self._channel)

    def read_build_logs(
        self,
        build_id: Optional[str] = None,
        before_offset: Optional[str] = None,
        after_offset: Optional[str] = None,
        max_number_of_results: Optional[int] = None,
        log_text_filter: Optional[str] = None,
        model_id: Optional[str] = None,
        model_group_name: Optional[str] = None,
    ) -> ReadLogsResponse:
        """
        Read logs for a remote build.

        Args:
            build_id: The build ID to fetch logs for
            before_offset: Optional offset to read logs before this point
            after_offset: Optional offset to read logs after this point
            max_number_of_results: Optional maximum number of log lines to return
            log_text_filter: Optional text filter to search for in logs
            model_id: The model ID. This is the display name(identifier), not the UUID.
            model_group_name: The model group name.

        Returns:
            ReadLogsResponse containing the log lines

        Raises:
            FrogmlException: If reading logs fails
        """
        try:
            remote_build_source = RemoteBuildSource(
                build_id=build_id,
                model_id=model_id,
                model_group_name=model_group_name,
            )

            response = self.read_logs(
                source=LogSource(remote_build=remote_build_source),
                before_offset=before_offset,
                after_offset=after_offset,
                log_text_filter=log_text_filter,
                max_number_of_results=max_number_of_results,
            )

            return response
        except FrogmlException as e:
            raise FrogmlException(f"Failed to fetch build logs, error is [{e}]")

    def read_model_runtime_logs(
        self,
        build_id: Optional[str] = None,
        deployment_id: Optional[str] = None,
        before_offset: Optional[str] = None,
        after_offset: Optional[str] = None,
        max_number_of_results: Optional[int] = None,
        log_text_filter: Optional[str] = None,
        model_id: Optional[str] = None,
        model_group_name: Optional[str] = None,
    ) -> ReadLogsResponse:
        """
        Read logs for a model runtime (deployment).

        Args:
            build_id: The build ID to fetch logs for
            deployment_id: The deployment ID to fetch logs for
            before_offset: Optional offset to read logs before this point
            after_offset: Optional offset to read logs after this point
            max_number_of_results: Optional maximum number of log lines to return
            log_text_filter: Optional text filter to search for in logs
            model_id: The model ID. This is the display name(identifier), not the UUID.
            model_group_name: The model group name.

        Returns:
            ReadLogsResponse containing the log lines

        Raises:
            FrogmlException: If reading logs fails
        """
        try:
            model_runtime_source = ModelRuntimeSource(
                build_id=build_id,
                deployment_id=deployment_id,
                model_id=model_id,
                model_group_name=model_group_name,
            )

            response = self.read_logs(
                source=LogSource(model_runtime=model_runtime_source),
                before_offset=before_offset,
                after_offset=after_offset,
                log_text_filter=log_text_filter,
                max_number_of_results=max_number_of_results,
            )

            return response
        except FrogmlException as e:
            raise FrogmlException(f"Failed to fetch runtime logs, error is [{e}]")

    def read_execution_models_logs(
        self,
        execution_id: str,
        before_offset: Optional[str] = None,
        after_offset: Optional[str] = None,
        max_number_of_results: Optional[int] = None,
        log_text_filter: Optional[str] = None,
        model_id: Optional[str] = None,
        model_group_name: Optional[str] = None,
    ) -> ReadLogsResponse:
        """
        Read logs for a model inference execution (batch job).

        Args:
            execution_id: The execution/inference job ID to fetch logs for
            before_offset: Optional offset to read logs before this point
            after_offset: Optional offset to read logs after this point
            max_number_of_results: Optional maximum number of log lines to return
            log_text_filter: Optional text filter to search for in logs
            model_id: The model ID. This is the display name(identifier), not the UUID.
            model_group_name: The model group name.

        Returns:
            ReadLogsResponse containing the log lines

        Raises:
            FrogmlException: If reading logs fails
        """
        try:
            inference_execution_source = InferenceExecutionSource(
                inference_job_id=execution_id,
                model_id=model_id,
                model_group_name=model_group_name,
            )

            response = self.read_logs(
                source=LogSource(inference_execution=inference_execution_source),
                before_offset=before_offset,
                after_offset=after_offset,
                log_text_filter=log_text_filter,
                max_number_of_results=max_number_of_results,
            )

            return response
        except FrogmlException as e:
            raise FrogmlException(f"Failed to fetch execution logs, error is [{e}]")

    @grpc_try_catch_wrapper("Failed to read logs request")
    def read_logs(
        self,
        source: LogSource,
        before_offset: Optional[str],
        after_offset: Optional[str],
        max_number_of_results: Optional[int],
        log_text_filter: Optional[str],
    ) -> ReadLogsResponse:
        """
        Low-level method to read logs from any source.

        Args:
            source: The log source to read from
            before_offset: Optional offset to read logs before this point
            after_offset: Optional offset to read logs after this point
            max_number_of_results: Optional maximum number of log lines to return
            log_text_filter: Optional text filter to search for in logs

        Returns:
            ReadLogsResponse containing the log lines
        """
        response: ReadLogsResponse = self._logging_service.ReadLogs(
            ReadLogsRequest(
                source=source,
                before_offset=before_offset,
                after_offset=after_offset,
                search_filter=SearchFilter(
                    log_text_filter=LogText(contains=log_text_filter)
                ),
                max_number_of_results=max_number_of_results,
            )
        )
        return response
