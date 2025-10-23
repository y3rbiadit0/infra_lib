import pytest
from unittest.mock import MagicMock
from pathlib import Path

from infra_lib.infra.aws_infra.lambda_util import LambdaUtil, AWSLambdaParameters


@pytest.fixture
def mock_lambda_client():
    return MagicMock()


@pytest.fixture
def mock_sts_util():
    sts = MagicMock()
    sts.get_account_id = MagicMock(return_value="123456789012")
    return sts


@pytest.fixture
def lambda_util(tmp_path, mock_lambda_client, mock_sts_util):
    util = LambdaUtil(
        creds=MagicMock(),
        environment=MagicMock(),
        infrastructure_dir=tmp_path,
        client_factory=MagicMock(),
        config_dir=tmp_path,
    )
    # Inject mocks
    util._lambda_client = mock_lambda_client
    util._sts_util = mock_sts_util
    util._build_lambda = MagicMock(return_value=str(tmp_path / "lambda.zip"))
    util._create_lambda = MagicMock()
    util._add_lambda_permission_for_apigateway = MagicMock()
    util._log_lambda_paths_from_apigateway = MagicMock()
    return util


@pytest.fixture
def sample_lambda_params(tmp_path):
    return AWSLambdaParameters(
        function_name="my-lambda",
        memory_size=128,
        timeout_secs=30,
        project_root=tmp_path,
        handler="handler.main",
        api_id=None,
        environment=MagicMock(),
        runtime="python3.9",
        env_vars={"TARGET_ENV": "dev", "AWS_ACCESS_KEY_ID": "test"},
    )


def test_add_lambda_creates_function(lambda_util, sample_lambda_params):
    lambda_util.add_lambda(sample_lambda_params)

    lambda_util._create_lambda.assert_called_once()
    lambda_util._add_lambda_permission_for_apigateway.assert_called_once()
    lambda_util._log_lambda_paths_from_apigateway.assert_called_once()
