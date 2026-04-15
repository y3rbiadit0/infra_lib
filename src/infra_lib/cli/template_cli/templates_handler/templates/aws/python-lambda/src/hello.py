import json


def handler(_event, _context):
	print("hello world")
	return {"statusCode": 200, "body": json.dumps({"message": "hello world"})}
