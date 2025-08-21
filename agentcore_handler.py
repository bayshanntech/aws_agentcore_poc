#!/usr/bin/env python3

import json
import asyncio
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from main import process_prompt

# Create the AgentCore app
app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):

    try:
        # Extract prompt from payload
        user_prompt = "hello world"  # default fallback
        if payload and isinstance(payload, dict):
            user_prompt = payload.get("prompt", "hello world")
        elif payload and isinstance(payload, str):
            try:
                parsed_payload = json.loads(payload)
                user_prompt = parsed_payload.get("prompt", "hello world")
            except:
                user_prompt = payload  # use raw string if not JSON
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(process_prompt(user_prompt))
        loop.close()
        
        response_data = json.loads(response)
        
        # Handle both old and new response formats
        if "final_response" in response_data:
            # New multi-agent workflow format
            return response_data["final_response"]
        elif "agent_response" in response_data:
            # Legacy format
            return response_data["agent_response"]
        else:
            # Fallback: return the whole response
            return response
        
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run()