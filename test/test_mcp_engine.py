from mcp_engine import MCPWorkflow

def test_generate_review_prompt():
    mcp = MCPWorkflow()
    mcp.start("review_defect", initial_context={
        "defect_id": "D-123",
        "title": "Crash on Save",
        "description": "App crashes when clicking Save"
    })

    mcp.enrich_context_with_similarity("App crashes when clicking Save")
    prompt = mcp.generate_prompt()

    print("🧪 Prompt:\n", prompt)
    assert "App crashes" in prompt
    assert "similar defects" in prompt.lower() or "suggest" in prompt.lower()

if __name__ == "__main__":
    test_generate_review_prompt()

