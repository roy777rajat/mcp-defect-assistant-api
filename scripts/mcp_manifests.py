import os

mcp_manifests = {
    "create_defect.mcp.yml": """
step: create_defect
actor: reporter
intent: "Create a new defect record"
context:
  defect_id: null
  title: null
  description: null
  created_by: null
  tags: []
  status: "New"
input_required:
  - title
  - description
  - created_by
allowed_next_steps:
  - review_defect
llm_prompt_template: |
  You are a defect management assistant helping a reporter to create a defect.

  Please gather these details:
  - Title: {{ context.title }}
  - Description: {{ context.description }}
  - Reporter name: {{ context.created_by }}

  After collecting, confirm the details and proceed to review.
""",

    "review_defect.mcp.yml": """
step: review_defect
actor: engineer
intent: "Review defect details and find similar defects"
context:
  defect_id: null
  title: null
  description: null
  status: "New"
  assigned_to: null
  tags: []
  comments: []
input_required:
  - defect_id
  - review_comments
allowed_next_steps:
  - assign_defect
  - close_defect
llm_prompt_template: |
  You are assisting an engineer reviewing defect {{ context.defect_id }}.

  Title: {{ context.title }}
  Description: {{ context.description }}
  Current status: {{ context.status }}
  Tags: {{ context.tags }}

  Use the defect description to find similar defects and suggest related fixes.

  Please provide review comments and suggest next steps: {{ allowed_next_steps }}.
""",

    "assign_defect.mcp.yml": """
step: assign_defect
actor: manager
intent: "Assign defect to engineer"
context:
  defect_id: null
  assigned_to: null
input_required:
  - defect_id
  - engineer_name
allowed_next_steps:
  - update_status
  - add_comment
llm_prompt_template: |
  You are helping a manager assign defect {{ context.defect_id }}.

  Current assigned engineer: {{ context.assigned_to }}

  Please provide engineer name to assign the defect.

  Suggested next steps: {{ allowed_next_steps }}.
""",

    "update_status.mcp.yml": """
step: update_status
actor: engineer
intent: "Update defect status"
context:
  defect_id: null
  status: null
input_required:
  - defect_id
  - new_status
allowed_next_steps:
  - add_comment
  - close_defect
llm_prompt_template: |
  You are helping update the status of defect {{ context.defect_id }}.

  Current status: {{ context.status }}

  Please provide the new status.

  Next steps after updating status: {{ allowed_next_steps }}.
""",

    "add_comment.mcp.yml": """
step: add_comment
actor: engineer
intent: "Add comment to defect"
context:
  defect_id: null
  comments: []
input_required:
  - defect_id
  - comment_text
  - commenter_name
allowed_next_steps:
  - update_status
  - close_defect
llm_prompt_template: |
  You are adding a comment to defect {{ context.defect_id }}.

  Existing comments: {{ context.comments }}

  Please provide your comment.

  Next steps: {{ allowed_next_steps }}.
""",

    "close_defect.mcp.yml": """
step: close_defect
actor: engineer
intent: "Close the defect if resolved"
context:
  defect_id: null
  status: "Resolved"
input_required:
  - defect_id
  - close_reason
allowed_next_steps:
  - none
llm_prompt_template: |
  You are closing defect {{ context.defect_id }}.

  Please provide a reason for closing the defect.

  This is the last step.
"""
}

def create_manifests_folder(folder_path="mcp_manifests"):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    for filename, content in mcp_manifests.items():
        with open(os.path.join(folder_path, filename), "w", encoding="utf-8") as f:
            f.write(content.strip())
    print(f"✅ MCP manifests created in '{folder_path}/'")

if __name__ == "__main__":
    create_manifests_folder()
