import yaml
from neo4j import GraphDatabase
from utils.aws_secrets import get_aws_secret

def load_app_config(path="config/config.yml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def get_neo4j_driver():
    config = load_app_config()
    secret_name = config["defaults"]["shared_secret"]
    region = config["defaults"]["region"]
    creds = get_aws_secret(secret_name, region)

    return GraphDatabase.driver(
        creds["NEO4J_URI"],
        auth=(creds["NEO4J_USER"], creds["NEO4J_PASSWORD"])
    )
