#!/usr/bin/env python3
"""
Simple Hello World ADK Agent using Claude API
Runs both locally and in AWS Bedrock AgentCore
"""

import asyncio
import json
import os
import boto3
from anthropic import Anthropic
from config import Config
from google.adk.agents import Agent
from playwright_agent import playwright_browser_tool

class ClaudeAPIAgent:
    """ADK Agent that uses Claude API instead of AWS hosted models"""
    
    def __init__(self):
        # Don't validate or get API key immediately - do it lazily
        self.api_key = None
        self.anthropic_client = None
    
    def _get_api_key(self) -> str:
        """Get API key from multiple sources in priority order"""
        
        # Priority 1: Try AgentCore outbound identity (if available and in AgentCore runtime)
        if Config.AGENTCORE_OUTBOUND_IDENTITY_ARN:
            try:
                from bedrock_agentcore.runtime import RequestContext
                context = RequestContext.get_current()
                
                if context and hasattr(context, 'identity'):
                    print("🔄 Trying AgentCore outbound identity...")
                    credential_response = context.identity.get_credential(
                        Config.AGENTCORE_OUTBOUND_IDENTITY_ARN
                    )
                    
                    if credential_response:
                        for key in ['token', 'credential', 'api_key', 'value', 'secret']:
                            if key in credential_response:
                                print(f"✅ Got API key from AgentCore outbound identity using key '{key}'")
                                return credential_response[key]
                        
                        if isinstance(credential_response, str):
                            print("✅ Got API key from AgentCore outbound identity (string response)")
                            return credential_response
                        if hasattr(credential_response, 'values'):
                            values = list(credential_response.values())
                            if values:
                                print("✅ Got API key from AgentCore outbound identity (first value)")
                                return values[0]
                                
            except ImportError:
                print("📝 bedrock_agentcore not available - trying other methods")
            except Exception as e:
                print(f"⚠️ AgentCore outbound identity error: {e}")
        
        # Priority 2: Try AWS Secrets Manager
        try:
            print("🔄 Trying AWS Secrets Manager...")
            secrets_client = boto3.client('secretsmanager', region_name=Config.AWS_REGION)
            response = secrets_client.get_secret_value(SecretId=Config.SECRETS_MANAGER_SECRET_ARN)
            secret_string = response['SecretString']
            
            # Secret might be JSON format or plain string
            try:
                import json as json_module
                secret_data = json_module.loads(secret_string)
                # Try common JSON keys for API keys
                for key in ['api_key_value', 'api_key', 'key', 'value', 'token']:
                    if key in secret_data:
                        print(f"✅ Got API key from AWS Secrets Manager (JSON key: {key})")
                        return secret_data[key]
                # If JSON but no recognized key, return the first value
                if isinstance(secret_data, dict):
                    values = list(secret_data.values())
                    if values:
                        print("✅ Got API key from AWS Secrets Manager (first JSON value)")
                        return values[0]
            except json_module.JSONDecodeError:
                # Not JSON, use as plain string
                print("✅ Got API key from AWS Secrets Manager (plain string)")
                return secret_string.strip()
                
            raise ValueError("Could not extract API key from secret")
        except Exception as e:
            print(f"⚠️ Secrets Manager error: {e}")
        
        # Priority 3: Environment variable (local development)
        if Config.ANTHROPIC_API_KEY:
            print("✅ Using environment variable ANTHROPIC_API_KEY")
            return Config.ANTHROPIC_API_KEY
            
        # If we get here, we have no API key available
        raise ValueError("No API key available. Configure one of: AgentCore outbound identity, Secrets Manager, or ANTHROPIC_API_KEY environment variable.")
    
    async def call_claude_api(self, prompt: str) -> str:
        """Call Claude API with the given prompt"""
        try:
            if self.anthropic_client is None:
                self.api_key = self._get_api_key()
                self.anthropic_client = Anthropic(api_key=self.api_key)
            
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return f"Error calling Claude API: {str(e)}"
    
    async def process_request(self) -> str:
        try:
            # Step 1: Use Playwright Agent to search Google
            print("🔄 Delegating to Playwright Agent for Google search...")
            
            # Prepare browser automation actions
            search_actions = json.dumps({
                "type": "google_search",
                "query": "hello world"
            })
            
            # Call the Playwright browser tool
            browser_result = await playwright_browser_tool("https://www.google.com", search_actions)
            browser_data = json.loads(browser_result)
            
            if browser_data.get("status") != "success":
                return json.dumps({
                    "error": "Playwright Agent failed to get search results",
                    "browser_error": browser_data.get("error", "Unknown error"),
                    "status": "failed"
                }, indent=2)
            
            # Extract the first result title from browser automation
            first_result_title = browser_data.get("result", {}).get("first_result_title", "No title found")
            
            # Step 2: Use Claude API to analyze the search result
            print("🔄 Using Claude API to analyze search result...")
            
            claude_prompt = f"""I searched Google for "hello world" and got this as the first result title:
            "{first_result_title}"
            
            Please provide a brief, friendly analysis of this search result. What does this title suggest about the search?"""
            
            claude_response = await self.call_claude_api(claude_prompt)
            
            return json.dumps({
                "workflow": "multi_agent_delegation",
                "playwright_agent_result": {
                    "search_query": "hello world",
                    "first_result_title": first_result_title,
                    "status": "success"
                },
                "claude_agent_analysis": claude_response,
                "final_response": f"Search completed! The first Google result for 'hello world' was: '{first_result_title}'. {claude_response}",
                "model": "claude-3-5-sonnet-20241022",
                "status": "success"
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "workflow": "multi_agent_delegation",
                "error": str(e),
                "status": "failed"
            }, indent=2)

async def say_hello() -> str:
    try:
        claude_agent = ClaudeAPIAgent()
        response = await claude_agent.process_request()
        return response
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"}, indent=2)

def create_agent() -> Agent:

    agent = Agent(
        name="claude-hello-world",
        model="gemini-2.0-flash",  # This won't actually be used since we override with Claude
        description="Simple hello world agent using Claude API",
        instruction="You are a helpful agent that says hello using Claude API",
        tools=[say_hello]
    )
    
    return agent

async def main():
    print("🚀 Starting Claude Hello World ADK Agent...")
    response = await say_hello()
    print("\n📄 Agent Response:")
    print(response)

if __name__ == '__main__':
    asyncio.run(main())
