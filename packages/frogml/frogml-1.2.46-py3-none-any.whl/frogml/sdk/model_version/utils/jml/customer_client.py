import logging
import os
import sys
from typing import Optional, Dict, Any, TextIO, Union

from typing_extensions import Self

from frogml._proto.jfml.model_version.v1.model_version_framework_pb2 import (
    ModelVersionFramework,
)
from frogml.core.clients.administration.eco_system.client import EcosystemClient
from frogml.core.clients.model_version_manager import ModelVersionManagerClient
from frogml.core.exceptions import FrogmlException
from frogml.sdk.model_version.constants import FROGML_LOG_LEVEL_ENVAR_NAME
from frogml.storage.frog_ml import FrogMLStorage
from frogml.storage.models.frogml_model_version import FrogMLModelVersion
from frogml.storage.models.model_manifest import ModelManifest
from frogml.storage.models.serialization_metadata import SerializationMetadata


class JmlCustomerClient:
    """
    A class to handle customer-related operations in the JML system.
    """

    def __init__(self: Self):
        """
        Initializes the JmlCustomerClient
        """
        self.__model_version_manager_client = ModelVersionManagerClient()
        self.__ecosystem_client = EcosystemClient()
        self.__logger = logging.getLogger(type(self).__name__)
        self.__ml_storage = FrogMLStorage()
        self.__define_client_logger()

    def __define_client_logger(self, stream: Union[TextIO, Any] = sys.stdout):
        if self.__logger.hasHandlers():
            return

        console_handler = logging.StreamHandler(stream)
        log_level: str = logging.getLevelName(
            os.getenv(FROGML_LOG_LEVEL_ENVAR_NAME) or logging.INFO
        )
        console_handler.setLevel(log_level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        self.__logger.addHandler(console_handler)
        self.__logger.setLevel(log_level)

    def is_customer_exists_in_jml(self) -> bool:
        try:
            self.__logger.debug("Checking if customer exists in JML...")
            self.__ecosystem_client.get_authenticated_user_context()
            self.__logger.info("Customer exists in JML.")

            return True
        except FrogmlException:
            self.__logger.info("Customer does not exist in JML.")
            return False

    def validate_model_version(
        self: Self,
        repository: str,
        model_name: str,
        model_version: str,
        model_version_framework: ModelVersionFramework,
    ):
        try:
            self.__model_version_manager_client.validate_create_model_version(
                repository_key=repository,
                model_name=model_name,
                model_version_name=model_version,
                model_version_framework=model_version_framework,
                model_artifact=[],
            )
        except Exception as e:
            raise ValueError(str(e)) from e

    def log_model_to_artifactory(
        self: Self,
        dependencies: Optional[list[str]],
        full_model_path: str,
        model_name: str,
        properties: Optional[dict[str, str]],
        repository: str,
        version: str,
        metadata: SerializationMetadata,
        code_archive_file_path: Optional[str],
    ) -> FrogMLModelVersion:
        return self.__ml_storage.upload_model_version(
            repository=repository,
            model_name=model_name,
            model_path=full_model_path,
            model_type=metadata,
            version=version,
            properties=properties,
            dependencies_files_paths=dependencies,
            code_archive_file_path=code_archive_file_path,
        )

    def register_model_version_in_jml(
        self: Self,
        repository: str,
        model_name: str,
        model_version_name: str,
        model_version_framework: ModelVersionFramework,
        manifest: ModelManifest,
        parameters: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a model version in JFrog ML."""
        try:
            self.__model_version_manager_client.create_model_version(
                repository_key=repository,
                model_name=model_name,
                model_version_name=model_version_name,
                model_version_framework=model_version_framework,
                model_artifact=manifest.artifacts,
                dependency_artifacts=manifest.dependency_artifacts,
                code_artifacts=(
                    [manifest.code_artifacts] if manifest.code_artifacts else None
                ),
                parameters=parameters,
                metrics=metrics,
            )
        except FrogmlException as e:
            self.__logger.exception(
                "Failed to create model version %s in JFML due to this following error: '%s'\n\n"
                "Before retrying, please delete the uploaded artifact from Artifactory",
                model_version_name,
                e.message,
            )
            raise e
