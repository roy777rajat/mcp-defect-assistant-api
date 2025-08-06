import json
import requests
from config.jira_conn import connect_jira

def raise_defect_api(context):

    print(f"[RAISE] Creating defect with: {context}")
    #print (f"The Title is :{context.get('title', 'Default Title')}  and the Description is :{context.get('description', 'Default Description')}")
    defect_id = create_jira_issue(summary=context.get('title', 'Default Summary') , description=context.get('description', 'Default Description'))
    if not defect_id:
        return {"status": "error", "message": "Failed to create defect in JIRA"}
    else:
        defect_id = f"Defect-{defect_id} create with Title as '{context.get('title')}' and Description as {context.get('description')}"  # Assuming JIRA returns an issue key like "PROJ-123"
    return {"status": "success", "defect_id": defect_id}

def assign_defect_api(context):
    print(f"[ASSIGN] Assigning defect with: {context}")
    return {"status": "success", "engineer_name": context['engineer_name']}

def add_comment_api(context):
    print(f"[ADD COMMENT] Commenting defect : {context}")
    return {"status": "success", "comment_text": context['comment_text']}

def review_defect_api(context):
    print(f"[REVIEW COMMENT] Commenting defect : {context}")
    return {"status": "success", "review_comments": context['review_comments']}

def close_defect_api(context):
    print(f"[CLOSE DEFECT] Commenting defect : {context}")
    return {"status": "success", "comment_text": context['comment_text']}

def update_status_api(context):
    print(f"[UPDATE STATUS] Commenting defect : {context}")
    return {"status": "success", "new_status": context['new_status']}






def create_jira_issue(summary: str, description: str):
    jira = connect_jira()

    url = f"{jira['base_url']}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": jira["project_key"]},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}]
                    }
                ]
            },
            "issuetype": {"name": "Bug"}
        }
    }

    response = requests.post(
        url,
        headers=jira["headers"],
        auth=jira["auth"],
        data=json.dumps(payload)
    )

    if response.status_code == 201:
        issue_key = response.json()["key"]
        print("✅ Jira issue created:", issue_key)
        return issue_key
    else:
        print("❌ Failed to create issue:", response.status_code)
        print(response.text)
        return None