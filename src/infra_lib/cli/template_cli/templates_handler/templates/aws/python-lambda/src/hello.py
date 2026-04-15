import json


def handler(event, context):
	print("hello world")
	return {"statusCode": 200, "body": json.dumps({"message": "hello world"})}
