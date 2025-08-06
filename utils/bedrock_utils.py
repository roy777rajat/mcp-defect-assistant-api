import json
import time
import boto3
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_bedrock_client(region: str = "eu-west-1"):
    # Create Bedrock client
    client = boto3.client("bedrock-runtime", region_name=region)

    # Log AWS caller identity for debugging credentials/permissions
    try:
        sts = boto3.client("sts", region_name=region)
        identity = sts.get_caller_identity()
        #logger.info(f"AWS Caller Identity: {identity}")
    except Exception as e:
        logger.warning(f"Could not get AWS caller identity: {e}")

    return client

def generate_defect_embedding(
    bedrock_client,
    text: str,
    model_id: str = "amazon.titan-embed-text-v2:0",
    input_key: str = "inputText",
    retries: int = 3,
    sleep_seconds: float = 1.0
) -> list[float]:
    """
    Generate embedding vector from text using Bedrock embedding model.
    """
    payload = {input_key: text}

    for attempt in range(retries):
        try:
            logger.info(f"Embedding attempt {attempt + 1} for model {model_id}")
            response = bedrock_client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload)
            )
            raw = response['body'].read()
            result = json.loads(raw)
            embedding = result.get("embedding")
            if embedding:
                return embedding
            else:
                raise Exception("Embedding missing in response")
        except Exception as e:
            logger.error(f"Embed attempt {attempt + 1} failed: {e}")
            time.sleep(sleep_seconds)

    raise Exception("Embedding generation failed after retries")

def query_bedrock_chat(
    bedrock_client,
    prompt: str,
    model_id: str = "anthropic.claude-3-haiku-20240307-v1:0",
    max_tokens: int = 1000,
    max_retries: int = 5,
    anthropic_version: str = "bedrock-2023-05-31",
    sleep_seconds: float = 1.0
):
    """
    Query Bedrock chat model (Claude or similar).
    """
    logger.info(f"Querying Bedrock chat with model_id={model_id}, max_tokens={max_tokens}")
    body = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "anthropic_version": anthropic_version
    }

    for attempt in range(max_retries):
        try:
            response = bedrock_client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )
            return response
        except bedrock_client.exceptions.ThrottlingException:
            wait = 2 ** attempt
            logger.warning(f"Throttled, retrying in {wait}s (attempt {attempt + 1})")
            time.sleep(wait)
        except Exception as e:
            logger.error(f"Bedrock call failed: {e}", exc_info=True)
            raise

    raise Exception("Max Bedrock retries exceeded")

def call_llm(
    prompt: str,
    model_id: str = "anthropic.claude-3-haiku-20240307-v1:0",
    max_tokens: int = 1000,
    version: str = "bedrock-2023-05-31",
    region: str = "eu-west-1"
) -> str:
    """
    Wrapper to call Bedrock chat model and return response text.
    """
    logger.info(f"Calling LLM with model_id={model_id} in region={region}")
    client = get_bedrock_client(region)
    response = query_bedrock_chat(
        bedrock_client=client,
        prompt=prompt,
        model_id=model_id,
        max_tokens=max_tokens,
        anthropic_version=version
    )

    raw = response['body'].read()
    result = json.loads(raw)

    # Claude-style format
    if isinstance(result, dict) and "content" in result:
        content = result["content"]
        if isinstance(content, list):
            return content[0].get("text", "").strip()
        elif isinstance(content, str):
            return content.strip()

    raise Exception(f"Unexpected LLM response format: {result}")
