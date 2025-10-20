from enum import StrEnum


class AwsService(StrEnum):
	APIGateway = "apigateway"
	SQS = "sqs"
	LAMBDA = "lambda"
	S3 = "s3"
	SECRETS_MANAGER = "secretsmanager"
	CLOUD_FORMATION = "cloudformation"
	STS = "sts"
