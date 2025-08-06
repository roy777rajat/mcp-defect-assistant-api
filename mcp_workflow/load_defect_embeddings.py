import json
import base64
import numpy as np
import os
import yaml
import datetime
import re

from config.bedrock_client import get_bedrock_client, get_bedrock_models
from config.redis_conn import get_redis_client
from config.neo4j_conn import get_neo4j_driver

from utils.redis_utils import upsert_embedding, clear_cache_from_redis, load_cache_from_redis
from utils.semantic_utils import polish_answer
from utils.neo4j_utils import fetch_all_defects
from utils.redis_index_util import create_vector_index, drop_index
from utils.redis_index_util import INDEX_CONFIGS
from redis.commands.search.field import TextField
from redis.commands.search.query import Query

manifest_cache = {}

def get_embeddings(text: str) -> list[float]:
    bedrock = get_bedrock_client()
    models = get_bedrock_models()
    model_id = models["titan_v2"]

    payload = {"inputText": polish_answer(text)}

    response = bedrock.invoke_model(
        body=json.dumps(payload),
        modelId=model_id,
        accept="application/json",
        contentType="application/json"
    )

    result = json.loads(response['body'].read())
    embedding = result.get("embedding")
    if not embedding or not isinstance(embedding, list):
        raise Exception("Invalid embedding format received")

    return embedding

def load_embeddings_to_redis_defect(token: str):
    redis_conn = get_redis_client()
    create_vector_index(token)

    neo4j_driver = get_neo4j_driver()
    with neo4j_driver.session() as session:
        defects = fetch_all_defects(session)
        print(f"✅ Fetched {len(defects)} defects from Neo4j")

        for defect in defects:
            defect_id = defect["defect_id"]
            text_for_embedding = f"{defect['title']} - {defect['description']}"
            embedding = get_embeddings(text_for_embedding)
            print(f"Embedding for defect {defect_id} generated successfully")
            print(f"Embeddding text: {text_for_embedding}   \nEmbedding: {embedding}")

        print(f"✅ Stored embeddings for {len(defects)} defects into Redis")

def manifest_to_text(manifest: dict) -> str:
    step = manifest.get('step', '')
    actor = manifest.get('actor', '')
    intent = manifest.get('intent', '')
    input_required = ', '.join(manifest.get('input_required', []))
    allowed_next_steps = ', '.join(manifest.get('allowed_next_steps', []))
    prompt_template = manifest.get('llm_prompt_template', '')

    text = f"""Step: {step}
Actor: {actor}
Intent: {intent}
Input Required: {input_required}
Allowed Next Steps: {allowed_next_steps}
Prompt Template: {prompt_template}
"""
    return text

