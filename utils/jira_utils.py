import requests
from requests.auth import HTTPBasicAuth
import json
from config.jira_conn import connect_jira



# --- Function to Create Jira Bug ---
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
        print("✅ Jira issue created:", response.json()["key"])
        return response.json()["key"]
    else:
        print("❌ Failed to create issue:", response.status_code)
        print(response.text)
        return None



# --- CLI Test Entry Point ---
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create a Jira defect/bug.")
    parser.add_argument("--summary", required=True, help="Issue summary/title")
    parser.add_argument("--description", required=True, help="Issue description/body")

    args = parser.parse_args()

    create_jira_issue(args.summary, args.description)
    #list_projects()


    
