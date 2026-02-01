import os
import json
import sys
import io
from configparser import ConfigParser
from awscli.clidriver import create_clidriver
from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.tools import StructuredTool


class AwsCliInput(BaseModel):
    """Input schema for the awscli_executor tool."""
    user_id: str = Field(..., description="The profile name associated with the aws credentials")
    aws_cli_command: str = Field(..., description='AWS CLI command and args (e.g., ["s3", "ls"] or "s3 ls")')
    aws_access_key_id: Optional[str] = Field(None, description="AWS access key id associated with the credentials")
    aws_secret_access_key: Optional[str] = Field(None, description="AWS secret access key id associated with the credentials")
    default_region: Optional[str] = Field(None, description="AWS default region associated with the AWS credentials")


def awscli_executor(
        user_id: str,
        aws_cli_command: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        default_region: Optional[str] = None
) -> str:
    """
    Executes an AWS CLI command using awscli.clidriver with profile management.
        - user_id (str): profile name
        - aws_cli_command (list or str): AWS CLI command and args (e.g., ["s3", "ls"] or "s3 ls")
        - aws_access_key_id (optional)
        - aws_secret_access_key (optional)
        - default_region (optional)
    """
    try:
        profile = user_id
        if not profile:
            return "Error: 'user_id' is required"
        command = aws_cli_command
        if not command:
            return "Error: 'aws_cli_command' is required"
        if isinstance(command, str):
            args = command.split()
        elif isinstance(command, list):
            args = command
        else:
            return "Error: 'aws_cli_command' must be a string or list"

        # AWS credentials/config file paths
        creds_file = os.path.expanduser("~/.aws/credentials")
        config_file = os.path.expanduser("~/.aws/config")

        # Ensure ~/.aws directory exists
        aws_dir = os.path.dirname(creds_file)
        os.makedirs(aws_dir, exist_ok=True)

        # Load existing credentials and config
        creds = ConfigParser()
        creds.read(creds_file)
        conf = ConfigParser()
        conf.read(config_file)

        # If profile missing in credentials, create it
        if not creds.has_section(profile):
            if not aws_access_key_id or not aws_secret_access_key:
                return f"Error: profile '{profile}' not found and no AWS keys provided"
            creds[profile] = {
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key
            }
            if default_region:
                creds[profile]["region"] = default_region
            with open(creds_file, "w") as f:
                creds.write(f)

        # Determine the config section name
        section = "default" if profile == "default" else f"profile {profile}"
        # If profile missing in config, create it
        if not conf.has_section(section):
            conf[section] = {}
            if default_region:
                conf[section]["region"] = default_region
            with open(config_file, "w") as f:
                conf.write(f)

        # Export env vars for awscli
        os.environ["AWS_PROFILE"] = profile
        os.environ["AWS_SHARED_CREDENTIALS_FILE"] = creds_file
        os.environ["AWS_CONFIG_FILE"] = config_file
        if default_region:
            os.environ["AWS_DEFAULT_REGION"] = default_region

        # Execute AWS CLI command via awscli.clidriver
        driver = create_clidriver()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
        try:
            exit_code = driver.main(args)
            out = sys.stdout.getvalue()
            err = sys.stderr.getvalue()
        finally:
            sys.stdout, sys.stderr = old_out, old_err

        if exit_code != 0:
            return f"Error (exit code {exit_code}): {err.strip()}"
        return out.strip()

    except Exception as e:
        return f"Error executing AWS CLI command: {e}"


awscli_executor_tool = StructuredTool.from_function(
    name="awscli_executor",
    func=awscli_executor,
    description=(
        "Executes AWS CLI commands via awscli.clidriver for a specified profile. "
        "Input contain:\n"
        "- user_id (required): the AWS CLI profile name\n"
        "- aws_cli_command (required): the command as a list or space-delimited string\n"
        "- aws_access_key_id (optional): for creating the profile if it doesn't exist\n"
        "- aws_secret_access_key (optional): for creating the profile if it doesn't exist\n"
        "- default_region (optional): region to set for the profile\n\n"
        "If the profile is missing, credentials/config entries are created automatically, then the command runs."
    ),
    args_schema=AwsCliInput
)
