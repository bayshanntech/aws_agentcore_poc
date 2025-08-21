#!/usr/bin/env python3
"""
API Key Retriever - Handles secure credential retrieval from multiple sources
Supports AgentCore outbound identity, AWS Secrets Manager, and environment variables
"""

import json
import boto3
from config import Config


class APIKeyRetriever:
    """Handles secure API key retrieval from multiple sources with priority fallback"""
    
    def get_api_key(self) -> str:
        """Get API key using priority fallback chain"""
        # Priority 1: Try AgentCore outbound identity
        try:
            return self._get_api_key_via_agentcore_outbound_identity()
        except Exception as e:
            print(f"AgentCore outbound identity failed: {e}")
        
        # Priority 2: Try AWS Secrets Manager
        try:
            return self._get_api_key_via_aws_secrets_manager()
        except Exception as e:
            print(f"Secrets Manager failed: {e}")
        
        # Priority 3: Try environment variable
        try:
            return self._get_api_key_via_environment_variable()
        except Exception as e:
            print(f"Environment variable failed: {e}")
        
        # If all methods fail
        raise ValueError("No API key available. Configure one of: AgentCore outbound identity, Secrets Manager, or ANTHROPIC_API_KEY environment variable.")
    
    def _get_api_key_via_agentcore_outbound_identity(self) -> str:
        """Priority 1: Try to get API key from AgentCore outbound identity"""
        if not Config.AGENTCORE_OUTBOUND_IDENTITY_ARN:
            raise ValueError("AgentCore outbound identity ARN not configured")
        
        try:
            from bedrock_agentcore.runtime import RequestContext
        except ImportError:
            raise ValueError("bedrock_agentcore not available - not in AgentCore runtime")
        
        print("Trying AgentCore outbound identity...")
        context = RequestContext.get_current()
        
        if not context or not hasattr(context, 'identity'):
            raise ValueError("No AgentCore context or identity available")
        
        credential_response = context.identity.get_credential(
            Config.AGENTCORE_OUTBOUND_IDENTITY_ARN
        )
        
        if not credential_response:
            raise ValueError("No credential response from AgentCore outbound identity")
        
        # Extract credential from various response formats
        # Try common key names
        for key in ['token', 'credential', 'api_key', 'value', 'secret']:
            if key in credential_response:
                print(f"Got API key from AgentCore outbound identity using key '{key}'")
                return credential_response[key]

        # Try direct string response
        if isinstance(credential_response, str):
            print("Got API key from AgentCore outbound identity (string response)")
            return credential_response

        # Try first value if it has values
        if hasattr(credential_response, 'values'):
            values = list(credential_response.values())
            if values:
                print("Got API key from AgentCore outbound identity (first value)")
                return values[0]

        raise ValueError("Could not extract credential from AgentCore outbound identity response")

    def _get_api_key_via_aws_secrets_manager(self) -> str:
        """Priority 2: Try to get API key from AWS Secrets Manager"""
        print("Trying AWS Secrets Manager...")

        secrets_client = boto3.client('secretsmanager', region_name=Config.AWS_REGION)
        response = secrets_client.get_secret_value(SecretId=Config.SECRETS_MANAGER_SECRET_ARN)
        secret_string = response['SecretString']

        # Try to parse as JSON first
        try:
            secret_data = json.loads(secret_string)
            # Extract API key from JSON secret data
            # Try common JSON keys for API keys
            for key in ['api_key_value', 'api_key', 'key', 'value', 'token']:
                if key in secret_data:
                    print(f"Got API key from AWS Secrets Manager (JSON key: {key})")
                    return secret_data[key]
            
            # If JSON but no recognized key, return the first value
            if isinstance(secret_data, dict):
                values = list(secret_data.values())
                if values:
                    print("Got API key from AWS Secrets Manager (first JSON value)")
                    return values[0]
            
            raise ValueError("Could not extract API key from AWS Secrets Manager JSON data")
        except json.JSONDecodeError:
            # Not JSON, use as plain string
            print("Got API key from AWS Secrets Manager (plain string)")
            return secret_string.strip()

    def _get_api_key_via_environment_variable(self) -> str:
        """Priority 3: Try to get API key from environment variable"""
        if not Config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        print("Using environment variable ANTHROPIC_API_KEY")
        return Config.ANTHROPIC_API_KEY