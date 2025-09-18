import logging
from pathlib import Path

from mypy_boto3_apigateway import APIGatewayClient

from .boto_client_factory import BotoClientFactory
from .aws_services_enum import AwsService
from ..enums import Environment
from .creds import CredentialsProvider

logger = logging.getLogger(__name__)


class APIGatewayUtil:
    creds: CredentialsProvider
    _client_factory: BotoClientFactory
    environment: Environment
    config_dir: Path

    def __init__(
        self,
        creds: CredentialsProvider,
        config_dir: Path,
        environment: Environment,
        client_factory: BotoClientFactory,
    ):
        self.creds = creds
        self.config_dir: Path = config_dir
        self.environment = environment
        self._client_factory = client_factory

    @property
    def apigateway_client(self) -> APIGatewayClient:
        return self._client_factory.client(AwsService.APIGateway)

    def create_api_gateway(
        self, api_id: str, gateway_config_file: str = "apigateway.json"
    ):
        api_id = self._create_api_with_custom_id(
            name=f"{api_id}",
            custom_id=f"{api_id}",
        )
        self._import_api_definition(
            api_id=api_id,
            json_file=Path.joinpath(self.config_dir, gateway_config_file),
        )
        self._deploy_api_gateway(api_id, stage_name=self.environment)

    def _create_api_with_custom_id(self, name: str, custom_id: str) -> str:
        response = self.apigateway_client.create_rest_api(
            name=name, tags={"_custom_id_": custom_id}
        )
        api_id = response["id"]
        logger.info(f"API Gateway created with custom ID: {api_id}")
        return api_id

    def _import_api_definition(self, api_id: str, json_file: str):
        with open(json_file, "r") as f:
            body = f.read()

        self.apigateway_client.put_rest_api(
            restApiId=api_id, mode="overwrite", body=body
        )
        logger.info(f"API definition imported into API {api_id}")

    def _deploy_api_gateway(self, api_id: str, stage_name: str):
        self.apigateway_client.create_deployment(restApiId=api_id, stageName=stage_name)
        logger.info(f"API Gateway '{api_id}' deployed to stage '{stage_name}'.")
