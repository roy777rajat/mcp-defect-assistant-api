import boto3
import json
import os

def get_aws_secret(secret_name, region_name="eu-west-1"):
    """
    Retrieve a JSON-formatted secret from AWS Secrets Manager.
    """
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response.get('SecretString')
        return json.loads(secret_string)
    except Exception as e:
        print(f"Error fetching secret {secret_name}: {e}")
        return None
