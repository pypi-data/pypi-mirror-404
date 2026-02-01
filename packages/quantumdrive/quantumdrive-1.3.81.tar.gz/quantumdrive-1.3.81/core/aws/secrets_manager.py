import boto3
import json
from botocore.exceptions import ClientError
import os
import logging

logger = logging.getLogger(__name__)


class SecretsManager:
    def __init__(self, secret_name, region_name="us-east-1"):
        """
        Initialize the SecretsManager class to access a specific secret.

        :param secret_name: The name of the secret in AWS Secrets Manager.
        :param region_name: The AWS region where the secret is stored. Default is 'us-east-1'.
        """
        self.secret_name = secret_name
        self.region_name = region_name
        self.client = boto3.client('secretsmanager', region_name=self.region_name)

    def get_secret(self):
        """
        Retrieve the secret from AWS Secrets Manager.

        :return: The secret as a dictionary or None if an error occurred.
        """
        try:
            # Fetch the secret value from Secrets Manager
            response = self.client.get_secret_value(SecretId=self.secret_name)

            # Secrets Manager returns the secret in the 'SecretString' field or 'SecretBinary'
            if 'SecretString' in response:
                secret = response['SecretString']
            else:
                # If it's stored as binary, decode it (you can adjust based on your use case)
                secret = response['SecretBinary']

            # Return the secret in a parsed format (usually a JSON string)
            return json.loads(secret)

        except ClientError as e:
            # Avoid noisy prints; log at warning level and return None gracefully
            logger.warning("Error fetching secret '%s': %s", self.secret_name, e)
            return None

    def get_db_credentials(self):
        """
        Retrieve database credentials stored in Secrets Manager and return them.

        :return: A dictionary containing DB credentials (username, password, host, etc.)
        """
        secret = self.get_secret()
        if secret:
            # Assuming your secret contains these fields
            db_credentials = {
                "username": secret.get("username"),
                "password": secret.get("password"),
                "host": secret.get("host"),
                "port": secret.get("port"),
                "dbname": secret.get("dbname"),
            }
            return db_credentials
        return None

    def get_aws_credentials(self):
        """
        Retrieve AWS credentials stored in Secrets Manager and return them.

        :return: A dictionary containing AWS credentials (access key and secret key).
        """
        secret = self.get_secret()
        if secret:
            # Assuming your secret contains AWS credentials
            aws_credentials = {
                "AWS_ACCESS_KEY_ID": secret.get("AWS_ACCESS_KEY_ID"),
                "AWS_SECRET_ACCESS_KEY": secret.get("AWS_SECRET_ACCESS_KEY"),
                # Optional session token if using temporary creds
                "AWS_SESSION_TOKEN": secret.get("AWS_SESSION_TOKEN"),
                "AWS_REGION": secret.get("AWS_REGION", "us-east-1"),  # Default to 'us-east-1' if not provided
                # Optional S3-specific settings
                "AWS_S3_BUCKET": secret.get("AWS_S3_BUCKET"),
                "AWS_S3_SSE": secret.get("AWS_S3_SSE"),  # e.g., 'AES256' or 'aws:kms'
                "AWS_S3_KMS_KEY_ID": secret.get("AWS_S3_KMS_KEY_ID"),
            }
            return aws_credentials
        return None

    def store_secret(self, secret_value):
        """
        Store or update a secret in AWS Secrets Manager.

        :param secret_value: The value of the secret (should be a dictionary).
        :return: True if the secret is successfully stored, False otherwise.
        """
        try:
            # Store the secret in Secrets Manager
            response = self.client.update_secret(
                SecretId=self.secret_name,
                SecretString=json.dumps(secret_value)
            )
            return response['ARN'] is not None
        except ClientError as e:
            print(f"Error storing secret: {e}")
            return False


# Example usage:
if __name__ == "__main__":
    # Example: Fetch and print DB credentials stored in Secrets Manager
    secret_name = "aws/rds/quantifydb"  # noqa Replace with your secret name
    secrets_manager = SecretsManager(secret_name)

    db_credentials = secrets_manager.get_db_credentials()
    if db_credentials:
        print("Database Credentials:")
        print(f"Username: {db_credentials['username']}")
        print(f"Password: {db_credentials['password']}")
        print(f"Host: {db_credentials['host']}")
        print(f"Port: {db_credentials['port']}")
        print(f"Database Name: {db_credentials['dbname']}")
    else:
        print("Failed to retrieve database credentials.")

    # Example: Fetch AWS credentials stored in Secrets Manager
    aws_credentials = secrets_manager.get_aws_credentials()
    if aws_credentials:
        print("AWS Credentials:")
        print(f"AWS Access Key ID: {aws_credentials['AWS_ACCESS_KEY_ID']}")
        print(f"AWS Secret Access Key: {aws_credentials['AWS_SECRET_ACCESS_KEY']}")
        print(f"AWS Region: {aws_credentials['AWS_REGION']}")
    else:
        print("Failed to retrieve AWS credentials.")
