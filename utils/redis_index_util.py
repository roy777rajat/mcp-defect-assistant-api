from config.redis_conn import get_redis_client
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

VECTOR_DIM = 1024  # Titan embedding size

INDEX_CONFIGS = {
    "defect_embeddings_index": {
        "index_name": "defect_index",
        "prefix": "defect:",
        "fields": [
            TextField("defect_id"),
            TextField("description"),
            VectorField("embedding", "FLAT", {
                "TYPE": "FLOAT32",
                "DIM": VECTOR_DIM,
                "DISTANCE_METRIC": "COSINE",
                "INITIAL_CAP": 100,
                "BLOCK_SIZE": 100,
            }),
        ],
    },
    "manifest_embeddings_index": {
        "index_name": "manifest_index",
        "prefix": "manifest:",
        "fields": [
            TextField("manifest_id"),
            TextField("description"),
            VectorField("embedding", "FLAT", {
                "TYPE": "FLOAT32",
                "DIM": VECTOR_DIM,
                "DISTANCE_METRIC": "COSINE",
                "INITIAL_CAP": 100,
                "BLOCK_SIZE": 100,
            }),
        ],
    }
}

def create_vector_index(token: str):
    config = INDEX_CONFIGS.get(token)
    if not config:
        raise ValueError(f"❌ Unknown embedding index token: '{token}'")

    redis_conn = get_redis_client()
    index_name = config["index_name"]

    try:
        redis_conn.ft(index_name).info()
        print(f"ℹ️ Redis index '{index_name}' already exists. ")
        return
    except Exception:
        print(f"🆕 Creating Redis index '{index_name}'...")

    redis_conn.ft(index_name).create_index(
        fields=config["fields"],
        definition=IndexDefinition(
            prefix=[config["prefix"]],
            index_type=IndexType.HASH
        )
    )
    print(f"✅ Redis index '{index_name}' created successfully.")


def drop_index(token: str, delete_documents: bool = False):
    config = INDEX_CONFIGS.get(token)
    if not config:
        raise ValueError(f"❌ Unknown embedding index token: '{token}'")

    redis_conn = get_redis_client()
    index_name = config["index_name"]

    try:
        redis_conn.ft(index_name).dropindex(delete_documents=delete_documents)
        if delete_documents:
            print(f"🗑️ Redis index '{index_name}' and all documents dropped.")
        else:
            print(f"🗑️ Redis index '{index_name}' dropped (documents retained).")
    except Exception as e:
        print(f"⚠️ Failed to drop index '{index_name}': {e}")
