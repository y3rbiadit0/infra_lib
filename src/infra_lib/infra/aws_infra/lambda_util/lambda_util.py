from dataclasses import InitVar, dataclass, field
import shutil
from typing import Dict, List, Optional
import logging
from pathlib import Path
from ..api_gateway_util import APIGatewayUtil
from mypy_boto3_lambda import LambdaClient
from mypy_boto3_lambda.literals import RuntimeType


from ..boto_client_factory import AwsService, BotoClientFactory
from ....enums import InfraEnvironment
from ..creds import CredentialsProvider
from .lambda_zip_builder import DEFAULT_BUILDER_BY_RUNTIME, BaseLambdaZipBuilder

logger = logging.getLogger(__name__)


class LambdaUtil:
	_infrastructure_dir: Path
	creds: CredentialsProvider
	environment: InfraEnvironment
	_client_factory: BotoClientFactory
	config_dir: Path

	def __init__(
		self,
		creds: CredentialsProvider,
		environment: InfraEnvironment,
		infrastructure_dir: Path,
		client_factory: BotoClientFactory,
		config_dir: Path,
	):
		self.creds = creds
		self.environment = environment
		self._infrastructure_dir = infrastructure_dir
		self._client_factory = client_factory
		self.config_dir = config_dir

	@property
	def _lambda_client(self) -> LambdaClient:
		return self._client_factory.client(AwsService.LAMBDA)

	@property
	def output_dir(self) -> Path:
		return Path.joinpath(self._infrastructure_dir, "out")

	def add_lambda(self, lambda_params: "AWSLambdaParameters"):
		zip_path = self._build_lambda(
			lambda_params=lambda_params,
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

		self._log_lambda_paths_from_apigateway(
			lambda_name=lambda_params.function_name, api_id=lambda_params.api_id
		)

	def _build_lambda(
		self,
		lambda_params: "AWSLambdaParameters",
		output_dir: Path,
		runtime: RuntimeType,
	):
		"""
		Builds a .NET project in Release mode and zips the output for Lambda deployment.
		:param project_path: Path to the .NET project (.csproj)
		:param output_zip: Path to the output zip file
		"""
		project_root = Path(lambda_params.project_root).resolve()
		output_dir.mkdir(parents=True, exist_ok=True)
		
		build_dir = output_dir / "build" / project_root.name
		
		if build_dir.exists():
			shutil.rmtree(build_dir)
		build_dir.mkdir(parents=True, exist_ok=True)

		lambda_builder = lambda_params.custom_lambda_builder

		if lambda_builder is None:
			default_lambda_builder_cls = DEFAULT_BUILDER_BY_RUNTIME.get(runtime)
		
			if not default_lambda_builder_cls:
				raise NotImplementedError(
					f"`custom_lambda_builder` not provided and Default Build runner for runtime '{runtime}' not implemented. Must provide a `custom_lambda_builder` or correct the runtime {runtime}"
				)
			lambda_builder = default_lambda_builder_cls()

		lambda_zip_file = lambda_builder.build(
			project_root=project_root, build_dir=build_dir, output_dir=output_dir
		)
		

		logger.info(f"Lambda zip created at {lambda_zip_file}")
		
		return lambda_zip_file

	def _create_lambda(self, zip_path: str, role: str, lambda_params: "AWSLambdaParameters"):
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
			logger.info(f"Lambda function '{lambda_params.function_name}' already exists.")

	def _add_lambda_permission_for_apigateway(self, function_name: str, statement_id: str):
		try:
			self._lambda_client.add_permission(
				FunctionName=function_name,
				StatementId=statement_id,
				Action="lambda:InvokeFunction",
				Principal="apigateway.amazonaws.com",
				SourceArn=f"arn:aws:execute-api:{self.creds.region}:000000000000:local/*/*/*",
			)
			logger.info(f"Permission added for API Gateway on Lambda '{function_name}'.")

		except self._lambda_client.exceptions.ResourceConflictException:
			logger.info(f"Permission '{statement_id}' already exists for Lambda '{function_name}'.")

	def _log_lambda_paths_from_apigateway(self, lambda_name: str, api_id: str):
		"""
		Checks the API Gateway JSON for any paths integrated with the given Lambda,
		and logs the URL for each path.
		"""
		gateway_util = APIGatewayUtil(
			creds=self.creds,
			config_dir=self.config_dir,
			environment=self.environment,
			client_factory=self._client_factory,
		)
		gateway_content = gateway_util.gateway_config_file()

		endpoint_url = self._lambda_client.meta.endpoint_url
		region = self._lambda_client.meta.region_name if "localhost" not in endpoint_url else None

		paths = gateway_content.get("paths", {})
		for resource_path, methods in paths.items():
			for method_name, method_def in methods.items():
				integration = method_def.get("x-amazon-apigateway-integration", {})
				uri = integration.get("uri", "")
				if lambda_name in uri:
					if "localhost" in endpoint_url:
						url = f"{endpoint_url}/restapis/{api_id}/{self.environment}/_user_request_/{resource_path.lstrip('/')}"
					else:
						url = f"https://{api_id}.execute-api.{region}.amazonaws.com/{self.environment}/{resource_path}"

					logger.info(
						f"Lambda '{lambda_name}' is integrated with API path '{resource_path}' "
						f"({method_name.upper()}) -> URL: {url}"
					)
					return
		logger.info(
			f"Lambda '{lambda_name}' is not integrated with API --> Check apigateway.json file"
		)


@dataclass
class AWSLambdaParameters:
	function_name: str
	memory_size: int
	timeout_secs: int
	project_root: Path
	handler: str
	api_id: Optional[str]
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
	custom_lambda_builder: BaseLambdaZipBuilder = None

	def __post_init__(self, env_vars: Dict[str, str]):
		self._filtered_env_vars = {k: v for k, v in env_vars.items() if k in self.allowed_env_vars}

	@property
	def filtered_env_vars(self) -> Dict[str, str]:
		return self._filtered_env_vars
