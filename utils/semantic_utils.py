import numpy as np
import json
import base64

from config.bedrock_client import get_bedrock_client, get_bedrock_models
from config.redis_conn import get_redis_client
from config.neo4j_conn import get_neo4j_driver
from utils.neo4j_utils import fetch_defect_by_id
from utils.neo4j_utils import fetch_defect_by_id


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

def find_similar_defects(
    query_embedding: list[float],
    defect_embeddings: list[dict],
    threshold: float = 0.8
) -> list[dict]:
    similar = []
    for defect in defect_embeddings:
        score = cosine_similarity(query_embedding, defect['embedding'])
        if score >= threshold:
            similar.append({"defect_id": defect["defect_id"], "score": score})
    return sorted(similar, key=lambda x: x["score"], reverse=True)

def polish_answer(text: str) -> str:
    return text.strip()

def vectorize_text(text: str) -> list[float]:
    """
    Uses Bedrock to get embedding for the given text
    """
    bedrock = get_bedrock_client()
    models = get_bedrock_models()
    model_id = models["titan_v2"]

    payload = { "inputText": polish_answer(text) }

    response = bedrock.invoke_model(
        body=json.dumps(payload),
        modelId=model_id,
        accept="application/json",
        contentType="application/json"
    )

    result = json.loads(response['body'].read())
    embedding = result.get("embedding")
    if not embedding:
        raise Exception("No embedding found in response")

    # embedding may be a list (already decoded) or base64 string, handle both
    if isinstance(embedding, list):
        return embedding
    else:
        vector_bytes = base64.b64decode(embedding)
        return np.frombuffer(vector_bytes, dtype=np.float32).tolist()


def search_similar_defects(query_text: str, top_k: int = 3, threshold: float = 0.75) -> list[dict]:
    """
    Search Redis for top-k similar defects using vectorized input
    """
    redis_conn = get_redis_client()
    query_vector = vectorize_text(query_text)

    # Pull all embeddings from Redis (for small-scale use)
    keys = redis_conn.keys("defect:*")
    all_embeddings = []
    for key in keys:
        data = redis_conn.json().get(key)
        all_embeddings.append({
            "defect_id": data["defect_id"],
            "embedding": data["embedding"]
        })

    # Use cosine similarity for filtering
    similar = find_similar_defects(query_vector, all_embeddings, threshold=threshold)

    # Add Neo4j metadata
    neo4j = get_neo4j_driver()
    enriched = []
    with neo4j.session() as session:
        for match in similar[:top_k]:
            record = fetch_defect_by_id(session, match["defect_id"])
            if record:
                record["score"] = match["score"]
                enriched.append(record)

    return enriched
