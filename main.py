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

if __name__ == '__main__':
    asyncio.run(main())

async def main():
    print("🚀 Starting Claude ADK Agent...")
    response = await process_prompt()
    print("\n📄 Agent Response:")
    print(response)


async def process_prompt(user_prompt: str = "Navigate to Duckduckgo and enter hello world, then summarise the content of the first result") -> str:
    try:
        claude_agent = ClaudeAPIAgent()
        response = await claude_agent.process_request(user_prompt)
        return response
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"}, indent=2)


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
    
    def _extract_json_from_response(self, response: str) -> dict:
        """Extract JSON from Claude's response, handling cases where there's additional text"""
        # First, try to parse the entire response as JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # If that fails, try to find JSON within the response
        import re
        
        # Look for JSON objects starting with { and ending with }
        json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
        
        for match in json_matches:
            try:
                # Try to parse each potential JSON match
                parsed = json.loads(match)
                # Validate it has the expected structure
                if isinstance(parsed, dict) and ('url' in parsed or 'actions' in parsed):
                    return parsed
            except json.JSONDecodeError:
                continue
        
        # If no valid JSON found, try a more sophisticated approach
        # Look for the first { and last } and extract everything between
        first_brace = response.find('{')
        last_brace = response.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
            json_candidate = response[first_brace:last_brace + 1]
            try:
                parsed = json.loads(json_candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"No valid JSON found in response: {response[:200]}...")


    async def process_request(self, user_prompt) -> str:
        try:
            # Step 1: Use Claude API to interpret the user's request and plan browser actions
            print("🔄 Using Claude API to interpret user request...")
            
            task_analysis_prompt = f"""You are a web automation planner. Analyze this user request and create a browser automation plan:

Request: "{user_prompt}"

Please respond with a JSON object containing:
1. "url": The starting URL to navigate to
2. "actions": A list of browser actions to perform
3. "data_to_extract": What information to extract from the final page

Available action types:
- navigate: Go to a URL
- search: Enter text in a search box and submit
- click: Click on an element
- scroll: Scroll the page
- extract_text: Get text content from elements
- extract_title: Get page title
- extract_first_result: Get first search result

Example response format:
{{
    "url": "https://duckduckgo.com",
    "actions": [
        {{"type": "search", "query": "hello world"}},
        {{"type": "click", "target": "first_result"}},
        {{"type": "extract_text", "target": "main_content"}}
    ],
    "data_to_extract": "content summary of the first search result"
}}

Create a plan for: "{user_prompt}"
"""
            
            plan_response = await self.call_claude_api(task_analysis_prompt)
            
            try:
                # Try to extract JSON from the response
                browser_plan = self._extract_json_from_response(plan_response)
            except (json.JSONDecodeError, ValueError) as e:
                return json.dumps({
                    "error": "Failed to parse browser automation plan",
                    "raw_response": plan_response,
                    "parse_error": str(e),
                    "status": "failed"
                }, indent=2)
            
            # Step 2: Execute the browser automation plan
            print("🔄 Delegating to Playwright Agent for task execution...")
            
            browser_actions = json.dumps({
                "type": "general_automation",
                "url": browser_plan.get("url", "https://www.google.com"),
                "actions": browser_plan.get("actions", []),
                "extract": browser_plan.get("data_to_extract", "page content")
            })
            
            # Call the Playwright browser tool
            browser_result = await playwright_browser_tool(browser_plan.get("url", "https://www.google.com"), browser_actions)
            browser_data = json.loads(browser_result)
            
            if browser_data.get("status") != "success":
                return json.dumps({
                    "error": "Playwright Agent failed to execute task",
                    "browser_error": browser_data.get("error", "Unknown error"),
                    "status": "failed"
                }, indent=2)
            
            # Step 3: Use Claude API to analyze and summarize the results
            print("🔄 Using Claude API to analyze browser results...")
            
            extracted_data = browser_data.get("result", {})
            
            summary_prompt = f"""Based on this browser automation task, please provide a helpful summary:

Original Request: "{user_prompt}"

Browser Results:
{json.dumps(extracted_data, indent=2)}

Please provide a clear, helpful summary of what was accomplished and the key information found."""
            
            claude_analysis = await self.call_claude_api(summary_prompt)
            
            return json.dumps({
                "workflow": "intelligent_browser_automation",
                "original_request": user_prompt,
                "browser_plan": browser_plan,
                "browser_results": extracted_data,
                "claude_analysis": claude_analysis,
                "final_response": f"Task completed! {claude_analysis}",
                "model": "claude-3-5-sonnet-20241022",
                "status": "success"
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "workflow": "multi_agent_delegation",
                "error": str(e),
                "status": "failed"
            }, indent=2)


