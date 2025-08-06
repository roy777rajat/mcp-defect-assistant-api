from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from mcp_llm_api import process_user_comment

app = FastAPI(title="MCP Defect Assistant API", version="1.0")

class CommentInput(BaseModel):
    comment: str
    confirm: Optional[str] = "YES"

@app.post("/api/mcp")
async def handle_mcp_request(data: CommentInput):
    return process_user_comment(data.comment, data.confirm)


# mcp_server_memory.py
# from fastapi import FastAPI, Request
# from pydantic import BaseModel
# from typing import Optional, Dict, Any
# import json
# import uuid

# from mcp_workflow.load_defect_embeddings import test_llm_manifest_mapping
# from mcp_llm_handler import process_llm_states

# app = FastAPI(title="MCP Defect Assistant API with Memory", version="1.1")

# # Simple in-memory store for demonstration (replace with Redis/db in production)
# user_state_cache: Dict[str, Dict[str, Any]] = {}

# class CommentInput(BaseModel):
#     user_id: str  # User identifier (for session tracking)
#     comment: Optional[str] = None
#     confirm: Optional[str] = None
#     missing_fields: Optional[Dict[str, str]] = None  # Optional input patch


# def check_missing_fields(parsed_output: Dict) -> Dict[str, list]:
#     missing = {}
#     for step in parsed_output.get("States", []):
#         step_name = step.get("Step Name")
#         for field, value in step.get("Required Fields", {}).items():
#             if value.strip().lower() == "not provided":
#                 missing.setdefault(step_name, []).append(field)
#     return missing


# def merge_missing_fields(parsed_output: Dict, field_patch: Dict[str, str]) -> Dict:
#     for step in parsed_output.get("States", []):
#         for field in step.get("Required Fields", {}):
#             if step["Required Fields"][field].strip().lower() == "not provided" and field in field_patch:
#                 step["Required Fields"][field] = field_patch[field]
#     return parsed_output


# @app.post("/api/mcp")
# async def handle_mcp_request(data: CommentInput):
#     user_id = data.user_id

#     # Branch 1: New Comment Input
#     if data.comment:
#         parsed_output = test_llm_manifest_mapping(data.comment)
#         if isinstance(parsed_output, str):
#             parsed_output = json.loads(parsed_output)

#         missing = check_missing_fields(parsed_output)
#         user_state_cache[user_id] = {
#             "parsed_output": parsed_output,
#             "pending_fields": missing
#         }

#         if missing:
#             return {
#                 "status": "waiting_for_input",
#                 "missing_fields": missing,
#                 "message": "Please provide the missing field(s)."
#             }

#         if data.confirm and data.confirm.upper() == "YES":
#             result = process_llm_states(parsed_output, "YES")
#             return {"status": "success", "result": result}
#         else:
#             return {"status": "awaiting_confirmation", "message": "Confirm to proceed (YES/NO)."}

#     # Branch 2: Missing Field Input Patch
#     elif data.missing_fields:
#         if user_id not in user_state_cache:
#             return {"status": "error", "message": "No prior session found."}

#         cached = user_state_cache[user_id]
#         patched = merge_missing_fields(cached["parsed_output"], data.missing_fields)
#         missing = check_missing_fields(patched)

#         cached["parsed_output"] = patched
#         cached["pending_fields"] = missing

#         if missing:
#             return {
#                 "status": "waiting_for_more_input",
#                 "missing_fields": missing,
#                 "message": "Still missing some fields."
#             }

#         # All fields filled, wait for confirmation
#         return {"status": "awaiting_confirmation", "message": "Confirm to proceed (YES/NO)."}

#     # Branch 3: Confirmation to Execute
#     elif data.confirm and data.confirm.upper() == "YES":
#         if user_id not in user_state_cache:
#             return {"status": "error", "message": "No parsed state available to confirm."}

#         cached = user_state_cache[user_id]
#         result = process_llm_states(cached["parsed_output"], "YES")
#         del user_state_cache[user_id]  # Clear session
#         return {"status": "success", "result": result}

#     return {"status": "error", "message": "Invalid input sequence."}