def safe_str(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: safe_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [safe_str(item) for item in obj]
    return str(obj)

# def parse_llm_output(text: str) -> dict:
#     result = {"State": None, "Required Fields": {}, "Allowed Next Steps": None, "Confirmation": None}

#     state_match = re.search(r"State:\s*(.+)", text)
#     if state_match:
#         result["State"] = state_match.group(1).strip()

#     fields_section = re.search(r"Required Fields:\s*((?:- .+\n?)*)", text)
#     if fields_section:
#         for line in fields_section.group(1).strip().splitlines():
#             match = re.match(r"- (\w+):\s*(.+)", line)
#             if match:
#                 field, value = match.groups()
#                 result["Required Fields"][field.strip()] = value.strip()

#     next_steps_match = re.search(r"Allowed Next Steps:\s*(.+)", text)
#     if next_steps_match:
#         result["Allowed Next Steps"] = next_steps_match.group(1).strip()

#     confirm_match = re.search(r"Confirmation:\s*(.+)", text)
#     if confirm_match:
#         result["Confirmation"] = confirm_match.group(1).strip()

#     return result

import re

def parse_llm_output_multiple_states(text: str) -> dict:
    steps = []
    current_step = None
    in_required_fields = False

    lines = text.splitlines()
    for line in lines:
        line = line.strip()

        # Detect start of a new step block (e.g. '1.' or '2.')
        if re.match(r'^\d+\.$', line):
            if current_step:
                steps.append(current_step)
            current_step = {
                "Step Name": None,
                "Required Fields": {},
                "Allowed Next Steps": None,
            }
            in_required_fields = False
            continue

        if current_step is not None:
            # Step Name line
            m = re.match(r'^Step Name:\s*(.+)$', line)
            if m:
                current_step["Step Name"] = m.group(1).strip()
                continue

            # Start of Required Fields
            if line.startswith("Required Fields:"):
                in_required_fields = True
                continue

            # Allowed Next Steps line
            m = re.match(r'^Allowed Next Steps:\s*(.+)$', line)
            if m:
                current_step["Allowed Next Steps"] = m.group(1).strip()
                in_required_fields = False
                continue

            # Lines under Required Fields
            if in_required_fields and line.startswith("-"):
                field_match = re.match(r'-\s*(\w+):\s*(.+)', line)
                if field_match:
                    field, value = field_match.groups()
                    current_step["Required Fields"][field.strip()] = value.strip()
                continue

    # Append last step
    if current_step:
        steps.append(current_step)

    # Extract Confirmation line (only once)
    confirmation = None
    m = re.search(r'^Confirmation:\s*(.+)$', text, re.MULTILINE)
    if m:
        confirmation = m.group(1).strip()

    return {
        "States": steps,
        "Confirmation": confirmation,
    }


def call_claude_for_step_selection(user_comment: str, candidates: list[dict]) -> dict:
    bedrock = get_bedrock_client()
    models = get_bedrock_models()
    model_id = models["claude_haiku"]
    version = models["anthropic_version"]

    candidate_text = "\n".join(
        [
            f"{i+1}. Step: {safe_str(c['manifest_id'])}\nDescription: {safe_str(c['description'])}"
            for i, c in enumerate(candidates)
        ]
    )

    # combined_prompt = (
    # "You are an intelligent assistant for managing defect workflows.\n\n"
    # "Your task is to analyze a user comment and identify all relevant workflow steps described sequentially.\n"
    # "Each step in the workflow manifest includes a step name, required fields, and allowed next steps.\n\n"
    # "Instructions:\n"
    # "1. Identify **all** relevant steps in the order they appear in the user comment.\n"
    # "2. For each step, extract the required fields from the comment. If a required field is missing, return 'Not Provided'.\n"
    # "3. For each step, return its allowed next steps as listed in the manifest.\n"
    # "4. Format your output exactly as shown in the example below.\n\n"
    # "Output Format:\n"
    # "States:\n"
    # "1.\n"
    # "  Step Name: <step_name_1>\n"
    # "  Required Fields:\n"
    # "  - field1: <value or 'Not Provided'>\n"
    # "  - field2: <value or 'Not Provided'>\n"
    # "  Allowed Next Steps: <comma-separated list>\n"
    # "2.\n"
    # "  Step Name: <step_name_2>\n"
    # "  Required Fields:\n"
    # "  - fieldA: <value or 'Not Provided'>\n"
    # "  Allowed Next Steps: <comma-separated list>\n"
    # "...\n"
    # "Confirmation: Do you want to proceed with these actions?\n\n"
    # "If no suitable step matches, respond with:\n"
    # "States: None\n"
    # "Required Fields: N/A\n"
    # "Allowed Next Steps: N/A\n"
    # "Confirmation: Unable to proceed due to insufficient information.\n\n"
    # "Example:\n"
    # "User Comment:\n"
    # "\"Create defect with Title: Login Issue, Description: Cannot login, Raised by: Alice, then assign to SupportTeam\"\n\n"
    # "Output:\n"
    # "States:\n"
    # "1.\n"
    # "  Step Name: create_defect\n"
    # "  Required Fields:\n"
    # "  - title: Login Issue\n"
    # "  - description: Cannot login\n"
    # "  - created_by: Alice\n"
    # "  Allowed Next Steps: review_defect\n"
    # "2.\n"
    # "  Step Name: assign_defect\n"
    # "  Required Fields:\n"
    # "  - assigned_to: SupportTeam\n"
    # "  Allowed Next Steps: close_defect\n"
    # "Confirmation: Do you want to proceed with these actions?\n\n"
    # f"User Comment:\n{user_comment}\n\n"
    # f"Workflow Steps Manifest:\n{candidate_text}"
    # )
    combined_prompt = (
    "You are an intelligent assistant for managing defect workflows.\n\n"
    "Your task is to analyze a user comment and identify all relevant workflow steps described sequentially.\n"
    "Each step in the workflow manifest includes a step name, required fields, and allowed next steps.\n\n"
    "Instructions:\n"
    "1. Identify **all** relevant steps in the order they appear in the user comment.\n"
    "2. For each step, extract the required fields from the comment. "
    "**If a required field is missing or cannot be extracted, return 'Not Provided' explicitly for that field.**\n"
    "3. For each step, return its allowed next steps as listed in the manifest.\n"
    "4. You MUST use the exact Step Name name from this set {create_defect,review_defect,assign_defect,update_status,add_comment,close_defect,search_similar_defect} .\n"
    "5. You MUST add serach similar (semantic) defect or similar text or description of the text, then you should also give one flag as Yes, else No  .\n"
    "6. Format your output exactly as shown in the example below.\n\n"
    "Output Format:\n"
    "States:\n"
    "1.\n"
    "  Step Name: <step_name_1>\n"
    "  Required Fields:\n"
    "  - field1: <value or 'Not Provided'>\n"
    "  - field2: <value or 'Not Provided'>\n"
    "  allowed_next_steps: <comma-separated list>\n"
    "2.\n"
    "  Step Name: <step_name_2>\n"
    "  Required Fields:\n"
    "  - fieldA: <value or 'Not Provided'>\n"
    "  allowed_next_steps: <comma-separated list>\n"
    "...\n"
    "SimilarDefect: Yes\n\n"
    "If no suitable step matches, respond with:\n"
    "States: None\n"
    "Required Fields: N/A\n"
    "allowed_next_steps: N/A\n"
    "Confirmation: Unable to proceed due to insufficient information.\n\n"
    "SimilarSearchFlag: No\n\n"
    "Example:\n"
    "User Comment:\n"
    "\"Create defect with Title: Login Issue, Description: Cannot login, Raised by: Alice, then assign defect_id: 12345 to SupportTeam\"\n\n"
    "Output:\n"
    "States:\n"
    "1.\n"
    "  Step Name: create_defect\n"
    "  Required Fields:\n"
    "  - title: Login Issue\n"
    "  - description: Cannot login\n"
    "  - created_by: Alice\n"
    "  allowed_next_steps: review_defect\n"
    "2.\n"
    "  Step Name: assign_defect\n"
    "  Required Fields:\n"
    "  - defect_id: 12345\n"
    "  - engineer_name: SupportTeam\n"
    "  allowed_next_steps: close_defect\n"
    "3.\n"
    "  Step Name: add_comment\n"
    "  Required Fields:\n"
    "  - defect_id: 12345\n"
    "  - comment_text: Adding comments in the defect 12345...\n"
    "  - commenter_name: rroy007\n"
    "  allowed_next_steps: update_status,close_defect\n"
    f"User Comment:\n{user_comment}\n\n"
    f"Workflow Steps Manifest:\n{candidate_text}"
    )



    response = bedrock.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "anthropic_version": version,
            "messages": [{"role": "user", "content": combined_prompt}],
            "max_tokens": 1000
        })
    )

    result = json.loads(response["body"].read())
    print(f"LLM response:\n {result}")

    return parse_llm_output_multiple_states(result["content"][0]["text"].strip())


