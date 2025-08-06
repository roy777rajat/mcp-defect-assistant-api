from config.bedrock_client import get_bedrock_client


def test_bedrock_client():
    bedrock = get_bedrock_client()
    try:
        response = bedrock.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            contentType="application/json",
            accept="application/json",
            body='{"inputText": "Test embedding generation"}'
        )
        print("✅ Bedrock client invocation test passed!")
    except Exception as e:
        print(f"❌ Bedrock client test failed: {e}")

if __name__ == "__main__":
    test_bedrock_client()
