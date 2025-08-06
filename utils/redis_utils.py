import numpy as np
import json
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType


def create_vector_index(
    redis_conn,
    index_name: str,
    vector_dim: int,
    prefix: str,
    text_fields: list[str],
    embedding_field_name: str = "embedding",
    distance_metric: str = "COSINE",
    vector_algo: str = "FLAT",
    vector_type: str = "FLOAT32"
):
    try:
        redis_conn.ft(index_name).info()
        print(f"ℹ️ Redis index '{index_name}' already exists.")
        return
    except Exception:
        print(f"🆕 Creating Redis index '{index_name}'...")

    try:
        fields = [TextField(field) for field in text_fields]
        fields.append(
            VectorField(
                embedding_field_name,
                vector_algo,
                {
                    "TYPE": vector_type,
                    "DIM": vector_dim,
                    "DISTANCE_METRIC": distance_metric,
                    "INITIAL_CAP": 100,
                    "BLOCK_SIZE": 100
                }
            )
        )

        redis_conn.ft(index_name).create_index(
            fields=fields,
            definition=IndexDefinition(prefix=[prefix], index_type=IndexType.HASH)
        )
        print(f"✅ Redis index '{index_name}' created.")
    except Exception as e:
        print(f"⚠️ Redis index creation issue for '{index_name}': {e}")


def upsert_embedding(
    redis_conn,
    key_id: str,
    embedding: list[float],
    metadata: dict,
    key_prefix: str,
    embedding_field_name: str = "embedding"
):
    key = f"{key_prefix}{key_id}"
    vector_bytes = np.array(embedding, dtype=np.float32).tobytes()

    hset_args = [embedding_field_name, vector_bytes]
    for field_name, value in metadata.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        else:
            value = str(value)
        hset_args.extend([field_name, value])

    try:
        redis_conn.execute_command("HSET", key, *hset_args)
        print(f"✅ Upserted embedding for {key} into Redis")
    except Exception as e:
        print(f"❌ Failed to upsert embedding for {key}: {e}")


def clear_cache_from_redis(redis_conn, key_prefix: str):
    """
    Delete all keys in Redis matching the given prefix (e.g., 'manifest:', 'defect:')
    """
    count = 0
    for key in redis_conn.scan_iter(f"{key_prefix}*"):
        redis_conn.delete(key)
        count += 1
    print(f"🗑️ Cleared {count} keys with prefix '{key_prefix}' from Redis.")


def load_cache_from_redis(redis_conn, key_prefix: str = "manifest:") -> dict:
    """
    Load Redis hashes (excluding binary fields) into a cache dictionary.
    """
    cache = {}
    for key in redis_conn.scan_iter(f"{key_prefix}*"):
        raw_data = redis_conn.hgetall(key)
        decoded_data = {}

        for k, v in raw_data.items():
            k_decoded = k.decode("utf-8", errors="ignore")

            # Skip binary embedding
            if k_decoded == "embedding":
                continue

            try:
                decoded_data[k_decoded] = json.loads(v)
            except Exception:
                try:
                    decoded_data[k_decoded] = v.decode("utf-8", errors="ignore")
                except Exception:
                    decoded_data[k_decoded] = str(v)

        key_id = key.decode("utf-8", errors="ignore").replace(key_prefix, "")
        cache[key_id] = decoded_data

    return cache



