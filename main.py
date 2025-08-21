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
from api_key_retriever import APIKeyRetriever

if __name__ == '__main__':
    asyncio.run(main())

async def main():
    print("🚀 Starting Claude ADK Agent...")
    response = await process_prompt()
    print("\n📄 Agent Response:")
    print(response)


async def process_prompt(user_prompt: str = "Navigate to Duckduckgo and enter hello world, then summarise the content of the first result") -> str:
    try:
        return await ClaudeAPIAgent().process_user_prompt(user_prompt)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"}, indent=2)


class ClaudeAPIAgent:

    def __init__(self):
        self.api_key = None
        self.anthropic_client = None
        self.api_key_retriever = APIKeyRetriever()


    async def process_user_prompt(self, user_prompt: str) -> str:
        try:
            browser_plan = await self._plan_browser_automation_task(user_prompt)
            extracted_data = await self._execute_browser_automation(browser_plan)
            claude_analysis = await self._analyze_browser_results(user_prompt, extracted_data)
            return await self._build_response_json(browser_plan, claude_analysis, extracted_data, user_prompt)
        except Exception as e:
            return await self._build_error_json(e)


    async def _build_error_json(self, e):
        return json.dumps({
            "workflow": "intelligent_browser_automation",
            "error": str(e),
            "status": "failed"
        }, indent=2)


    async def _build_response_json(self, browser_plan, claude_analysis, extracted_data, user_prompt):
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
    

    async def _plan_browser_automation_task(self, user_prompt: str) -> dict:
        """Step 1: Use Claude to analyze user request and create browser automation plan"""
        print("Using Claude API to interpret user request...")
        
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
            return self._parse_claude_response(plan_response)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to parse browser automation plan: {str(e)}. Raw response: {plan_response}")


    async def call_claude_api(self, prompt: str) -> str:
        try:
            if self.anthropic_client is None:
                self.api_key = self.api_key_retriever.get_api_key()
                self.anthropic_client = Anthropic(api_key=self.api_key)

            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return f"Error calling Claude API: {str(e)}"


    def _parse_claude_response(self, response: str) -> dict:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        import re
        json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)

        for match in json_matches:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, dict) and ('url' in parsed or 'actions' in parsed):
                    return parsed
            except json.JSONDecodeError:
                continue

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

    
    async def _execute_browser_automation(self, browser_plan: dict) -> dict:

        browser_actions = json.dumps({
            "type": "general_automation",
            "url": browser_plan.get("url", "https://www.google.com"),
            "actions": browser_plan.get("actions", []),
            "extract": browser_plan.get("data_to_extract", "page content")
        })
        
        browser_result = await playwright_browser_tool(browser_plan.get("url", "https://www.google.com"), browser_actions)
        browser_data = json.loads(browser_result)
        
        if browser_data.get("status") != "success":
            raise RuntimeError(f"Playwright Agent failed to execute task: {browser_data.get('error', 'Unknown error')}")
        
        return browser_data.get("result", {})


    async def _analyze_browser_results(self, user_prompt: str, extracted_data: dict) -> str:
        print("Using Claude API to analyze browser results...")
        
        summary_prompt = f"""Based on this browser automation task, please provide a helpful summary:

Original Request: "{user_prompt}"

Browser Results:
{json.dumps(extracted_data, indent=2)}

Please provide a clear, helpful summary of what was accomplished and the key information found."""
        
        claude_analysis = await self.call_claude_api(summary_prompt)
        return claude_analysis
    

