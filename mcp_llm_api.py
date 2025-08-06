# mcp_llm_api.py
import json
from mcp_workflow.load_defect_embeddings import test_llm_manifest_mapping
from mcp_llm_handler import process_llm_states

def process_user_comment(user_comment: str, confirmation="YES") -> dict:
    try:
        # Step 1: Get LLM interpretation of the comment
        llm_response = test_llm_manifest_mapping(user_comment)

        if isinstance(llm_response, str):
            llm_response = json.loads(llm_response)

        # Step 2: Process through MCP engine
        result = process_llm_states(llm_response, confirmation)
        return {
            "status": "success",
            "llm_output": llm_response,
            "result": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
