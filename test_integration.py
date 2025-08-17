#!/usr/bin/env python3
"""
Integration tests for the multi-agent system
Tests the complete workflow: Main Agent -> Playwright Agent -> Claude Analysis
"""

import asyncio
import json
import pytest
from main import say_hello, ClaudeAPIAgent
from playwright_agent import playwright_browser_tool


class TestIntegration:
    """Integration tests for multi-agent workflow"""
    
    @pytest.mark.asyncio
    async def test_full_multi_agent_workflow(self):
        """Test the complete multi-agent delegation workflow"""
        
        # Run the full workflow
        result = await say_hello()
        
        # Parse the JSON response
        response_data = json.loads(result)
        
        # Verify no errors occurred
        assert response_data.get("status") == "success", f"Expected success status, got: {response_data.get('status')}"
        assert "error" not in response_data, f"Unexpected error in response: {response_data.get('error')}"
        
        # Verify multi-agent workflow structure
        assert response_data.get("workflow") == "multi_agent_delegation", "Expected multi-agent delegation workflow"
        
        # Verify Playwright Agent results
        playwright_result = response_data.get("playwright_agent_result", {})
        assert playwright_result.get("status") == "success", "Playwright Agent should succeed"
        assert "first_result_title" in playwright_result, "Should have first result title from Google search"
        assert playwright_result.get("search_query") == "hello world", "Should search for 'hello world'"
        
        # Verify Claude analysis
        assert "claude_agent_analysis" in response_data, "Should have Claude's analysis of the search result"
        claude_analysis = response_data.get("claude_agent_analysis")
        assert isinstance(claude_analysis, str), "Claude analysis should be a string"
        assert len(claude_analysis) > 0, "Claude analysis should not be empty"
        
        # Verify final response
        final_response = response_data.get("final_response")
        assert isinstance(final_response, str), "Final response should be a string"
        assert "hello world" in final_response.lower(), "Final response should mention the search query"
        
        print(f"✅ Integration test passed! Final response: {final_response[:100]}...")
    
    @pytest.mark.asyncio
    async def test_playwright_browser_tool_directly(self):
        """Test the Playwright browser tool directly"""
        
        # Test Google search action
        search_actions = json.dumps({
            "type": "google_search",
            "query": "hello world"
        })
        
        result = await playwright_browser_tool("https://www.google.com", search_actions)
        response_data = json.loads(result)
        
        # Verify success
        assert response_data.get("status") == "success", f"Expected success, got: {response_data}"
        assert response_data.get("url") == "https://www.google.com", "Should navigate to Google"
        assert response_data.get("action_type") == "google_search", "Should perform google_search action"
        
        # Verify search results
        search_result = response_data.get("result", {})
        assert "first_result_title" in search_result, "Should have first result title"
        assert search_result.get("search_query") == "hello world", "Should search for 'hello world'"
        
        print(f"✅ Playwright tool test passed! First result: {search_result.get('first_result_title')}")
    
    @pytest.mark.asyncio
    async def test_claude_api_agent_directly(self):
        """Test the Claude API agent directly"""
        
        claude_agent = ClaudeAPIAgent()
        
        # Test a simple prompt
        response = await claude_agent.call_claude_api("Please say hello in exactly 5 words.")
        
        # Verify response
        assert isinstance(response, str), "Response should be a string"
        assert len(response) > 0, "Response should not be empty"
        assert not response.startswith("Error calling Claude API"), f"Should not have API error: {response}"
        
        print(f"✅ Claude API test passed! Response: {response}")
        
    @pytest.mark.asyncio  
    async def test_generic_browser_actions(self):
        """Test generic browser actions (fill_form, extract_text, click)"""
        
        # Test form filling action
        fill_actions = json.dumps({
            "type": "fill_form",
            "selector": "textarea[name='q'], input[name='q']",
            "text": "test query",
            "submit": False
        })
        
        result = await playwright_browser_tool("https://www.google.com", fill_actions)
        response_data = json.loads(result)
        
        # Verify form filling worked
        assert response_data.get("status") == "success", f"Form filling failed: {response_data}"
        assert response_data.get("action_type") == "fill_form", "Should be fill_form action"
        
        form_result = response_data.get("result", {})
        assert form_result.get("action") == "fill_form", "Result should indicate fill_form"
        assert form_result.get("text") == "test query", "Should have filled with test query"
        
        print("✅ Generic browser actions test passed!")


def test_json_response_format():
    """Test that our responses are valid JSON (synchronous test)"""
    
    # This is a simple JSON validation test
    sample_response = {
        "workflow": "multi_agent_delegation",
        "playwright_agent_result": {
            "search_query": "hello world",
            "first_result_title": "Sample Title",
            "status": "success"
        },
        "claude_agent_analysis": "This looks like a programming tutorial.",
        "final_response": "Search completed! The first Google result for 'hello world' was: 'Sample Title'.",
        "model": "claude-3-5-sonnet-20241022",
        "status": "success"
    }
    
    # Verify JSON serialization works
    json_string = json.dumps(sample_response, indent=2)
    parsed_back = json.loads(json_string)
    
    assert parsed_back == sample_response, "JSON serialization should be reversible"
    assert parsed_back.get("status") == "success", "Should maintain success status"
    
    print("✅ JSON format test passed!")


if __name__ == "__main__":
    # Allow running tests directly
    asyncio.run(TestIntegration().test_full_multi_agent_workflow())