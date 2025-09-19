from dataclasses import InitVar, dataclass, field
from typing import Dict, List
import boto3
import logging
from pathlib import Path
import zipfile
from mypy_boto3_lambda import LambdaClient
from mypy_boto3_lambda.literals import RuntimeType


from ..boto_client_factory import AwsService, BotoClientFactory
from ....enums import InfraEnvironment
from ..creds import CredentialsProvider
from .build_runner import RUNTIME_BUILDERS

logger = logging.getLogger(__name__)


class LambdaUtil:
    _infrastructure_dir: Path
    creds: CredentialsProvider
    environment: InfraEnvironment
    _client_factory: BotoClientFactory

    def __init__(
        self,
        creds: CredentialsProvider,
        environment: InfraEnvironment,
        infrastructure_dir: Path,
        client_factory: BotoClientFactory,
    ):
        self.creds = creds
        self.environment = environment
        self._infrastructure_dir = infrastructure_dir
        self._client_factory = client_factory

    @property
    def _lambda_client(self) -> LambdaClient:
        return self._client_factory.client(AwsService.LAMBDA)

    @property
    def output_dir(self) -> Path:
        return Path.joinpath(self._infrastructure_dir, "out")

    def add_lambda(self, lambda_params: "AWSLambdaParameters"):

        zip_path = self._build_and_zip_lambda(
            project_root=lambda_params.project_root,
            output_dir=self.output_dir,
            runtime=lambda_params.runtime,
        )

        self._create_lambda(
            zip_path=zip_path,
            role="arn:aws:iam::000000000000:role/lambda-role",
            lambda_params=lambda_params,
        )

        self._add_lambda_permission_for_apigateway(
            function_name=lambda_params.function_name, statement_id="apigateway-access"
        )

    def _build_and_zip_lambda(
        self, project_root: Path, output_dir: Path, runtime: RuntimeType
    ):
        """
        Builds a .NET project in Release mode and zips the output for Lambda deployment.
        :param project_path: Path to the .NET project (.csproj)
        :param output_zip: Path to the output zip file
        """

        project_root = Path(project_root).resolve()

        output_dir.mkdir(parents=True, exist_ok=True)
        build_dir = output_dir / "build"
        build_dir.mkdir(exist_ok=True)

        runner_cls = RUNTIME_BUILDERS.get(runtime)
        if not runner_cls:
            raise NotImplementedError(
                f"Build runner for runtime '{runtime}' not implemented"
            )

        runner = runner_cls()
        runner.build(project_root, build_dir)

        # Zip the build directory
        zip_path = output_dir / f"{project_root.name}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in build_dir.rglob("*"):
                zipf.write(file_path, arcname=file_path.relative_to(build_dir))

        logger.info(f"Lambda zip created at {zip_path}")
        return zip_path

    def _create_lambda(
        self, zip_path: str, role: str, lambda_params: "AWSLambdaParameters"
    ):

        with open(zip_path, "rb") as f:
            zip_bytes = f.read()

        try:
            self._lambda_client.create_function(
                FunctionName=lambda_params.function_name,
                Runtime=lambda_params.runtime,
                Role=role,
                Handler=lambda_params.handler,
                Code={"ZipFile": zip_bytes},
                Environment={"Variables": lambda_params.filtered_env_vars},
                MemorySize=lambda_params.memory_size,
                Timeout=lambda_params.timeout_secs,
            )
            logger.info(f"Lambda function '{lambda_params.function_name}' created.")
        except self._lambda_client.exceptions.ResourceConflictException:
            logger.info(
                f"Lambda function '{lambda_params.function_name}' already exists."
            )

    def _add_lambda_permission_for_apigateway(
        self, function_name: str, statement_id: str
    ):

        try:
            self._lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=statement_id,
                Action="lambda:InvokeFunction",
                Principal="apigateway.amazonaws.com",
                SourceArn=f"arn:aws:execute-api:{self.creds.region}:000000000000:local/*/*/*",
            )
            logger.info(
                f"Permission added for API Gateway on Lambda '{function_name}'."
            )
        except self._lambda_client.exceptions.ResourceConflictException:
            logger.info(
                f"Permission '{statement_id}' already exists for Lambda '{function_name}'."
            )


@dataclass
class AWSLambdaParameters:
    function_name: str
    memory_size: int
    timeout_secs: int
    project_root: Path
    handler: str
    environment: InfraEnvironment
    runtime: RuntimeType
    env_vars: InitVar[Dict[str, str]]
    allowed_env_vars: List[str] = field(
        default_factory=lambda: [
            "TARGET_ENV",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_DEFAULT_REGION",
        ]
    )

    def __post_init__(self, env_vars: Dict[str, str]):
        self._filtered_env_vars = {
            k: v for k, v in env_vars.items() if k in self.allowed_env_vars
        }

    @property
    def filtered_env_vars(self) -> Dict[str, str]:
        return self._filtered_env_vars
