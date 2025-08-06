import boto3
import yaml

def load_app_config(path="config/config.yml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def get_bedrock_client():
    config = load_app_config()
    region = config["defaults"]["region"]

    return boto3.client(
        service_name="bedrock-runtime",
        region_name=region
    )

def get_bedrock_models():
    config = load_app_config()
    return {
        "titan_v1": config["defaults"]["bedrock_model_titan_v1"],
        "titan_v2": config["defaults"]["bedrock_model_titan_v2"],
        "claude_v3": config["defaults"]["bedrock_model_claude_v3"],
        "claude_haiku": config["defaults"]["bedrock_model_claude_haiku"],
        "anthropic_version": config["defaults"]["anthropic_version"],
        "top_k": config["defaults"].get("top_k", 5),
        "embedding_dim": config["defaults"].get("embedding_dim", 1536)
    }
