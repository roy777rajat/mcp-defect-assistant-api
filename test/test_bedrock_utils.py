from config.bedrock_client import get_bedrock_client
from utils.bedrock_utils import generate_defect_embedding
from utils.bedrock_utils import query_bedrock_chat

def test_embedding():
    client = get_bedrock_client()
    text = "Test defect: UI not loading"
    embedding = generate_defect_embedding(client, text, model_id="amazon.titan-embed-text-v2:0")
    print("✅ Embedding vector length:", len(embedding))

def test_chat():
    client = get_bedrock_client()  # region where chat model is hosted
    prompt = "Hello, say hi!"
    try:
        response = query_bedrock_chat(client, prompt, model_id="anthropic.claude-3-haiku-20240307-v1:0")
        raw = response['body'].read()
        print("✅ Chat response:", raw)
    except Exception as e:
        print("❌ Chat test failed:", e)

if __name__ == "__main__":
    test_embedding()
    test_chat()