def dynamic_mode_switch(user_comment: str, redis_conn, token="manifest_embeddings_index", top_k=3, threshold=0.5):
    config = INDEX_CONFIGS[token]
    index_name = config["index_name"]

    user_comment_emb = f"USER COMMENT: {user_comment}\nCONTEXT: Decide if this is a create_defect, assign_defect, close_defect, review_defect, update_status, or add_comment."
    query_embedding = get_embeddings(user_comment_emb)
    vector_bytes = np.array(query_embedding, dtype=np.float32).tobytes()

    query_str = f"*=>[KNN {top_k} @embedding $vec_param AS score]"
    query = Query(query_str).sort_by("score").return_fields("manifest_id", "description", "score").paging(0, top_k).dialect(2)
    params_dict = {"vec_param": vector_bytes}

    try:
        results = redis_conn.ft(index_name).search(query, query_params=params_dict)
        if results.total == 0:
            print("No matching manifest found.")
            return None, None, None

        candidates = []
        for doc in results.docs:
            manifest_id = doc.manifest_id
            description = str(doc.description)
            candidates.append({"manifest_id": manifest_id, "description": description})

        parsed_output = call_claude_for_step_selection(user_comment, candidates)
        
        #print(f"[PARSED OUTPUT] {parsed_output}")
        return parsed_output

        # if parsed_output["State"].lower() == "none":
        #     print("Claude LLM: No confident match.")
        #     return None, None, None

        # selected = next((c for c in candidates if parsed_output["State"] in c["manifest_id"]), None)

        # if selected:
        #     return parsed_output["State"], parsed_output, selected
        # else:
        #     return None, None, None

    except Exception as e:
        print(f"Search error: {e}")
        return None, None, None

def test_llm_manifest_mapping(user_comment: str):
    redis_conn = get_redis_client()
    parsed_output = dynamic_mode_switch(user_comment, redis_conn)
    #print (f"User comment: {user_comment}   \nParsed output: {parsed_output}")
    json_output = json.dumps(parsed_output, indent=2)
    return json_output
    

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load manifest embeddings and test LLM mapping with a user comment.")
    parser.add_argument(
        "--comment",
        type=str,
        required=True,
        help="User comment text to test LLM mapping against manifest steps."
    )
    args = parser.parse_args()

    #rint("\n--- Running LLM Mapping Test ---")
    json_output = test_llm_manifest_mapping(args.comment)
    print("\n--- LLM Sophistacated Output ---")
    print(json_output)



    # from mcp_llm_handler import process_llm_states
    # if isinstance(json_output, str):
    #     json_output = json.loads(json_output) 
    # responses=process_llm_states(json_output, "YES")
    # print("=== Test Output ===")
    # print(str(responses))
