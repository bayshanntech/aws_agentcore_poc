#!/usr/bin/env python3

import json
import asyncio
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from main import say_hello

# Create the AgentCore app
app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(say_hello())
        loop.close()
        
        response_data = json.loads(response)
        
        return response_data["agent_response"]
        
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run()