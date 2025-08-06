import yaml
import redis
from utils.aws_secrets import get_aws_secret

def load_app_config(path="config/config.yml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def get_redis_client():
    config = load_app_config()
    secret_name = config["defaults"]["shared_secret"]
    region = config["defaults"]["region"]
    secret = get_aws_secret(secret_name, region)
    

    return redis.Redis(
        host=secret["REDIS_HOST"],
        port=int(secret.get("REDIS_PORT", 6379)),
        username=secret.get("REDIS_USER", "default"),
        password=secret["REDIS_PASS"],
        decode_responses=False
    )
