from mcp_engine import MCPWorkflow  # your MCP engine
from interface.api_handlers import raise_defect_api, assign_defect_api,add_comment_api,review_defect_api,close_defect_api,update_status_api  # Simulated or real APIs

# Register step functions
STEP_FUNCTIONS = {
    "create_defect": raise_defect_api,
    "assign_defect": assign_defect_api,
    "add_comment" : add_comment_api,
    "review_defect" : review_defect_api,
    "close_defect" : close_defect_api,
    "update_status": update_status_api # Assuming you have this function defined
}

def process_llm_states(llm_output, user_confirmation):
    mcp = MCPWorkflow()
    messages_to_user = []

    # ✅ Keep context outside the loop to persist across steps
    global_context = {}

    States = llm_output.get("States", [])
    if not States or len(States) == 0:
        messages_to_user.append(f"⚠️Sorry!! Unable to understand the ask, kindly ask about defects in general, No define action I have.")
       
    
    for step_data in llm_output.get("States", []):
        step_name = step_data.get("Step Name")
        fields = step_data.get("Required Fields", {})
        
        # ✅ Merge new fields into global context
        # Safe update: skip keys with 'Not Provided' or empty values
        for key, value in fields.items():
            if value and value != "Not Provided":
                global_context[key] = value

        # ✅ Start engine with full global context so far
        mcp.start(step_name=step_name, initial_context=global_context)

        # Validate required inputs
        missing_fields = []
        for req_field in mcp.get_input_requirements():
            if req_field not in global_context or not global_context[req_field] or global_context[req_field] == "Not Provided":
                missing_fields.append(req_field)

        if missing_fields:
            messages_to_user.append(f"Step `{step_name}` is missing fields: {missing_fields}")
            continue

        # Execute the step
        if user_confirmation.strip().upper() == "YES":
            action_fn = STEP_FUNCTIONS.get(step_name)
            if action_fn:
                print(f"▶️ Executing API for step: {step_name}")
                result = action_fn(global_context)

                # ✅ Merge returned API values into global context
                if isinstance(result, dict):
                    global_context.update(result)

                messages_to_user.append(f"✅ Executed `{step_name}`: {result}")
            else:
                messages_to_user.append(f"⚠️ No action function found for `{step_name}`")

        # Update context for next step
        mcp.update_context(global_context)

        # Transition to next step
        next_steps_str = step_data.get("Allowed Next Steps")
        if next_steps_str:
            # Split comma-separated string to list
            next_steps = [step.strip() for step in next_steps_str.split(",")]
            # Pick the first allowed next step (or add your own logic)
            chosen_next_step = next_steps[0]
            mcp.proceed_to_next(chosen_next_step)


    return convert_missing_field_messages(messages_to_user)

import re
def convert_missing_field_messages(messages):
    """
    Converts messages like:
    "Step `update_status` is missing fields: ['defect_id', 'new_status']"
    into:
    "Sorry!! kindly provide the following: for 'update_status' requires 'defect_id, new_status'"
    
    Leaves all other messages as-is.
    """
    parts = []
    passthrough_msgs = []

    for msg in messages:
        match = re.match(r"Step `(.+?)` is missing fields: \[(.*?)\]", msg)
        if match:
            step_name = match.group(1)
            fields_raw = match.group(2)
            fields = [f.strip().strip("'\"") for f in fields_raw.split(",")]
            field_str = ', '.join(fields)
            parts.append(f"for Action: '{step_name}' requires '{field_str}' , which is missing.Unable to proceed.")
        else:
            passthrough_msgs.append(msg)

    response = ""
    if parts:
        response += "⚠️ Provide the following: " + "; ".join(parts) + ".\n"

    if passthrough_msgs:
        response += "\n".join(passthrough_msgs)

    return response or "✅ All required fields are present."



# ✅ Mock LLM output
mock_llm_output_multiple_state = {
    'States': [
        {
            'Step Name': 'create_defect',
            'Required Fields': {
                'title': 'Fund Page have incorrect proce',
                'description': 'Fund Prices is not properly invoked, need to check as soon as possible',
                'created_by': 'rroy'
            },
            'Allowed Next Steps': 'assign_defect'
        },
        {
            'Step Name': 'assign_defect',
            'Required Fields': {
                'defect_id': 'Not Provided',
                'engineer_name': 'ITTeam'
            },
            'Allowed Next Steps': 'update_status, add_comment'
        }
    ],
    'Confirmation': 'YES'
}


mock_llm_output = {
    'States': [
        {
         "Step Name":"add_comment",
         "Required Fields":{
            "defect_id":"1234",
            "comment_text":"Attaching new comments",
            "commenter_name":"rahul"
         },
         "Allowed Next Steps":"update_status, close_defect"
        }
    ],
    'Confirmation': 'YES'
}

if __name__ == "__main__":
    responses = process_llm_states(mock_llm_output_multiple_state, user_confirmation="YES")
    print("=== Test Output ===")
    print(str(responses))
    # for message in responses:
    #     print(message)
