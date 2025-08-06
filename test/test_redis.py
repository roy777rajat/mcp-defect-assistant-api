from config.redis_conn import get_redis_client

def test_redis_connection():
    redis_client = get_redis_client()
    pong = redis_client.ping()
    assert pong is True
    print("✅ Redis connection test passed!")

if __name__ == "__main__":
    test_redis_connection()
    