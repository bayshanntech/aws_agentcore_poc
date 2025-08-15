import os
from dotenv import load_dotenv

try:
    load_dotenv()
    print("✅ .env file loaded successfully")
except Exception as e:
    print(f"⚠️ Could not load .env file: {e}")

class Config:
    # Claude API Configuration - for local development only
    # In production, use AgentCore outbound identity instead
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_PROFILE = os.getenv('AWS_PROFILE', 'default')
    
    # AgentCore Configuration
    AGENTCORE_OUTBOUND_IDENTITY_ARN = os.getenv('AGENTCORE_OUTBOUND_IDENTITY_ARN')
    
    # Runtime environment detection
    @classmethod
    def is_agentcore_runtime(cls):
        """Check if running in AgentCore runtime"""
        try:
            from bedrock_agentcore.runtime import RequestContext
            context = RequestContext.get_current()
            if context is not None:
                return True
        except ImportError:
            return False
        except Exception:
            pass
        
        return (
            os.getenv('AWS_EXECUTION_ENV') == 'AWS_ECS_FARGATE' or
            os.getenv('BEDROCK_AGENTCORE_RUNTIME') or
            'bedrock-agentcore' in str(os.getcwd()).lower() or
            'fargate' in str(os.getcwd()).lower() or
            '/opt/ml' in str(os.getcwd()) or
            os.path.exists('/opt/ml/code') or
            os.getenv('ECS_CONTAINER_METADATA_URI_V4') is not None or
            os.getenv('ECS_CONTAINER_METADATA_URI') is not None
        )
    
    @classmethod
    def validate(cls):
        """Validate required configuration (called at runtime, not initialization)"""
        if not cls.is_agentcore_runtime() and not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required for local development. Set it in .env file or environment.")
        return True