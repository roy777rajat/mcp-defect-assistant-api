import yaml
from utils.aws_secrets import get_aws_secret
from requests.auth import HTTPBasicAuth

def load_app_config(path="config/config.yml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def connect_jira():

    config = load_app_config()
    secret_name = config["defaults"]["shared_secret"]
    region = config["defaults"]["region"]

    creds = get_aws_secret(secret_name, region)

    base_url = creds["JIRA_BASE_URL"]
    auth = HTTPBasicAuth(creds["JIRA_EMAIL"], creds["JIRA_API_TOKEN"])

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    return {
        "base_url": base_url,
        "headers": headers,
        "auth": auth,
        "project_key": creds["JIRA_PROJECT_KEY"],
        "email": creds["JIRA_EMAIL"],
        "api_token": creds["JIRA_API_TOKEN"]
    }
